
def toLeftLoss(px, py, qx, qy, sx, sy):
    return torch.max(torch.tensor(0.0), px * qy - py * qx + qx * sy - qy * sx + sx * py - sy * px)

def loss_1(x):
    loss = torch.tensor(0.0)
    for i in range(len(x)):
        for j in range(len(x)):
            if i == j:
                continue
            for l in range(4):
                loss += pointInRectangleLoss_1(x[j], x[i][l])
    return loss

def rotate_bb_local(point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.
    The angle should be given in radians.
    Assuming origin is zero.
    modified from: https://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python
    """
    result = point.clone()
    result[0] = torch.cos(angle) * point[0] - torch.sin(angle) * point[1]
    result[1] = torch.sin(angle) * point[0] + torch.cos(angle) * point[1]
    return result

def fa_layout_nxt(rj):
    pend_obj_list = []
    final_obj_list = []
    ol = rj['objList']
    total_obj_num = 0
    for o in ol:
        if o is None:
            continue
        if o['modelId'] not in obj_semantic:
            final_obj_list.append(o)
        else:
            total_obj_num += 1
            isRoot = True
            for existobj in pend_obj_list:
                if csrmatrix[name_to_ls[existobj['modelId']], name_to_ls[o['modelId']]] == 1.0:
                    sample_translateRela(o, existobj)
                    existobj['children'].append(o)
                    isRoot = False
                    break
            if isRoot:
                o['children'] = []
                pend_obj_list.append(o)
    room_meta = p2d('.', '/suncg/room/{}/{}f.obj'.
    format(rj['origin'], rj['modelId']))
    room_polygon = Polygon(room_meta[:, 0:2])
    room_shape = torch.from_numpy(room_meta[:, 0:2]).float()
    translate = torch.zeros((len(pend_obj_list), 2)).float()
    orient = torch.zeros((len(pend_obj_list))).float()
    # for o in pend_obj_list:
    #     disturbance(o, 0.5, room_polygon)
    for i in range(len(pend_obj_list)):
        translate[i][0] = pend_obj_list[i]['translate'][0]
        translate[i][1] = pend_obj_list[i]['translate'][2]
        orient[i] = pend_obj_list[i]['orient']
    translate.requires_grad_()
    orient.requires_grad_()
    bbindex = []
    for o in pend_obj_list:
        bbindex.append(name_to_ls[o['modelId']])
        print(o['modelId'])
        for child in o['children']:
            print(" --- ", child['modelId'])
            bbindex.append(name_to_ls[child['modelId']])
    bb = four_points_xz[bbindex].float()
    csrrelation = csrmatrix[bbindex][:, bbindex]
    yrelation = ymatrix[bbindex][:, bbindex]
    print(yrelation)
    bi = 0
    for o in pend_obj_list:
        bb[bi] = rotate_bb_local_para(bb[bi], torch.tensor(o['orient'], dtype=torch.float))
        bi += 1
        for child in o['children']:
            bb[bi] = rotate_bb_local_para(bb[bi], torch.tensor(child['orient'], dtype=torch.float))
            bi += 1
    translate_full = children_translate(pend_obj_list, translate, total_obj_num)

    # time for collision detection
    iteration = 0
    loss = collision_loss(translate_full.reshape(total_obj_num, 1, 2) + bb, room_shape, yrelation)
    while loss.item() > 0.0 and iteration < MAX_ITERATION:
        loss.backward()
        translate.data = translate.data - translate.grad * 0.05
        translate.grad = None
        translate_full = children_translate(pend_obj_list, translate, total_obj_num)
        loss = collision_loss(translate_full.reshape(total_obj_num, 1, 2) + bb, room_shape, yrelation)
        iteration += 1

    for i in range(len(pend_obj_list)):
        o = pend_obj_list[i]
        o['translate'][0] = translate[i][0].item()
        o['translate'][2] = translate[i][1].item()
        for child in o['children']:
            child['translate'][0] = translate[i][0].item() + child['translateRela'][0]
            child['translate'][2] = translate[i][1].item() + child['translateRela'][2]
    return rj

def fa_layout(rj):
    pend_obj_list = []
    final_obj_list = []
    ol = rj['objList']
    for o in ol:
        if o is None:
            continue
        if o['modelId'] not in obj_semantic:
            final_obj_list.append(o)
        else:
            pend_obj_list.append(o)
    room_meta = p2d('.', '/suncg/room/{}/{}f.obj'.
    format(rj['origin'], rj['modelId']))
    room_polygon = Polygon(room_meta[:, 0:2])
    room_shape = torch.from_numpy(room_meta[:, 0:2]).float()
    translate = torch.zeros((len(pend_obj_list), 2)).float()
    orient = torch.zeros((len(pend_obj_list))).float()
    for i in range(len(pend_obj_list)):
        translate[i][0] = pend_obj_list[i]['translate'][0]
        translate[i][1] = pend_obj_list[i]['translate'][2]
        orient[i] = pend_obj_list[i]['orient']
    bbindex = []
    for o in pend_obj_list:
        bbindex.append(name_to_ls[o['modelId']])
    bb = four_points_xz[bbindex].float()
    # Rotate bb with respect to Y-orient of objects, may requires parallel later
    # for i in range(len(pend_obj_list)):
    #     for k in range(4):
    #         bb[i, k] = rotate_bb_local(bb[i, k], orient[i])
    for i in range(len(pend_obj_list)):
        bb[i] = rotate_bb_local_para(bb[i], orient[i])
    translate.requires_grad_()
    orient.requires_grad_()
    loss = loss_2(translate.reshape(len(pend_obj_list), 1, 2) + bb)
    loss += loss_4(translate.reshape(len(pend_obj_list), 1, 2) + bb, room_shape)
    # print(translate.reshape(len(pend_obj_list), 1, 2) + bb)
    # torch.save(translate.reshape(len(pend_obj_list), 1, 2) + bb, './tryp.pt')
    iteration = 0
    while loss.item() > 0.0 and iteration < MAX_ITERATION:
        loss.backward()
        translate.data = translate.data - translate.grad * 0.05
        translate.grad = None
        loss = loss_2(translate.reshape(len(pend_obj_list), 1, 2) + bb)
        loss += loss_4(translate.reshape(len(pend_obj_list), 1, 2) + bb, room_shape)
        iteration += 1
        # print(loss)
    # currently, we dont consider rotation

    # calculate loss for cross object collision

    # then calculate loss for object vs room collision
    for i in range(len(pend_obj_list)):
        o = pend_obj_list[i]
        o['translate'][0] = translate[i][0].item()
        o['translate'][2] = translate[i][1].item()
        # disturbance(o, 0.5, room_shape)
        final_obj_list.append(o)
    return rj

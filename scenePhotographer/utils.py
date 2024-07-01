import numpy as np
import math


DELTA_A = 10
TOKENS=[
    '0442FF36-CEA8-4a98-B18F-9AC9C4A92576',
    'FEEAC78A-42F2-4274-9942-CE0EE0134FAB',
    'FD3130D4-B372-4f14-B03B-8C63FA92DAAF',
    'FA2B1422-EC40-48ec-A97F-14B7464FA262',
    'F50E2B80-811E-4013-ABF6-F469690BEA4F',
    'F50CD7A7-1ADE-4c60-AF73-F6833B5AB02C',
    'EEC0BB51-B97E-44e0-BF6E-91195268C425',
    'E933EF28-DE04-4bb4-905D-AC34DD0B9EE8',
    'E8E6806E-A14A-43cc-ACF3-4D48C7A35420',
    'E5F4AEFB-B724-498d-8D18-17AD37444192',
    'E310B555-6B43-403f-AABF-D6992E4D534A',
    'E24713AC-6195-4cb0-A9E8-5AED9CCD39C1',
    'E0CA75CC-542E-4601-B76A-BF097CAB91DC',
    'DB06893D-642B-4eb9-8D24-8A66755F66D7',
    'D7B1D3C2-B5DC-4284-AF98-176E47062794',
    'D2A2C780-D5EE-4cd5-9A86-3075FFD5C62D',
    'D1263CEE-1464-4abd-BECD-B1445ECA28C7',
    'D0E1D275-4DFB-4d02-A76B-FB51E07C1269',
    'CF964479-35A6-463b-B409-247DA8E06070',
    'CDEEEF9F-266B-4c53-B976-567F3D159B74',
    'C53D0A05-94E6-4e29-BA68-89BEBB8EE815',
    '0442FF36-CEA8-4a98-B18F-9AC9C4A92576',
    '08020071-ECA0-495b-B9AA-974C228C9A55',
    '0BFFF508-9BDE-4437-B907-E3AA3D62172E',
    '0CE06C77-2198-4bd2-BB40-79271C91A287',
    '0D5111A2-2E3F-41b8-B6D9-F0C37427F207',
    '0F898EDC-E171-45cf-840D-D03621A389EE',
    '1BF82BEB-702D-42b2-9E12-3BB8BD9BF8DC',
    '1DBBFF41-C3AF-4f98-B894-DC60B60F21EA',
    '2D0F54A1-053E-46af-A52B-816464DC2EE7',
    '2ED1A2E5-6BAC-4414-B4A2-E78F07778780',
    '331020DF-4E98-4658-866D-F261EC683C07',
    '34C57F53-C51D-45ea-A085-B374FA91FD4A',
    '366ECB7D-665B-41a5-A050-3B50555381C4',
    '38EF7F4B-6D50-4dd4-824F-53DF3C91EB05',
    '3F0996F0-C598-4325-A734-2457A5920AD5',
    '4B2A40AD-6F23-4685-B589-89327E3654EB',
    '4D5B7A2D-A5BC-453c-987F-DE22D6D88C82',
    '5AFA4501-742D-4878-889D-0C875DAF4014',
    '6383DF77-7028-479a-83EA-C9A83E98FAA1',
    '66609CF8-C6BA-4c55-816B-A136D11B776F',
    '7740AC3F-3674-41ec-A78D-9A18FB08D1DB',
    '8BE7CBAB-9743-489b-96C7-025B4BBFB27B',
    '90CFD1D6-ACFF-424e-A92B-8EF8F58BFD26',
    '96C81A43-2EB6-4497-9F8B-E2FCD2171902',
    '9D25547C-DE62-4a96-B076-260E901561BD',
    'BD561741-3920-4dbe-A782-CC8B3A1837EE',
    'BA257E84-E5BD-441c-A754-D5A86F82DFC2',
    'B9FDA021-CFAA-44f8-B9CE-79D859773882',
    'B88A445B-B550-435d-B239-75E8549DED72',
    'B385768B-4ACA-4136-A318-70838B8F3AF3',
    'AED7E801-4936-4011-9B6D-F9BFCACE041E',
    'A3FE51A7-27EF-4e9e-BEC6-0EB6E369D031',
]

def twoInfLineIntersection(p1, p2, p3, p4, isDebug=False):
    x1 = p1[0]
    y1 = p1[1]
    x2 = p2[0]
    y2 = p2[1]
    x3 = p3[0]
    y3 = p3[1]
    x4 = p4[0]
    y4 = p4[1]
    D = (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)
    if isDebug:
        print(D)
    if np.abs(D) < 0.1:
        return None
    px = ( (x1*y2-y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4) ) / D
    py = ( (x1*y2-y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4) ) / D
    return [px, py]

def findBBoxforGroup(group):
    g_max = np.array(group[0]["bbox"]['max'])
    g_min = np.array(group[0]['bbox']['min'])
    for obj in group:
        if obj['bbox']['min'][0] < g_min[0]:
            g_min[0] = obj['bbox']['min'][0]
        if obj['bbox']['min'][2] < g_min[2]:
            g_min[2] = obj['bbox']['min'][2]
        if obj['bbox']['min'][1] < g_min[1]:
            g_min[1] = obj['bbox']['min'][1]
        if obj['bbox']['max'][0] > g_max[0]:
            g_max[0] = obj['bbox']['max'][0]
        if obj['bbox']['max'][2] > g_max[2]:
            g_max[2] = obj['bbox']['max'][2]
        if obj['bbox']['max'][1] >g_max[1]:
            g_max[1] = obj['bbox']['max'][1]
    return g_max,g_min


def normalize(v):
    return v/np.linalg.norm(v)

def pointInLine(p, p1 ,p2):
    p = np.array(p)
    p1 = np.array(p1)
    p2 = np.array(p2)
    # if abs(np.linalg.norm(p1-p)) < 1e-3:
    #     return False
    # if abs(np.linalg.norm(p2-p)) < 1e-3:
    #     return True
    v1 = normalize(p1-p)
    v2 = normalize(p2-p)
    #print(abs(np.dot(v1,v2) +1))
    return abs(np.dot(v1,v2) +1) < 1e-3

def toXZ(pt):
    return np.array([pt[0],pt[2]])

def XZtoXYZ(pt,y = 0):
    return np.array([pt[0],y,pt[1]])

def rotate(v, theta):
    # theta in radian
    v = np.array(v)
    rMatrix = np.array([
        [math.cos(theta),-math.sin(theta)],
        [math.sin(theta),math.cos(theta)]
    ])
    return np.matmul(rMatrix,v)


def Fov(origin,d, target, group):
    origin = np.array(origin)
    target = np.array(target)
    g_max, g_min = findBBoxforGroup(group=group)
    gmax_xz = toXZ(g_max)
    gmin_xz = toXZ(g_min)
    d = toXZ(d)
    span = gmax_xz-gmin_xz

    span_pro = np.linalg.norm(span-np.dot(span,d)*d)
    dist = np.linalg.norm(target-origin)
    
    hfov = np.arctan(span_pro/2/dist)+(np.pi * DELTA_A / 180)
    if hfov > np.pi/4:
        hfov = np.pi/4
    return hfov


def aspect(origin,d,roomshape,hfov):
    height_of_wall = 2.6
    r1 = 16/9
    r2 = 4/3
    origin = np.array(origin)
    d = np.array(d)
    d2d = toXZ(d)
    d1 = rotate(d2d, hfov)
    d2 = rotate(d2d,-hfov)
    edges_num = len(roomshape)
    a = None
    b = None
    for i, vertex in enumerate(roomshape):
        next_v = roomshape[(i+1)%edges_num]
        p3 = toXZ(origin)
        p4 = p3+d1

        p = twoInfLineIntersection(vertex,next_v,p3,p4)
        if p is None:
            continue
        if not pointInLine(p,vertex,next_v):
            continue
        a = p
        break
    for i, vertex in enumerate(roomshape):
        next_v = roomshape[(i+1)%edges_num]
        p3 = toXZ(origin)
        p4 = p3+d2

        p = twoInfLineIntersection(vertex,next_v,p3,p4)
        if p is None:
            continue
        if not pointInLine(p,vertex,next_v):
            continue
        b = p
        break

    a = XZtoXYZ(a)
    b = XZtoXYZ(b)
    
    span = a-b
    span_pro = np.linalg.norm(span-np.dot(span,d)*d)

    if span_pro/height_of_wall<math.sqrt(r1*r2):
        return r2
    else:
        return r1



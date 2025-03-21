import numpy as np
from scipy import stats
import math
import json
import csv

kindlist = []
with open("./layoutmethods/shelfarrangement/Matrix/kindId.txt", 'r') as fp:
        kindlist = list(map(lambda x: x.strip(), fp.readlines()))

modellist = []
with open("./layoutmethods/shelfarrangement/Matrix/modelId.txt", 'r') as fp:
        modellist = list(map(lambda x: x.strip(), fp.readlines()))

priorMatrix = np.loadtxt("./layoutmethods/shelfarrangement/Matrix/priorMatrix.txt")
priorMatrixforKind = np.loadtxt("./layoutmethods/shelfarrangement/Matrix/priorMatrixforKind.txt")

liftMatrix = np.loadtxt("./layoutmethods/shelfarrangement/Matrix/confidentMatrix.txt")
liftMatrixforKind = np.loadtxt("./layoutmethods/shelfarrangement/Matrix/confidentMatrixforKind.txt")

liftMatrixTest = np.loadtxt("./layoutmethods/shelfarrangement/Matrix/liftMatrixTest.txt")
liftMatrixforKindTest = np.loadtxt("./layoutmethods/shelfarrangement/Matrix/liftMatrixforKindTest.txt")

supportMatrix = np.loadtxt("./layoutmethods/shelfarrangement/Matrix/supportMatrix.txt")
supportMatrixforKind = np.loadtxt("./layoutmethods/shelfarrangement/Matrix/supportMatrixforKind.txt")
confidentMatrix = np.loadtxt("./layoutmethods/shelfarrangement/Matrix/confidentMatrix.txt")
confidentMatrixforKind = np.loadtxt("./layoutmethods/shelfarrangement/Matrix/confidentMatrixforKind.txt")

whereMatrix = np.loadtxt("./layoutmethods/shelfarrangement/Matrix/whereMatrix.txt")

similarityMatrix = np.loadtxt("./layoutmethods/shelfarrangement/Matrix/similarityMatrix.txt")
similarityMatrixforKind = np.loadtxt("./layoutmethods/shelfarrangement/Matrix/similarityMatrixforKind.txt")

with open(f'./layoutmethods/shelfarrangement/Matrix/price.json') as f:
    modelPrices = json.load(f)

priceMatrix = np.loadtxt("./layoutmethods/shelfarrangement/Matrix/price2.txt")

model_kind_dict = {}
kind_model_dict = {}
model_class_dict = {}



with open("./layoutmethods/shelfarrangement/Matrix/csv.csv",mode="r",encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        kind_name = row[2]
        class_name = row[1]
        model_name = row[0]
        model_kind_dict[class_name] = kind_name
        model_class_dict[model_name] = class_name
        if kind_model_dict.get(class_name,"") != "":
            kind_model_dict[class_name].append(model_name)
        else:
            kind_model_dict[class_name] = []
            kind_model_dict[class_name].append(model_name)
    f.close()

# print(model_kind_dict)
# print(kind_model_dict)

MINDISTANCE = 121
MINDISTANCEFORWHERE = 64
DISTANCEFUNCPARAM = 0.01
KINDDIFPARAM = 10000000000


class shelf(object):
    x = 0.0
    y = 0.0
    item_list = []
    group_id = 0
    decided_kind = ""
    def __init__(self,x,y,ilist,decided_kind,group_id = -1):
        self.x = x
        self.y = y
        self.item_list =  ilist
        self.decided_kind = decided_kind
        self.group_id = group_id
    def addItem(self,item):
        self.item_list.append(item)

class shelfReturnType(object):
    name = ""
    flag = False
    def __init__(self,name,flag):
        self.name = name
        self.flag = flag


def distanceFunc(distancesquare):
    return math.exp(-DISTANCEFUNCPARAM*distancesquare)

def disForSameKind(distancesquare):
    return math.pow(0.4,1/distancesquare)

def noRecommandKind(room,shelfkey):
    exist_type_list = []
    new_kind_list = sorted(kindlist, key=str.lower)
    for obj in room['objList']:
        if obj["modelId"] == "shelf01":
            try:
                kind = str(obj["shelfType"])
                exist_type_list.append(new_kind_list.index(kind))
            except:
                continue
    recommond_list = []
    for i in range(len(new_kind_list)):
        flag = False
        if exist_type_list.count(i) >= 1:
            flag = True
        recommond_list.append(shelfReturnType(new_kind_list[i],flag))
    recommond_list.append(shelfReturnType("mix",False))
    return recommond_list

def noRecommandItem(room,placeholders):
    new_modle_list = sorted(modellist,key=str.lower)
    for obj in room['objList']:
        if obj["key"] == list(placeholders.keys())[0]:
            try:
                kind = str(obj["shelfType"])
            except:
                print("please select kind first!") ## todo:need to alert in frontend
                return []
    recommond_list = []
    for i in range(len(modellist)):
        if model_kind_dict[new_modle_list[i]] == kind:
            kind_name = new_modle_list[i]
            for j in range(len(kind_model_dict[kind_name])):
                recommond_list.append(kind_model_dict[kind_name][j])
        else:
            continue
    for i in range(len(new_modle_list)):
        if model_kind_dict[new_modle_list[i]] != kind:
            kind_name = new_modle_list[i]
            for j in range(len(kind_model_dict[kind_name])):
                recommond_list.append(kind_model_dict[kind_name][j])
        else:
            continue
    return recommond_list


def clutterRecommandKind(room,shelfkey):
    shelf_list = []
    shelfkeys = list(shelfkey)
    these_shelves = []
    exist_type_list = []
    for obj in room['objList']:
        if shelfkeys.count(obj["key"]) == 1:
            item_list = obj["commodities"]
            item_name_list = []
            for item in item_list:
                for i in item:
                    if i["modelId"] != "":
                        item_name_list.append(i["modelId"])    
            this_shelf = shelf(float(obj["translate"][0]),float(obj["translate"][2]),item_name_list,"")
            these_shelves.append(this_shelf)
        elif obj["modelId"] == "shelf01":
            try:
                kind = str(obj["shelfType"])
                exist_type_list.append(kindlist.index(kind))
            except:
                continue
            item_list = obj["commodities"]
            item_name_list = []
            for item in item_list:
                for i in item:
                    if i["modelId"] != "":
                        item_name_list.append(i["modelId"])
            kind = str(obj["shelfType"])
            x = float(obj["translate"][0])
            y = float(obj["translate"][2])
            new_shelf = shelf(x,y,item_name_list,kind)
            shelf_list.append(new_shelf)
    p_list = []
    p_co_list = []
    p_prior_list = []
    idx_list = []

    x_list = []
    y_list = []
    for i in range(0,len(these_shelves)):
        x_list.append(these_shelves[i].x)
        y_list.append(these_shelves[i].y)
    
    center_x = sum(x_list)/len(x_list)
    center_y = sum(y_list)/len(y_list)


    for idx in range(0,len(kindlist)):
        p_prior = priorMatrixforKind[idx]
        p_co = 1
        for eachshelf in shelf_list:
            otherx = eachshelf.x
            othery = eachshelf.y
            distance = (otherx-center_x)*(otherx-center_x) + (othery - center_y)*(othery - center_y)
            if distance <= 1.5*1.5:
                if(eachshelf.decided_kind == "mix"):
                    continue
                idx_this = kindlist.index(eachshelf.decided_kind)
                p_co = p_co * confidentMatrixforKind[idx_this][idx]
                if(idx_this == idx):
                    p_prior = p_prior
                    p_co = p_co
       
        p_co_list.append(p_co)
        p_prior_list.append(p_prior)
        idx_list.append(idx)

    for i in range(len(p_co_list)): 
        p_co_list[i] = math.log10(p_co_list[i]*100000 + 1)
        p_prior_list[i] = math.log10(p_prior_list[i]*100000 + 1)
        p_list.append(p_co_list[i] + p_prior_list[i])
        # print(p_prior_list[i],p_co_list[i],kindlist[i],p_list[i])

    for i in range(len(p_list) - 1): 
        for j in range(len(p_list) - i - 1): 
            if p_list[j] < p_list[j+1]:
                p_list[j], p_list[j+1] = p_list[j+1], p_list[j]
                idx_list[j],idx_list[j+1] = idx_list[j+1],idx_list[j]
    
    recommond_list = []
    for i in range(len(kindlist)):
        flag = False
        if exist_type_list.count(idx_list[i]) >= 1:
            flag = True
        recommond_list.append(shelfReturnType(kindlist[idx_list[i]],flag))
    recommond_list.append(shelfReturnType("mix",False))
    return recommond_list

def clutterRecommandItem(room,placeholders):
    shelf_list = []
    for obj in room['objList']:
        if obj["key"] == list(placeholders.keys())[0]:
            try:
                kind = str(obj["shelfType"])
            except:
                print("please select kind first!") ## todo:need to alert in frontend
                continue
            item_list = obj["commodities"]
            item_name_list = []
            for item in item_list:
                for i in item:
                    if i["modelId"] != "":
                        item_name_list.append(i["modelId"])    
            this_shelf = shelf(float(obj["translate"][0]),float(obj["translate"][2]),item_name_list,kind)
            shelf_list.append(this_shelf)
        elif obj["modelId"] == "shelf01":
            try:
                kind = str(obj["shelfType"])
            except:
                continue
            item_list = obj["commodities"]
            item_name_list = []
            for item in item_list:
                for i in item:
                    if i["modelId"] != "":
                        item_name_list.append(i["modelId"])
            kind = str(obj["shelfType"])
            x = float(obj["translate"][0])
            y = float(obj["translate"][2])
            new_shelf = shelf(x,y,item_name_list,kind)
            shelf_list.append(new_shelf)
    p_list = []
    p_co_list = []
    p_prior_list = []
    idx_list = []
    for idx in range(0,len(modellist)):
        p_prior = priorMatrix[idx] * 0.1
        p_co = 1

        for nextshelf in shelf_list:
            otherx = nextshelf.x
            othery = nextshelf.y
            distance = (otherx-this_shelf.x)*(otherx-this_shelf.x) + (othery - this_shelf.y)*(othery - this_shelf.y)
            if(distance <= 1.5*1.5):
                item_list = nextshelf.item_list
                for item in item_list:
                    item_class = model_class_dict[item]
                    item_idx = modellist.index(item_class)
                    p_co = p_co * confidentMatrix[item_idx][idx]
                    if(item_idx == idx):
                        p_prior = p_prior 
                        p_co = p_co
        
        p_co_list.append(p_co)
        p_prior_list.append(p_prior)
        idx_list.append(idx)
    

    for i in range(len(p_co_list)): 
        new_p =math.log10(p_co_list[i]*100000 + 1)+ math.log10(p_prior_list[i]*100000 + 1)
        if model_kind_dict[modellist[i]] == this_shelf.decided_kind:
            new_p = new_p * KINDDIFPARAM
        p_list.append(new_p)
        # print(p_prior_list[i],p_co_list[i],p_sim_list[i],modellist[i],p_list[i])
    for i in range(len(p_list) - 1): 
        for j in range(len(p_list) - i - 1): 
            if p_list[j] < p_list[j+1]:
                p_list[j], p_list[j+1] = p_list[j+1], p_list[j]
                idx_list[j],idx_list[j+1] = idx_list[j+1],idx_list[j]
    
    # print(modellist[idx_list[0]])
    recommond_list = []
    for i in range(len(modellist)):
        kind_name = modellist[idx_list[i]]
        for j in range(len(kind_model_dict[kind_name])):
            recommond_list.append(kind_model_dict[kind_name][j])

    return recommond_list


def kindRecommand(room,shelfkey):
    exist_type_list = []
    shelf_list = []
    shelfkeys = list(shelfkey)
    these_shelves = []
    is_entrance = True
    for obj in room['objList']:
        if shelfkeys.count(obj["key"]) == 1:
            item_list = obj["commodities"]
            group_id = obj["groupId"]
            item_name_list = []
            for item in item_list:
                for i in item:
                    if i["modelId"] != "":
                        item_name_list.append(i["modelId"])    
            this_shelf = shelf(float(obj["translate"][0]),float(obj["translate"][2]),item_name_list,"",group_id)
            these_shelves.append(this_shelf)
        elif obj["modelId"] == "cgaxis_models_32_24":
            if is_entrance:
                is_entrance = False
                entrance_x = float(obj["translate"][0])
                entrance_y = float(obj["translate"][2])
            else:
                exit_x = float(obj["translate"][0])
                exit_y = float(obj["translate"][2])
            
        elif obj["modelId"] == "shelf01":
            try:
                kind = str(obj["shelfType"])
            except:
                continue
            item_list = obj["commodities"]
            group_id = obj["groupId"]
            item_name_list = []
            for item in item_list:
                for i in item:
                    if i["modelId"] != "":
                        item_name_list.append(i["modelId"])
            kind = str(obj["shelfType"])
            x = float(obj["translate"][0])
            y = float(obj["translate"][2])
            new_shelf = shelf(x,y,item_name_list,kind,group_id)
            exist_type_list.append(kindlist.index(kind))
            shelf_list.append(new_shelf)
    p_list = []
    p_co_list = []
    p_where_list = []
    p_sim_list = []
    p_prior_list = []
    idx_list = []

    x_list = []
    y_list = []
    for i in range(0,len(these_shelves)):
        x_list.append(these_shelves[i].x)
        y_list.append(these_shelves[i].y)
    
    center_x = sum(x_list)/len(x_list)
    center_y = sum(y_list)/len(y_list)

    group_id = these_shelves[0].group_id


    for idx in range(0,len(kindlist)):
        co_kind = []
        p_prior = priorMatrixforKind[idx]
        p_where = 1

        distance_to_entrance = (entrance_x-center_x)*(entrance_x-center_x) + (entrance_y - center_y)*(entrance_y - center_y)
        distance_to_exit = (exit_x-center_x)*(exit_x-center_x) + (exit_y - center_y)*(exit_y - center_y)
        if distance_to_entrance < MINDISTANCEFORWHERE:
            p_where = whereMatrix[idx][0] * distanceFunc(distance_to_entrance) * p_where
        else:
            p_where = p_where * 1
        if distance_to_exit < MINDISTANCEFORWHERE:
            p_where = whereMatrix[idx][1] * distanceFunc(distance_to_exit) * p_where
        else:
            p_where = p_where * 1
        
        p_co = 1
        p_sim = 1
        for eachshelf in shelf_list:
            otherx = eachshelf.x
            othery = eachshelf.y
            distance = (otherx-center_x)*(otherx-center_x) + (othery - center_y)*(othery - center_y)
            dis = distanceFunc(distance)
            if(eachshelf.decided_kind == "mix"):
                continue
            idx_this = kindlist.index(eachshelf.decided_kind)
            if co_kind.count(idx_this) == 1:
                continue
            else:
                co_kind.append(idx_this)
            p_co = p_co * dis * liftMatrixforKindTest[idx_this][idx]
            p_sim = p_sim * dis *similarityMatrixforKind[idx_this][idx]
            if(idx_this == idx):
                if eachshelf.group_id != group_id and distance >= 9:
                    p_prior = p_prior * disForSameKind(dis)
                    p_co = p_co * disForSameKind(dis)
                    p_sim = p_sim * disForSameKind(dis)
       
        p_co_list.append(p_co)
        p_where_list.append(p_where)
        p_sim_list.append(p_sim)
        p_prior_list.append(p_prior)
        idx_list.append(idx)
    
    # min_p_co = min(p_co_list)*0.98
    # max_p_co = max(p_co_list)*1.02
    # min_p_sim = min(p_sim_list)*0.98
    # max_p_sim = max(p_sim_list)*1.02
    # min_p_where = min(p_where_list)*0.98
    # max_p_where = max(p_where_list)*1.02
    # min_p_prior = min(p_prior_list)*0.98
    # max_p_prior = max(p_prior_list)*1.02

    # for i in range(len(p_co_list)): 
    #     if max_p_co!=min_p_co:
    #         p_co_list[i] = (p_co_list[i] - min_p_co)/(max_p_co - min_p_co)
    #     if max_p_sim!=min_p_sim:
    #         p_sim_list[i] = (p_sim_list[i]-min_p_sim)/(max_p_sim - min_p_sim)
    #     if max_p_prior!= min_p_prior:
    #         p_prior_list[i] = (p_prior_list[i]-min_p_prior)/(max_p_prior - min_p_prior)
    #     if max_p_where != min_p_where:
    #         p_where_list[i] = (p_where_list[i]-min_p_where)/(max_p_where - min_p_where)
    #     p_list.append(p_co_list[i] * p_sim_list[i]*p_prior_list[i]*p_where_list[i])
    #     print(p_prior_list[i],p_co_list[i],p_sim_list[i],p_where_list[i],kindlist[i],p_list[i])

    p_co_list = np.array(p_co_list)
    p_sim_list = np.array(p_sim_list)
    p_where_list = np.array(p_where_list)
    p_prior_list = np.array(p_prior_list)
    average_p_co = np.std(p_co_list)
    average_p_sim = np.std(p_sim_list)
    average_p_where = np.std(p_where_list)
    average_p_prior = np.std(p_prior_list)
    if average_p_co!=0:
        p_co_list = p_co_list/average_p_co
    if average_p_sim!=0:
        p_sim_list = p_sim_list/average_p_sim
    if average_p_where!= 0:
        p_where_list = p_where_list/average_p_where
    if average_p_prior != 0:
        p_prior_list = p_prior_list/average_p_prior
    p_list = p_co_list * p_sim_list * p_where_list * p_prior_list


    for i in range(len(p_list)): 
        print(p_prior_list[i],p_co_list[i],p_sim_list[i],p_where_list[i],kindlist[i],p_list[i])

    

    for i in range(len(p_list) - 1): 
        for j in range(len(p_list) - i - 1): 
            if p_list[j] < p_list[j+1]:
                p_list[j], p_list[j+1] = p_list[j+1], p_list[j]
                idx_list[j],idx_list[j+1] = idx_list[j+1],idx_list[j]
    
    recommond_list = []
    for i in range(len(kindlist)):
        flag = False
        if exist_type_list.count(idx_list[i]) >= 1:
            flag = True
        recommond_list.append(shelfReturnType(kindlist[idx_list[i]],flag))
    recommond_list.append(shelfReturnType("mix",False))
    print(recommond_list)
    return recommond_list


def heightfunction(height):
    height_adult = 1.697        #成人身高
    height_child = 1.12         #小孩身高
    C_ad = 0.7                  #系数
    C_ch = 0.3                  #系数
    if height > height_child:
        return 1
    else:
        return height / height_child
    # P(h1 < h < h2) = stats.norm.cdf(h2, 1.7) - stats.norm.cdf(h1, 1.7)
    return C_ad*stats.norm.pdf(height,height_adult) + C_ch*stats.norm.pdf(height,height_child)

def ModelRecommand(room,placeholders):
    # np.set_printoptions(suppress=True)
    # with open("./layoutmethods/shelfarrangement/Matrix/room.json", "w") as f:
    #     json.dump(room, f)
    # with open("./layoutmethods/shelfarrangement/Matrix/placeholders.json", "w") as f:
    #     json.dump(placeholders, f)
    # print(placeholders)
    shelf_list = []
    for obj in room['objList']:
        if obj["key"] == list(placeholders.keys())[0]:
            try:
                kind = str(obj["shelfType"])
            except:
                print("please select kind first!") ## todo:need to alert in frontend
                continue
            item_list = obj["commodities"]
            item_name_list = []
            for item in item_list:
                for i in item:
                    if i["modelId"] != "":
                        item_name_list.append(i["modelId"])    
            this_shelf = shelf(float(obj["translate"][0]),float(obj["translate"][2]),item_name_list,kind)
            shelf_list.append(this_shelf)
        elif obj["modelId"] == "shelf01":
            try:
                kind = str(obj["shelfType"])
            except:
                continue
            item_list = obj["commodities"]
            item_name_list = []
            for item in item_list:
                for i in item:
                    if i["modelId"] != "":
                        item_name_list.append(i["modelId"])
            kind = str(obj["shelfType"])
            x = float(obj["translate"][0])
            y = float(obj["translate"][2])
            new_shelf = shelf(x,y,item_name_list,kind)
            shelf_list.append(new_shelf)
    p_list = []
    p_co_list = []
    p_where_list = []
    p_sim_list = []
    p_prior_list = []
    idx_list = []

    average_vis = 0
    average_POI = 0
    average_height = 0
    placeholderCount = 0
    for shelfKey in placeholders:
        for placeholderKey in placeholders[shelfKey]:
            average_vis += placeholders[shelfKey][placeholderKey][0]
            average_POI += placeholders[shelfKey][placeholderKey][1]
            average_height += placeholders[shelfKey][placeholderKey][2]
            placeholderCount += 1
    average_vis /= placeholderCount
    average_POI /= placeholderCount
    average_height /= placeholderCount
    vis = 0.5 * average_vis + 0.5 * average_POI + 0.5 * heightfunction(average_height)

    for idx in range(0,len(modellist)):
        co_model = []
        p_prior = priorMatrix[idx] * 0.1
        p_where = priceMatrix[idx]
        p_co = 1
        p_sim = 1

        for nextshelf in shelf_list:
            otherx = nextshelf.x
            othery = nextshelf.y
            distance = (otherx-this_shelf.x)*(otherx-this_shelf.x) + (othery - this_shelf.y)*(othery - this_shelf.y)
            if(distance < MINDISTANCE):
                dis = distanceFunc(distance)
                item_list = nextshelf.item_list
                for item in item_list:
                    item_class = model_class_dict[item]
                    item_idx = modellist.index(item_class)
                    if co_model.count(item_idx) == 1:
                        continue
                    else:
                        co_model.append(item_idx)
                    p_co = p_co * dis * liftMatrixTest[item_idx][idx]
                    p_sim = p_sim * dis * similarityMatrix[item_idx][idx]
                    if(item_idx == idx):
                        p_prior = p_prior * disForSameKind(dis)
                        p_co = p_co * disForSameKind(dis)
                        p_sim = p_sim * disForSameKind(dis)
                        p_where = p_where *disForSameKind(dis)
        
        p_co_list.append(p_co)
        p_where_list.append(p_where)
        p_sim_list.append(p_sim)
        p_prior_list.append(p_prior)
        idx_list.append(idx)
    

    # min_p_co = min(p_co_list)
    # max_p_co = max(p_co_list)
    # min_p_sim = min(p_sim_list)
    # max_p_sim = max(p_sim_list)
    # min_p_where = min(p_where_list)
    # max_p_where = max(p_where_list)
    # min_p_prior = min(p_prior_list)
    # max_p_prior = max(p_prior_list)

    # for i in range(len(p_co_list)): 
    #     if max_p_co!=min_p_co:
    #         p_co_list[i] = (p_co_list[i] - min_p_co)/(max_p_co - min_p_co)
    #     if max_p_sim!=min_p_sim:
    #         p_sim_list[i] = (p_sim_list[i]-min_p_sim)/(max_p_sim - min_p_sim)
    #     if max_p_prior!= min_p_prior:
    #         p_prior_list[i] = (p_prior_list[i]-min_p_prior)/(max_p_prior - min_p_prior)
    #     if max_p_where != min_p_where:
    #         p_where_list[i] = (p_where_list[i]-min_p_where)/(max_p_where - min_p_where)
    #     new_p =p_co_list[i] * p_sim_list[i]*p_prior_list[i]*p_where_list[i]
    #     p_list.append(new_p)
        # print(p_prior_list[i],p_co_list[i],p_sim_list[i],modellist[i],p_list[i])

    p_co_list = np.array(p_co_list)
    p_sim_list = np.array(p_sim_list)
    p_where_list = np.array(p_where_list)
    p_prior_list = np.array(p_prior_list)
    average_p_co = np.std(p_co_list)
    average_p_sim = np.std(p_sim_list)
    average_p_where = np.std(p_where_list)
    average_p_prior = np.std(p_prior_list)
    if average_p_co!=0:
        p_co_list = p_co_list/average_p_co
    if average_p_sim!=0:
        p_sim_list = p_sim_list/average_p_sim
    if average_p_where!= 0:
        p_where_list = vis*p_where_list/average_p_where
    if average_p_prior != 0:
        p_prior_list = p_prior_list/average_p_prior
    p_list = p_co_list * p_sim_list * p_where_list * p_prior_list


    # for i in range(len(p_list)): 
    #     print(p_prior_list[i],p_co_list[i],p_sim_list[i],p_where_list[i],kindlist[i],p_list[i])
    for i in range(len(p_list) - 1): 
        for j in range(len(p_list) - i - 1): 
            if p_list[j] < p_list[j+1]:
                p_list[j], p_list[j+1] = p_list[j+1], p_list[j]
                idx_list[j],idx_list[j+1] = idx_list[j+1],idx_list[j]
    
    # print(modellist[idx_list[0]])
    recommond_list = []
    for i in range(len(modellist)):
        kind_name = modellist[idx_list[i]]
        if model_kind_dict[kind_name] == this_shelf.decided_kind:
            # print(kind_name, p_co_list[idx_list[i]], p_sim_list[idx_list[i]], p_where_list[idx_list[i]], priceMatrix[idx_list[i]], vis, average_p_where)
            for j in range(len(kind_model_dict[kind_name])):
                recommond_list.append(kind_model_dict[kind_name][j])
    # print()
    
    for i in range(len(modellist)):
        kind_name = modellist[idx_list[i]]
        if model_kind_dict[kind_name] != this_shelf.decided_kind:
            for j in range(len(kind_model_dict[kind_name])):
                recommond_list.append(kind_model_dict[kind_name][j])
    return recommond_list

    
    
    
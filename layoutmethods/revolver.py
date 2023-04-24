import json
import os
import numpy as np
import math
import csv

def pointProjectToLineSeg(p, p1, p2):
    p = np.array(p)
    p1 = np.array(p1)
    p2 = np.array(p2)
    return np.dot(p2-p1, p2-p) / np.linalg.norm(p2-p1)

with open('../dataset/objCatListLG.json') as f:
    objCatListLG = json.load(f)

origin, xaxis, yaxis, zaxis = [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]
def wall_distance_orient():
    import trimesh
    level_root = "../dataset/Levels2021/"
    with open('../dataset/sk_to_ali.json') as f:
        obj_semantic = json.load(f)

    level_dirs = os.listdir(level_root)
    objMeshCache = {}
    csvfile = open('revolver.csv', 'w', newline='')
    csvwriter = csv.writer(csvfile, delimiter=' ', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for i in range(0, len(level_dirs)):
        dire = level_dirs[i]
        print('(%d/%d) tackle ' % (i + 1, len(level_dirs)) + dire)
        with open(f'../dataset/Levels2021/{dire}', 'r') as f:
            print(dire) 
            h = json.load(f)
        for i in range(0, len(h['rooms'])):
            room = h['rooms'][i]
            if 'roomShape' not in room:
                continue
            shape = np.array(room['roomShape'])
            if len(shape) <= 2:
                continue
            for i in range(len(room['objList'])):
                obji = room['objList'][i]

                if obji['modelId'] not in obj_semantic:
                    continue
                if 'translate' not in obji:
                    continue
                if 'orient' not in obji:
                    continue
                if len(objCatListLG[obji['modelId']]) == 0:
                    continue

                # find the nearest wall; 
                p = np.array([obji['translate'][0], obji['translate'][2]])
                shapeEnd = shape[np.arange(1,len(shape)).tolist() + [0]]
                a_square = np.sum((shape - p)**2, axis=1)
                b_square = np.sum((shapeEnd - p)**2, axis=1)
                c_square = np.sum((shape - shapeEnd)**2, axis=1)
                area_double = 0.5 * np.sqrt(4 * a_square * b_square - (a_square + b_square - c_square)**2 )
                distances = area_double / np.sqrt(c_square)
                _indicesList = []
                wallMinIndices = np.argsort(distances)
                innerProducts = np.sum((shape - p) * (shape - shapeEnd), axis=1)
                for i in wallMinIndices:
                    if 0 <= innerProducts[i] and innerProducts[i] <= c_square[i]:
                        _indicesList.append(i)
                        if len(_indicesList) == 2:
                            break
                        # wallMinIndex = i
                if len(_indicesList) < 2:
                    continue
                wallMinIndex = _indicesList[0]
                minDistance = distances[wallMinIndex]
                secMinDistance = distances[_indicesList[1]]

                wallLengthes = np.linalg.norm(shape - shapeEnd, axis=1)

                # calculate the wall orient; 
                wn = (shape[wallMinIndex] - shapeEnd[wallMinIndex])[[1,0]]
                wn[1] = -wn[1]

                # ori_prior equals to ori_final - ori_wall; 
                ori = obji['orient'] - np.arctan2(wn[0], wn[1])
                while ori > math.pi:
                    ori -= 2 * math.pi
                while ori < -(math.pi):
                    ori += 2 * math.pi

                # calculate the length of this object w.r.t the wall; 
                # wd = shapeEnd[wallMinIndex] - shape[wallMinIndex]
                # wallorient = np.arctan2(wd[0], wd[1])
                Ry = trimesh.transformations.rotation_matrix(-np.arctan2(wn[0], wn[1]), yaxis)
                try:
                    if obji['modelId'] in objMeshCache:
                        _mesh = objMeshCache[obji['modelId']]
                    else:
                        print('loading ... ' + obji['modelId'])
                        _mesh = trimesh.load(f'../dataset/object/{obji["modelId"]}/{obji["modelId"]}.obj')
                        objMeshCache[obji['modelId']] = _mesh
                    # we always take the copy before modifying it; 
                    mesh = _mesh.copy()
                    mesh.vertices *= np.array(obji['scale'])
                    mesh.apply_transform(Ry)
                    objWallLength = np.max(mesh.vertices[:, 0]) - np.min(mesh.vertices[:, 0])
                    objWallLength = objWallLength.tolist() / 2 
                except Exception as e:
                    print(e)
                    objWallLength = 0

                projectedLength1 = pointProjectToLineSeg([obji['translate'][0], obji['translate'][2]], shape[_indicesList[0]], shapeEnd[_indicesList[0]])
                projectedLength2 = wallLengthes[_indicesList[0]] - projectedLength1
                csvwriter.writerow([objCatListLG[obji['modelId']], obji['translate'], ori, obji['scale'], minDistance, secMinDistance, wallLengthes[_indicesList[0]], wallLengthes[_indicesList[1]], projectedLength1, projectedLength2])
    csvfile.close()

if __name__ == '__main__':
    wall_distance_orient()
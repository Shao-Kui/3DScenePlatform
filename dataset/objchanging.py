import trimesh
import numpy as np
import shutil
import os
import json

# with open('suncgalimapping.json') as f:
with open('E:/CVPR 2020/tvcgfig12/suncgalimapping.json') as f:
    mapping = json.load(f)

def maxmin(x):
    return np.max(x) - np.min(x)

# code is from https://github.com/mikedh/trimesh/issues/507
def as_mesh(scene_or_mesh):
    """
    Convert a possible scene to a mesh.

    If conversion occurs, the returned mesh has only vertex and face data.
    """
    if isinstance(scene_or_mesh, trimesh.Scene):
        if len(scene_or_mesh.geometry) == 0:
            mesh = None  # empty scene
        else:
            # we lose texture information here
            mesh = trimesh.util.concatenate(
                tuple(trimesh.Trimesh(vertices=g.vertices, faces=g.faces)
                    for g in scene_or_mesh.geometry.values()))
    else:
        # assert(isinstance(mesh, trimesh.Trimesh))
        mesh = scene_or_mesh
    return mesh

PROOT = '../latentspace/pos-orient-3/{}.json'
def switchPattern(i, j):
    newname = '_to_'.join([j, i])
    if not os.path.exists(PROOT.format(i)):
        return
    with open(PROOT.format(i)) as f:
        pattern_i = json.load(f)
    pattern_new = pattern_i.copy()
    for item in pattern_i:
        if item not in mapping:
            continue
        if mapping[item] == "":
            continue
        pattern_new['_to_'.join([mapping[item], item])] = pattern_i[item]
    with open(PROOT.format(newname), 'w') as f:
        json.dump(pattern_new, f)

def switchModel(i, j):
    mesh_i = as_mesh(trimesh.load(f'./object/{i}/{i}.obj'))
    mesh_j = as_mesh(trimesh.load(f'./object/{j}/{j}.obj'))
    # i / j
    mesh_j.vertices[:, 0] *= maxmin(mesh_i.vertices[:, 0])/maxmin(mesh_j.vertices[:, 0])
    mesh_j.vertices[:, 1] *= maxmin(mesh_i.vertices[:, 1])/maxmin(mesh_j.vertices[:, 1])
    mesh_j.vertices[:, 2] *= maxmin(mesh_i.vertices[:, 2])/maxmin(mesh_j.vertices[:, 2])
    newname = '_to_'.join([j, i])
    if not os.path.exists(f'./object/{newname}/render20/'):
        os.makedirs(f'./object/{newname}/render20')
    mesh_j.export(f'./object/{newname}/{newname}.obj')
    with open(f'./object/{newname}/{newname}.obj') as f:
        mesh_j_txt = f.read()
    if 'mtllib material0.mtl' in mesh_j_txt:
        mesh_j_txt = mesh_j_txt.replace('mtllib material0.mtl', f'mtllib {newname}.mtl')
    else:
        mesh_j_txt = f'mtllib {newname}.mtl\n' + mesh_j_txt
    mesh_j_txt = mesh_j_txt.replace('usemtl material0', 'usemtl tsushima')
    with open(f'./object/{newname}/{newname}.obj', 'w') as f:
        f.write(mesh_j_txt)
    shutil.copy(f'./object/{j}/{j}.mtl', f'./object/{newname}/{newname}.mtl')
    shutil.copy(f'./object/{j}/render20/render-{j}-10.png', f'./object/{newname}/render20/render-{newname}-10.png')

def planitfixing(config):
    for room, roomId in zip(config['rooms'], range(len(config['rooms']))):
        room['roomId']
        for o in room['objList']:
            if o is None:
                continue
            o['roomId'] = roomId
            if o['modelId'] in mapping:
                if mapping[o['modelId']] != "":
                    o['modelId'] = '_to_'.join([mapping[o['modelId']], o['modelId']])
    return config

if __name__ == "__main__":
    for m in mapping:
        if mapping[m] == "":
            continue
        print(f'switching {m} and {mapping[m]} ...')
        switchModel(m, mapping[m])
        # switchPattern(m, mapping[m])
    # casenames = os.listdir('./planit/')
    # for casename in casenames:
    #     casefilejson = ""
    #     for f in os.listdir(f'./planit/{casename}'):
    #         if '.json' in f:
    #             casefilejson = f
    #             break
    #     with open(f'./planit/{casename}/{casefilejson}') as fj:
    #         config = json.load(fj)
    #     if not os.path.exists(f'./planitfix/{casename}/'):
    #         os.makedirs(f'./planitfix/{casename}/')
    #     with open(f'./planitfix/{casename}/{casefilejson}', 'w') as f:
    #         json.dump(planitfixing(config), f)
    
    casenames = os.listdir('E:/CVPR 2020/tvcgfig12/origin')
    for casename in casenames:
        with open(f'E:/CVPR 2020/tvcgfig12/origin/{casename}') as fj:
            config = json.load(fj)
        with open(f'E:/CVPR 2020/tvcgfig12/fixed/{casename}', 'w') as f:
            json.dump(planitfixing(config), f)

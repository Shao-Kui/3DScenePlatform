import json
import torch
import numpy as np

with open('./latentspace/obj-semantic.json') as f:
    obj_semantic = json.load(f)
with open('./latentspace/name_to_ls.json') as f:
    name_to_ls = json.load(f)
with open('./latentspace/ls_to_name.json') as f:
    ls_to_name = json.load(f)

csrmatrix = torch.from_numpy(np.load("./latentspace/csrmatrix.npy")).float()
csrmatrix[name_to_ls['679']] = 0.0
csrmatrix[name_to_ls['681']] = 0.0
csrmatrix[:, name_to_ls['679']] = 0.0
csrmatrix[:, name_to_ls['681']] = 0.0
csrmatrix[name_to_ls['236']] = 0.0
csrmatrix[:, name_to_ls['236']] = 0.0
csrmatrix[name_to_ls['680']] = 0.0
csrmatrix[:, name_to_ls['680']] = 0.0
csrmatrix[name_to_ls['458']] = 0.0
csrmatrix[:, name_to_ls['458']] = 0.0

ymatrix = torch.from_numpy(np.load("./latentspace/ymatrix.npy")).float()
ymatrix[name_to_ls['271'], name_to_ls['267']] = 1.0
ymatrix[name_to_ls['267'], name_to_ls['271']] = 1.0
ymatrix[name_to_ls['83'], name_to_ls['79']] = 1.0
ymatrix[name_to_ls['79'], name_to_ls['83']] = 1.0

wallvector = torch.zeros((len(obj_semantic))).float()
wallvector[name_to_ls['266']] = 1.0

cornervector = torch.zeros((len(obj_semantic))).float()
cornervector[name_to_ls['266']] = 1.0

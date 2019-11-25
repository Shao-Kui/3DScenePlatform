import json
import torch
import numpy as np

with open('./latentspace/obj-semantic.json') as f:
    obj_semantic = json.load(f)
with open('./latentspace/name_to_ls.json') as f:
    name_to_ls = json.load(f)
with open('./latentspace/ls_to_name.json') as f:
    ls_to_name = json.load(f)

csrbanlist = ['522', '144', '257', '153', '251', '138', '271', '781', '235', '124', '493', '736', '225', '508', '481']
csrmatrix = torch.from_numpy(np.load("./latentspace/csrmatrix_53.npy")).float()
csrmatrix[(torch.arange(len(csrmatrix)), torch.arange(len(csrmatrix)))] = 0.0
csrmatrix[name_to_ls['679']] = 0.0
csrmatrix[name_to_ls['681']] = 0.0
csrmatrix[:, name_to_ls['679']] = 0.0
csrmatrix[:, name_to_ls['681']] = 0.0
csrmatrix[name_to_ls['236']] = 0.0
csrmatrix[:, name_to_ls['236']] = 0.0
csrmatrix[name_to_ls['238']] = 0.0
csrmatrix[:, name_to_ls['238']] = 0.0
csrmatrix[name_to_ls['680']] = 0.0
csrmatrix[:, name_to_ls['680']] = 0.0
csrmatrix[name_to_ls['458']] = 0.0
csrmatrix[:, name_to_ls['458']] = 0.0
for i in csrbanlist:
    csrmatrix[name_to_ls[i]] = 0.0
    csrmatrix[:, name_to_ls[i]] = 0.0
csrmatrix[name_to_ls['495'], name_to_ls['189']] = 1.0
csrmatrix[name_to_ls['189'], name_to_ls['495']] = 1.0
csrmatrix[name_to_ls['261'], name_to_ls['109']] = 1.0
csrmatrix[name_to_ls['109'], name_to_ls['261']] = 1.0
csrmatrix[name_to_ls['115'], name_to_ls['168']] = 1.0
csrmatrix[name_to_ls['168'], name_to_ls['115']] = 1.0
csrmatrix[name_to_ls['113'], name_to_ls['617']] = 1.0
csrmatrix[name_to_ls['617'], name_to_ls['113']] = 1.0

csrmatrix[name_to_ls['428'], name_to_ls['106']] = 1.0
csrmatrix[name_to_ls['106'], name_to_ls['428']] = 1.0
csrmatrix[name_to_ls['75'], name_to_ls['558']] = 1.0
csrmatrix[name_to_ls['105'], name_to_ls['516']] = 1.0

csrmatrix[name_to_ls['s__881'], name_to_ls['197']] = 1.0
csrmatrix[name_to_ls['s__881'], name_to_ls['558']] = 1.0

csrmatrix[name_to_ls['71'], name_to_ls['170']] = 1.0
csrmatrix[name_to_ls['71'], name_to_ls['57']] = 1.0
csrmatrix[name_to_ls['71'], name_to_ls['166']] = 1.0
csrmatrix[name_to_ls['170'], name_to_ls['71']] = 1.0
csrmatrix[name_to_ls['57'], name_to_ls['71']] = 1.0
csrmatrix[name_to_ls['166'], name_to_ls['71']] = 1.0

csrmatrix[name_to_ls['278'], name_to_ls['320']] = 0.0
csrmatrix[name_to_ls['320'], name_to_ls['278']] = 0.0
csrmatrix[name_to_ls['266'], name_to_ls['267']] = 0.0
csrmatrix[name_to_ls['267'], name_to_ls['266']] = 0.0
csrmatrix[name_to_ls['45'], name_to_ls['86']] = 0.0
csrmatrix[name_to_ls['86'], name_to_ls['45']] = 0.0
csrmatrix[name_to_ls['45'], name_to_ls['101']] = 0.0
csrmatrix[name_to_ls['101'], name_to_ls['45']] = 0.0
csrmatrix[name_to_ls['101'], name_to_ls['86']] = 0.0
csrmatrix[name_to_ls['86'], name_to_ls['101']] = 0.0
csrmatrix[name_to_ls['407'], name_to_ls['446']] = 0.0
csrmatrix[name_to_ls['446'], name_to_ls['407']] = 0.0
csrmatrix[name_to_ls['89'], name_to_ls['189']] = 0.0
csrmatrix[name_to_ls['189'], name_to_ls['89']] = 0.0
csrmatrix[name_to_ls['89'], name_to_ls['258']] = 0.0
csrmatrix[name_to_ls['258'], name_to_ls['89']] = 0.0
csrmatrix[name_to_ls['57'], name_to_ls['170']] = 0.0
csrmatrix[name_to_ls['170'], name_to_ls['57']] = 0.0
csrmatrix[name_to_ls['166'], name_to_ls['170']] = 0.0
csrmatrix[name_to_ls['170'], name_to_ls['166']] = 0.0

ybanlist = ['235']
ymatrix = torch.from_numpy(np.load("./latentspace/ymatrix.npy")).float()
for i in ybanlist:
    ymatrix[name_to_ls[i]] = 0.0
    ymatrix[:, name_to_ls[i]] = 0.0
ymatrix[name_to_ls['271'], name_to_ls['267']] = 1.0
ymatrix[name_to_ls['267'], name_to_ls['271']] = 1.0
ymatrix[name_to_ls['83'], name_to_ls['79']] = 1.0
ymatrix[name_to_ls['79'], name_to_ls['83']] = 1.0

wallvector = torch.zeros((len(obj_semantic))).float()
wallvector[name_to_ls['266']] = 1.0
wallvector[name_to_ls['108']] = 1.0
wallvector[name_to_ls['144']] = 1.0
wallvector[name_to_ls['259']] = 1.0
wallvector[name_to_ls['495']] = 1.0
wallvector[name_to_ls['634']] = 1.0
wallvector[name_to_ls['737']] = 1.0
wallvector[name_to_ls['199']] = 1.0
wallvector[name_to_ls['668']] = 1.0
wallvector[name_to_ls['398']] = 1.0
wallvector[name_to_ls['115']] = 1.0
wallvector[name_to_ls['124']] = 1.0
# wallvector[name_to_ls['612']] = 1.0
wallvector[name_to_ls['86']] = 1.0
wallvector[name_to_ls['101']] = 1.0
wallvector[name_to_ls['45']] = 1.0
wallvector[name_to_ls['493']] = 1.0
wallvector[name_to_ls['116']] = 1.0
wallvector[name_to_ls['736']] = 1.0
wallvector[name_to_ls['167']] = 1.0
wallvector[name_to_ls['78']] = 1.0

cornervector = torch.zeros((len(obj_semantic))).float()
cornervector[name_to_ls['266']] = 1.0
cornervector[name_to_ls['267']] = 1.0
cornervector[name_to_ls['733']] = 1.0
cornervector[name_to_ls['517']] = 1.0
cornervector[name_to_ls['251']] = 1.0
cornervector[name_to_ls['138']] = 1.0
cornervector[name_to_ls['623']] = 1.0
cornervector[name_to_ls['612']] = 1.0
cornervector[name_to_ls['398']] = 1.0
cornervector[name_to_ls['271']] = 1.0
cornervector[name_to_ls['s__523']] = 1.0
cornervector[name_to_ls['108']] = 10.0

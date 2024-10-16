import os 
import json

name_to_ls = {}
ls_to_name = {}

objnames = os.listdir('./object/')

index = 0
for objname in objnames:
    if os.path.exists(f'./object/{objname}/{objname}.obj'):
        name_to_ls[objname] = index
        ls_to_name[index] = objname
        index += 1

with open('./name_to_ls.json', 'w') as f:
    json.dump(name_to_ls, f)

with open('./ls_to_name.json', 'w') as f:
    json.dump(ls_to_name, f)

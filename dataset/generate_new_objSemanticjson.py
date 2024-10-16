import json

with open('./name_to_ls.json') as f:
    objnames = list(json.load(f).keys())
with open('F:/3DFurniture/sk_to_ali.json') as f:
    sk_to_ali = json.load(f)
with open('./full-obj-semantic_suncg.json') as f:
    os_suncg = json.load(f)
with open('F:/3DFurniture/model_info.json') as f:
    os_ali = json.load(f)

result = {}
for objname in objnames:
    if objname in os_suncg:
        result[objname] = os_suncg[objname]
    else:
        try:
            result[objname] = next((x for x in os_ali if x['model_id'] == sk_to_ali[objname]))['super-category']
            result[objname] = result[objname].replace('/', '_')
        except Exception as e:
            print(e)
with open('./obj_coarse_semantic.json', 'w') as f:
    json.dump(result, f)

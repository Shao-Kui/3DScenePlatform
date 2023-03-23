import json
import faiss
import numpy as np


with open('./all_suncg.json', 'r') as f:
    suncg_dict = json.load(f)

with open('../catalog.json', 'r') as f:
    catalog = json.load(f)

catalog_suncg = {
    "models": []
}
catalog_non_suncg = {
    "models": []
}

suncg_idx = []
non_suncg_idx = []

for i, model in enumerate(catalog["models"]):
    if model in suncg_dict:
        catalog_suncg["models"].append(model)
        suncg_idx.append(i)
    else:
        catalog_non_suncg["models"].append(model)
        non_suncg_idx.append(i)

with open('./catalog_suncg.json', 'w') as f:
    json.dump(catalog_suncg, f)

with open('./catalog_non_suncg.json', 'w') as f:
    json.dump(catalog_non_suncg, f)


suncg_idx = np.array(suncg_idx)
non_suncg_idx = np.array(non_suncg_idx)

model_lib = faiss.read_index('./models.index')

features = model_lib.reconstruct_n(0, model_lib.ntotal)
# print(features.shape)
# print(type(features))
# print(len(catalog["models"]))
suncg_features = features[suncg_idx]
non_suncg_features = features[non_suncg_idx]

# print(suncg_features.shape)
# print(non_suncg_features.shape)

suncg_model_lib = faiss.IndexFlatL2(suncg_features.shape[1])
non_suncg_model_lib = faiss.IndexFlatL2(non_suncg_features.shape[1])

suncg_model_lib.add(suncg_features)
non_suncg_model_lib.add(non_suncg_features)

print(suncg_model_lib.ntotal)
print(non_suncg_model_lib.ntotal)

faiss.write_index(suncg_model_lib, "./suncg_models.index")
faiss.write_index(non_suncg_model_lib, "./non_suncg_models.index")

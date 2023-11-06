import numpy as np
import json
from math import *
from tqdm import tqdm

with open('dataset.json', 'r') as dataset_json:
    with open('object/validlist.txt', 'r') as valid_list_txt:
        valid_list = [line.strip() for line in valid_list_txt.readlines()]
        dataset = json.load(dataset_json)
        length = len(valid_list)
        relations = [[0 for j in range(length)] for i in range(length)]
        name_index_dict = {}
        for i in range(length):
            name_index_dict[valid_list[i]] = i
        for data_obj in dataset:
            if data_obj['mainObjId'] in name_index_dict:
                index1 = name_index_dict[data_obj['mainObjId']]
                if 'gtrans' in data_obj and 'state':
                    for relation in data_obj['gtrans']:
                        if 'currentState' in relation:
                            index2 = name_index_dict[relation['attachedObjId']]
                            relations[index1][index2] += 1
                            if index1 != index2:
                                relations[index2][index1] += 1
                if 'wall' in data_obj and len(data_obj['wall']) > 0:
                    relations[index1][index1] += 1
        result = []
        for i in tqdm(range(length)):
            for j in range(i + 1, length):
                for k in range(j + 1, length):
                    for l in range(k + 1, length):
                        total_relations = relations[i][j] + relations[i][k] + relations[i][l] + relations[j][
                            k] + relations[j][l] + relations[k][l] + relations[i][i] + relations[j][j] + relations[k][
                                k] + relations[l][l]
                        result.append((total_relations, (i, j, k, l)))
        result.sort(reverse=True)
        print(len(result))
        with open('calc_result.txt', 'w') as out:
            for i in range(100):
                total_str = '('
                for index in (list)(result[i][1]):
                    total_str += valid_list[index] + ','
                total_str += ') {}\n'.format(result[i][0])
                out.write(total_str)

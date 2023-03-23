import xlrd
import re
import json

workbook = xlrd.open_workbook(filename='./形变模组_1.xlsx')
table = workbook.sheets()[0]
res = {}

for r in range(0, table.nrows):
    if table.cell_value(rowx=r, colx=1) not in res:
        res[table.cell_value(rowx=r, colx=1)] = []
    res[table.cell_value(rowx=r, colx=1)].append({'modelId': table.cell_value(rowx=r, colx=0), 'status': 'origin'})
    if table.cell_value(rowx=r, colx=7) not in res:
        res[table.cell_value(rowx=r, colx=7)] = []
    res[table.cell_value(rowx=r, colx=7)].append({'modelId': table.cell_value(rowx=r, colx=0), 'status': table.cell_value(rowx=r, colx=7)})


    # 中文
    nextKey = table.cell_value(rowx=r, colx=2)
    if nextKey not in res:
        res[nextKey] = []
        print(nextKey)
    res[nextKey].append({'modelId': table.cell_value(rowx=r, colx=0), 'status': 'origin'})
    nextKey = table.cell_value(rowx=r, colx=9)
    if nextKey not in res:
        res[nextKey] = []
        print(nextKey)
    res[nextKey].append({'modelId': table.cell_value(rowx=r, colx=0), 'status': table.cell_value(rowx=r, colx=7)})

    if(table.cell_value(rowx=r, colx=14) == ''):
        continue
    nextKey = table.cell_value(rowx=r, colx=14)
    if nextKey not in res:
        res[nextKey] = []
    res[nextKey].append({'modelId': table.cell_value(rowx=r, colx=0), 'status': nextKey})
    nextKey = table.cell_value(rowx=r, colx=15)
    if nextKey not in res:
        res[nextKey] = []
        print(nextKey)
    res[nextKey].append({'modelId': table.cell_value(rowx=r, colx=0), 'status': table.cell_value(rowx=r, colx=14)})


with open('./transModuleIndex.json', 'w') as f:
    json.dump(res, f)

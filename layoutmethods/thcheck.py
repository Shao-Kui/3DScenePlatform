import os

ids = os.listdir('./cgseries')
for id in ids:
    series = os.listdir(f'./cgseries/{id}')
    if len(series) == 0:
        print(f'!!! EMPTY {id}')
        continue
    for s in series:
        files = os.listdir(f'./cgseries/{id}/{s}')
        p = 0
        j = 0
        for f in files:
            if f == 'result.json':
                continue
            elif '.json' in f:
                j += 1
            elif '.png' in f:
                p += 1
        if p < j:
            print(f'{id}/{s} json: {j} png: {p}')
        elif j < 15:
            print(f'{id}/{s} {j}')
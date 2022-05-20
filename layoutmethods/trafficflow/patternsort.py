from pattern import *
from params import *

TARGET_NUMBER = SET_NUMBER


def sort(trial: int):
    if os.path.exists('models/full' + (str)(TARGET_NUMBER) + '_' + (str)(trial) + '.npy'):
        model = np.load('models/full' + (str)(TARGET_NUMBER) + '_' + (str)(trial) + '.npy', allow_pickle=True).tolist()
    context = model[1]
    contextCount = model[2]
    bundle = [[context[i], contextCount[i]] for i in range(SET_NUMBER)]
    bundle = sorted(bundle, key=cmp_to_key(contextCostCmp))
    newContext = [bundle[i][0] for i in range(SET_NUMBER)]
    newContextCount = [bundle[i][1] for i in range(SET_NUMBER)]
    fullResult = [model[0], newContext, newContextCount, model[3]]
    np.save('models/full' + (str)(TARGET_NUMBER) + '_' + (str)(trial) + '.npy', np.array(fullResult, dtype=object))


if __name__ == '__main__':
    for i in range(0, TRIALS):
        sort(i)

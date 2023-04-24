import numpy as np
import math
import csv

kindlist = []
with open("./Matrix/kindId.txt", 'r') as fp:
        kindlist = list(map(lambda x: x.strip(), fp.readlines()))

modellist = []
with open("./Matrix/modelId.txt", 'r') as fp:
        modellist = list(map(lambda x: x.strip(), fp.readlines()))

priorMatrix = np.loadtxt("./Matrix/priorMatrix.txt")
priorMatrixforKind = np.loadtxt("./Matrix/priorMatrixforKind.txt")

liftMatrix = np.loadtxt("./Matrix/liftMatrix.txt")
liftMatrixforKind = np.loadtxt("./Matrix/liftMatrixforKind.txt")
supportMatrix = np.loadtxt("./Matrix/supportMatrix.txt")
supportMatrixforKind = np.loadtxt("./Matrix/supportMatrixforKind.txt")
confidentMatrix = np.loadtxt("./Matrix/confidentMatrix.txt")
confidentMatrixforKind = np.loadtxt("./Matrix/confidentMatrixforKind.txt")

whereMatrix = np.loadtxt("./Matrix/whereMatrix.txt")

similarityMatrix = np.loadtxt("./Matrix/similarityMatrix.txt")
similarityMatrixforKind = np.loadtxt("./Matrix/similarityMatrixforKind.txt")

for i in range(len(kindlist)):
    liftMatrixforKind[i][i] = 1
for i in range(len(modellist)):
    liftMatrix[i][i] = 1

np.savetxt("liftMatrixforKindTest.txt",liftMatrixforKind)
np.savetxt("liftMatrixdTest.txt",liftMatrix)
    
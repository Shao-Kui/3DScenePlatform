import numpy as np
import os
import json
import functools
import pdb
import skimage.draw
import skimage.filters
import scipy.misc
import sklearn.decomposition
import random
import skimage.transform
import joblib
import time
import sklearn.mixture

with open("ModelCategoryMapping.csv","r") as mappingf:
	lines=map(lambda x:x.split(","),mappingf.read().split("\n"))
	coarsemappingdict={line[1]:line[3] for line in lines}
	finemappingdict={line[1]:line[2] for line in lines}

coarse_categories=sorted(list(set(coarsemappingdict.values())))
fine_categories=sorted(list(set(finemappingdict.values())))
ncoarse=len(coarse_categories)
nfine=len(fine_categories)
coarse_mapping={coarse_categories[i]:i for i in range(ncoarse)}
fine_mapping={fine_categories[i]:i for i in range(nfine)}


binrel=joblib.load("binrel.bin")

binindex={}

def gmmtry(data):
	if(data.shape[0]>200000):
		choice=np.random.choice(np.arange(data.shape[0]),200000)
		data_=data[choice]
	else:
		data_=data
	gmmrange=range(1,max(2,min(10,int(data.shape[0]/2))))
	gmms=[sklearn.mixture.GaussianMixture(n_components=i) for i in gmmrange]
	[gmm.fit(data_) for gmm in gmms]
	bics=[gmm.bic(data_) for gmm in gmms]
	return gmms[np.argmin(bics)]
cnt=0
for key in binrel:
	cnt+=1
	print("%d/%d"%(cnt,len(binrel)))
	print(key)
	try:
		rel=np.array(binrel[key])
		relquant=np.round(rel[:,3:]/(0.25*np.pi))
		relquant[relquant<0]+=8
		relquant[relquant>=8]-=8
		rel[:,3:]=relquant
		posmodel=gmmtry(rel[:,:3])
		posrotmodel=gmmtry(rel)
		rotmodel=gmmtry(relquant)
		binindex[key]={"nsample":len(rel),"posmodel":posmodel,"posrotmodel":posrotmodel,"rotmodel":rotmodel}
	except:
		print("error!")
	
joblib.dump(binindex,"binindex.bin")
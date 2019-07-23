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
import sklearn.neighbors 

suncg_root=os.path.join("..","suncg")
levels_root="test"
rooms_root="room"

lfilter=lambda f,x:list(filter(f,x))
lmap=lambda f,x:list(map(f,x))

cos=np.cos
sin=np.sin

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
def area(c):
	corner=np.array(c)
	n = len(corner) # of corners
	'''
	area = 0.0
	for i in range(n):
		j = (i + 1) % n
		area += corners[i][0] * corners[j][1]
		area -= corners[j][0] * corners[i][1]
	area = abs(area) / 2.0
	'''
	corner2=np.roll(corner,1,axis=0)
	area=np.sum(corner[:,0]*corner2[:,1])-np.sum(corner[:,1]*corner2[:,0])
	return area

obj_binary_stat={}
def profile_room(room):
	objs=room["objList"]
	poss=np.array(lmap(lambda x:x["translate"],objs))
	rots=np.array(lmap(lambda x:x["rotate"],objs))
	dists=np.linalg.norm(poss[np.newaxis,:,:]-poss[:,np.newaxis,:],axis=2)
	for i1 in range(len(objs)):
		for i2 in np.argsort(dists[i1])[1:int(min(5,2+len(objs)*0.25,len(objs)-1))]:
			o1,o2=objs[i1],objs[i2]
			t1,t2=coarse_mapping[coarsemappingdict[o1["modelId"]]],coarse_mapping[coarsemappingdict[o2["modelId"]]]
			if(not((t1,t2) in obj_binary_stat)):
				obj_binary_stat[(t1,t2)]=[]
			reltrans=np.array(o1["translate"])-np.array(o2["translate"])
			#rot=np.array([[cos(rots[i2,1]/180*np.pi),0,sin(rots[i2,1]/180*np.pi)],[0,1,0],[-sin(rots[i2,1]/180*np.pi),0,cos(rots[i2,1]/180*np.pi)]])
			rotinv=np.array([[cos(-rots[i2,1]/180*np.pi),0,sin(-rots[i2,1]/180*np.pi)],[0,1,0],[-sin(-rots[i2,1]/180*np.pi),0,cos(-rots[i2,1]/180*np.pi)]])
			obj_binary_stat[(t1,t2)].append(rotinv.dot(reltrans).tolist()+(rots[i1]-rots[i2]).tolist())
			
def profile_level(level):
	origin=level["origin"]
	rooms=level["rooms"]
	for r in rooms:
		try:
			profile_room(r)
		except:
			continue
	return 

def loadjson(fname):
	with open(fname,"r") as inf:
		return json.load(inf)

level_files=os.listdir(levels_root)

cnt=0
for inf in level_files:
	cnt+=1
	if(cnt%100==0):
		print(cnt)
	profile_level(loadjson(os.path.join(levels_root,inf)))

joblib.dump(obj_binary_stat,"binrel.bin")


	


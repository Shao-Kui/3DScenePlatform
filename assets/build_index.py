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
reduce=functools.reduce
room_list=joblib.load("room_list.bin")
npix=50
kern_size=3
pcadata=[]

'''
for i in range(10000):
	roominfo=random.choice(room_list)
	if(i%10==0):
		print(i)
	geo=roominfo["contour"]
	geopoints=np.array(reduce(lambda x,y:x+y,geo))
	bbox={"min":geopoints.min(axis=0),"max":geopoints.max(axis=0)}
	center=(bbox["min"]+bbox["max"])*0.5
	pixscale=(bbox["max"]-bbox["min"]).max()/npix
	canvas=np.zeros((npix,npix))
	for g in geo:
		(rr,cc)=skimage.draw.polygon([(p[0]-center[0])/pixscale+npix*0.5 for p in g],[(p[1]-center[1])/pixscale+npix*0.5 for p in g],(npix,npix))
		canvas[(rr,cc)]=1.0-canvas[(rr,cc)]
	canvas=skimage.filters.gaussian(canvas,kern_size,mode="constant")
	canvas=skimage.transform.rotate(canvas,random.choice([0,90,180,270]))
	canvas=canvas.flatten()
	pcadata.append(canvas)
pca = sklearn.decomposition.PCA(n_components=50)
pca.fit(pcadata)
joblib.dump(pca,"pca.bin")
'''

pca=joblib.load("pca.bin")
feature=[]
meta=[]
for i in range(len(room_list)):
	room=room_list[i]
	if(i%10==0):
		print("%d of %d"%(i,len(room_list)))
	if(len(room["types"])!=1):
		continue
	rtype=room["types"][0]
	geo=room["contour"]
	geopoints=np.array(reduce(lambda x,y:x+y,geo))
	bbox={"min":geopoints.min(axis=0),"max":geopoints.max(axis=0)}
	center=(bbox["min"]+bbox["max"])*0.5
	pixscale=(bbox["max"]-bbox["min"]).max()/npix
	canvas=np.zeros((npix,npix))
	for g in geo:
		(rr,cc)=skimage.draw.polygon([(p[0]-center[0])/pixscale+npix*0.5 for p in g],[(p[1]-center[1])/pixscale+npix*0.5 for p in g],(npix,npix))
		canvas[(rr,cc)]=1.0-canvas[(rr,cc)]
	canvas=skimage.filters.gaussian(canvas,kern_size,mode="constant")
	canvasfeature=[skimage.transform.rotate(canvas,r).flatten() for r in [0,90,180,270]]
	canvasfeature=pca.transform(canvasfeature)
	feature.append(canvasfeature)
	canvasmeta=[{"type":rtype,"origin":room["origin"],"roomid":room["roomid"],"level":room["level"],"rotate":r,"area":np.prod(bbox["max"]-bbox["min"])} for r in [0,90,180,270]]
	meta.append(canvasmeta)

feature=np.concatenate(feature,axis=0)
meta=reduce(lambda x,y:x+y,meta)
rtypes=set([m["type"] for m in meta])

index={}
for rtype in rtypes:
	print(rtype)
	fter=[i for i in range(len(meta)) if meta[i]["type"]==rtype]
	fea=feature[fter]
	mt=[meta[i] for i in fter]
	nn=sklearn.neighbors.NearestNeighbors(n_neighbors=max(1,min(int(len(fter)/10),200)))
	nn.fit(fea)
	index[rtype]={"meta":mt,"feature":fea,"nn":nn}
joblib.dump(index,"auto_index.bin")

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
import itertools
import pyclipper
import matplotlib.path as mpltPath

with open("ModelCategoryMapping.csv","r") as mappingf:
	lines=map(lambda x:x.split(","),mappingf.read().split("\n"))
	coarsemappingdict={line[1]:line[3] for line in lines}
	finemappingdict={line[1]:line[2] for line in lines}

def loadjson(fname):
	with open(fname,"r") as inf:
		return json.load(inf)
suncg_root=os.path.join("..","suncg")
levels_root=os.path.join(".","test")

coarse_categories=sorted(list(set(coarsemappingdict.values())))
fine_categories=sorted(list(set(finemappingdict.values())))
ncoarse=len(coarse_categories)
nfine=len(fine_categories)
coarse_mapping={coarse_categories[i]:i for i in range(ncoarse)}
fine_mapping={fine_categories[i]:i for i in range(nfine)}

candidate_categories=list(range(ncoarse)) # Please find some categories that really work

binrel=joblib.load("binindex.bin")
cos=np.cos
sin=np.sin
reduce=functools.reduce
lfilter=lambda f,x:list(filter(f,x))
lmap=lambda f,x:list(map(f,x))

gmmscore_lo_thres=-20
gmmscore_hi_thres=100
priorscore_lo_thres=0
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
def loadroom(origin,level,roomid):
	level=loadjson("%s-l%d.json"%(origin,level))
	rooms=lfilter(lambda x:x["modelId"]==roomid,level["rooms"])
	return rooms[0]
def getroomcontour(origin,room):
	room_fname=os.path.join(suncg_root,"room",origin,room+"f.obj")
	if(not os.path.isfile(room_fname)):
		room_fname=os.path.join(os.path.split(housef)[0].replace(house_root,room_root),room["modelId"]+"c.obj")
	with open(room_fname,"r") as inf:
		lines=inf.read().split("\n")
		vertices_lines=lfilter(lambda x:x.startswith("v "),lines)
		vertices=np.array(lmap(lambda x:lmap(float,x.split()[1:]),vertices_lines))
		vys=vertices[:,1]
		vertices=vertices[:,[0,2]]
		faces_lines=lfilter(lambda x:x.startswith("f "),lines)
		faces=lmap(lambda x:lmap(lambda y:int(y.split("/")[0])-1,x.split()[1:]),faces_lines)
		paths=pyclipper.scale_to_clipper([vertices[faces[0]]])
		for face in faces:
			if(np.abs(area(vertices[face]))<1e-5):
				continue
			pc = pyclipper.Pyclipper()
			pc.AddPaths(paths,pyclipper.PT_SUBJECT, True)
			clipface=pyclipper.scale_to_clipper(vertices[face])
			pc.AddPath(clipface,pyclipper.PT_CLIP,True)
			paths=pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
		paths=pyclipper.scale_from_clipper(paths)
		ymin,ymax=np.min(vys),np.max(vys)
	return ((ymin,ymax),paths)
	
def find_category_and_rotate_given_placement(origin,level,roomid,objList,translate): # The first 3 parameters are not used here #refer to build_obj_index.py for the function
	objs=objList
	poss=np.array(lmap(lambda x:x["translate"],objs))
	rots=np.array(lmap(lambda x:x["rotate"],objs))
	dists=np.linalg.norm(np.array(translate)[np.newaxis,:]-poss,axis=1)
	
	# Please refer to build_obj_binrel.py
	i2s=np.argsort(dists)[1:int(min(5,2+len(objs)*0.25,len(objs)-1))]
	o2s=[objs[i2] for i2 in i2s]
	t2s=[coarse_mapping[coarsemappingdict[o2["modelId"]]] for o2 in o2s]
	reltranss=[translate-np.array(o2["translate"]) for o2 in o2s]
	rotinvs=[np.array([[cos(-rots[i2,1]/180*np.pi),0,sin(-rots[i2,1]/180*np.pi)],[0,1,0],[-sin(-rots[i2,1]/180*np.pi),0,cos(-rots[i2,1]/180*np.pi)]]) for i2 in i2s]
	
	relposs=[rotinv.dot(reltrans) for (rotinv,reltrans) in zip(rotinvs,reltranss)]
	
	scores=[]


	for t1 in candidate_categories: 
		print(coarse_categories[t1])
		rels=[binrel[(t1,t2)] if ((t1,t2) in binrel) else None for t2 in t2s]
		gmms=[rel["posmodel"] if (rel) else None for rel in rels ]
		gmmscores=np.array([gmm.score([relpos]) if gmm else gmmscore_lo_thres for (gmm,relpos) in zip(gmms,relposs)])
		gmmscores[gmmscores<gmmscore_lo_thres]=gmmscore_lo_thres
		gmmscores[gmmscores>gmmscore_hi_thres]=gmmscore_hi_thres
		priorscores=np.array([np.log(rel["nsample"]) if rel else priorscore_lo_thres for rel in rels])+0.01
		score_total=np.sum(gmmscores*priorscores)/np.sum(priorscores)+np.sum(priorscores)*0.1
		scores.append(score_total)
	
	t1=candidate_categories[np.argmax(scores)]
	
	#get rotation
	rotquant_candidate=np.array(list(itertools.product(range(8),range(8),range(8))))
	relrot_candidate=np.round(rots[i2s,np.newaxis,:]/(np.pi*0.25)).astype("int")-rotquant_candidate[np.newaxis,:,:]
	relrot_candidate[relrot_candidate<0]+=8
	relrot_candidate[relrot_candidate>8]-=8
	rels=[binrel[(t1,t2)] if ((t1,t2) in binrel) else None for t2 in t2s]
	gmms=[rel["posrotmodel"] if (rel) else None for rel in rels ]
	gmmscores=np.array([gmm.score_samples(np.concatenate([np.tile(relpos[np.newaxis,:],[512,1]),relrot],axis=1)) if gmm else None for (gmm,relrot,relpos) in zip(gmms,relrot_candidate,relposs)])
	gmmscores[gmmscores<gmmscore_lo_thres]=gmmscore_lo_thres
	gmmscores[gmmscores>gmmscore_hi_thres]=gmmscore_hi_thres
	priorscores=np.array([np.log(rel["nsample"]) if rel else priorscore_lo_thres for rel in rels])+0.01
	scores=(priorscores[:,np.newaxis]*gmmscores).sum(axis=0)
	return coarse_categories[t1],rotquant_candidate[np.argmax(scores)]*(np.pi*0.25)
	
def find_placement_and_rotate_given_category(origin,level,roomid,objList,category): # The level parameter is not used here
	objs=objList
	poss=np.array(lmap(lambda x:x["translate"],objs))
	rots=np.array(lmap(lambda x:x["rotate"],objs))
	
	((ymin,ymax),contour)=getroomcontour(origin,roomid)
	contour=np.array(contour[0])
	path = mpltPath.Path(contour)
	[xmin,zmin]=contour.min(axis=0)
	[xmax,zmax]=contour.max(axis=0)
	
	#refer to find_category_and_rotate_given_placement, modified for fast batch processing
	poss_candidate=np.array(list(itertools.product(np.linspace(xmin,xmax,20),[ymin],np.linspace(zmin,zmax,20))))
	poss_candidate=poss_candidate[path.contains_points(poss_candidate[:,[0,2]])] #candidate point in room
	dists=np.linalg.norm(poss_candidate[:,np.newaxis,:]-poss[np.newaxis,:,:],axis=2)
	
	
	t1=coarse_mapping[category]
	i2ss=[np.argsort(dists[i])[1:int(min(5,2+len(objs)*0.25,len(objs)-1))] for i in range(len(poss_candidate))]
	o2ss=[[objs[i2] for i2 in i2s] for i2s in i2ss]
	t2ss=[[coarse_mapping[coarsemappingdict[o2["modelId"]]] for o2 in o2s] for o2s in o2ss]
	reltransss=poss_candidate[:,np.newaxis,:]-poss[i2ss]
	rotinvss=[[np.array([[cos(-rots[i2,1]/180*np.pi),0,sin(-rots[i2,1]/180*np.pi)],[0,1,0],[-sin(-rots[i2,1]/180*np.pi),0,cos(-rots[i2,1]/180*np.pi)]]) for i2 in i2s]for i2s in i2ss]
	
	relposss=[[rotinv.dot(reltrans) for (rotinv,reltrans) in zip(rotinvs,reltranss)]for (rotinvs,reltranss) in zip(rotinvss,reltransss)]
	
	relss=[[binrel[(t1,t2)] if ((t1,t2) in binrel) else None for t2 in t2s] for t2s in t2ss]
	gmmss=[[rel["posmodel"] if (rel) else None for rel in rels ] for rels in relss]
	gmmscoress=np.array([[gmm.score([relpos]) if gmm else gmmscore_lo_thres for (gmm,relpos) in zip(gmms,relposs)] for (gmms,relposs) in zip(gmmss,relposss)])
	gmmscoress[gmmscoress<gmmscore_lo_thres]=gmmscore_lo_thres
	gmmscoress[gmmscoress>gmmscore_hi_thres]=gmmscore_hi_thres
	priorscoress=np.array([[np.log(rel["nsample"]) if rel else priorscore_lo_thres for rel in rels]for rels in relss])+0.01
	score_total=np.sum(gmmscoress*priorscoress,axis=1)/np.sum(priorscoress,axis=1)+np.sum(priorscoress,axis=1)*0.1
	
	sel=np.argmax(score_total)
	translate=poss_candidate[sel]
	relposs=relposss[sel]
	i2s=i2ss[sel]
	t2s=t2ss[sel]
	rotquant_candidate=np.array(list(itertools.product(range(8),range(8),range(8))))
	relrot_candidate=np.round(rots[i2s,np.newaxis,:]/(np.pi*0.25)).astype("int")-rotquant_candidate[np.newaxis,:,:]
	relrot_candidate[relrot_candidate<0]+=8
	relrot_candidate[relrot_candidate>8]-=8
	rels=[binrel[(t1,t2)] if ((t1,t2) in binrel) else None for t2 in t2s]
	gmms=[rel["posrotmodel"] if (rel) else None for rel in rels ]
	gmmscores=np.array([gmm.score_samples(np.concatenate([np.tile(relpos[np.newaxis,:],[512,1]),relrot],axis=1)) if gmm else None for (gmm,relrot,relpos) in zip(gmms,relrot_candidate,relposs)])
	gmmscores[gmmscores<gmmscore_lo_thres]=gmmscore_lo_thres
	gmmscores[gmmscores>gmmscore_hi_thres]=gmmscore_hi_thres
	priorscores=np.array([np.log(rel["nsample"]) if rel else priorscore_lo_thres for rel in rels])+0.01
	scores=(priorscores[:,np.newaxis]*gmmscores).sum(axis=0)
	return translate,rotquant_candidate[np.argmax(scores)]*(np.pi*0.25)
#build a case to test
testroom=loadroom('00e1559bdd1539323f3efba225af0531',0,'fr_0rm_0')
drop=random.choice(testroom["objList"])
testroom["objList"].remove(drop)
print((coarsemappingdict[drop["modelId"]],drop["translate"],drop["rotate"])) # The object dropped
print(find_category_and_rotate_given_placement('00e1559bdd1539323f3efba225af0531',0,'fr_0rm_0',testroom["objList"],drop["translate"]))
print(find_placement_and_rotate_given_category('00e1559bdd1539323f3efba225af0531',0,'fr_0rm_0',testroom["objList"],coarsemappingdict[drop["modelId"]]))

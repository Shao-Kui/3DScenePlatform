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
import pyclipper

suncg_root=os.path.join("..","suncg")
levels_root="test"
rooms_root="room"

lfilter=lambda f,x:list(filter(f,x))
lmap=lambda f,x:list(map(f,x))
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
def profile_room(origin,levelid,room):
	room_fname=os.path.join(suncg_root,"room",origin,room["modelId"]+"f.obj")
	if(not os.path.isfile(room_fname)):
		room_fname=os.path.join(os.path.split(housef)[0].replace(house_root,room_root),room["modelId"]+"c.obj")
	with open(room_fname,"r") as inf:
		lines=inf.read().split("\n")
		vertices_lines=lfilter(lambda x:x.startswith("v "),lines)
		vertices=np.array(lmap(lambda x:lmap(float,x.split()[1:]),vertices_lines))[:,[0,2]]
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
		
	return {"origin":origin,"roomid":room["modelId"],"level":levelid,"types":room["roomTypes"],"contour":paths}	
def profile_level(level):
	origin=level["origin"]
	rooms=level["rooms"]
	levelinfo=[]
	for r in rooms:
		try:
			levelinfo.append(profile_room(origin,level["id"],r))
		except:
			continue
	return levelinfo

def loadjson(fname):
	with open(fname,"r") as inf:
		return json.load(inf)

level_files=os.listdir(levels_root)
index=[]
for inf in level_files:
	print(inf)
	level=loadjson(os.path.join(levels_root,inf))
	index=index+profile_level(level)
joblib.dump(index,"room_list.bin")

	


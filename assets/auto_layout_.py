import flask
from flask import Flask
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
import matplotlib.path as mpltPath
import pyclipper
from flask_cors import CORS

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
CORS(app)


suncg_root=os.path.join("..","suncg")



cos=np.cos
sin=np.sin
reduce=functools.reduce
lfilter=lambda f,x:list(filter(f,x))
lmap=lambda f,x:list(map(f,x))

index=joblib.load("auto_index.bin")
pca=joblib.load("pca.bin")
roomtype_stat=sorted([len(index[key]["meta"]) for key in index.keys()])
roomtypes=[key for key in index.keys() if len(index[key]["meta"])>=roomtype_stat[-10] and key!="Garage" and key!="Room"]


npix=50
kern_size=3
pcadata=[]

door_objects=["122","133","214","246","247","326","327","331","73","756","757","758","759","760","761","762","763","764","768","769","770","s__1762","s__1763","s__1764","s__1765","s__1766","s__1767","s__1768","s__1769","s__1770","s__1771","s__1772","s__1773"]
window_objects=["126","209","210","211","212","213","752","753","754","755","766","767","s__1276","s__2010","s__2011","s__2012","s__2013","s__2014","s__2015","s__2016","s__2017","s__2019"]

def loadjson(fname):
	with open(fname,"r") as inf:
		return json.load(inf)
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

def find_candidates(geo,rtype):
	geopoints=np.array(reduce(lambda x,y:x+y,geo))
	bbox={"min":geopoints.min(axis=0),"max":geopoints.max(axis=0)}
	center=(bbox["min"]+bbox["max"])*0.5
	pixscale=(bbox["max"]-bbox["min"]).max()/npix
	canvas=np.zeros((npix,npix))
	for g in geo:
		(rr,cc)=skimage.draw.polygon([(p[0]-center[0])/pixscale+npix*0.5 for p in g],[(p[1]-center[1])/pixscale+npix*0.5 for p in g],(npix,npix))
		canvas[(rr,cc)]=1.0-canvas[(rr,cc)]
	canvas=skimage.filters.gaussian(canvas,kern_size,mode="constant")
	canvas=canvas.flatten()
	fea=pca.transform([canvas])
	dist,indi=index[rtype]["nn"].kneighbors(fea)
	area=np.prod(bbox["max"]-bbox["min"])
	dist,indi=index[rtype]["nn"].kneighbors(fea)
	areas=[index[rtype]["meta"][i]["area"] for i in indi[0]]
	picked=indi[0][np.argsort(np.abs(np.log(area/areas)))][0:20]
	return picked
def exec_transfer(geo,rtype,roomid):
	geopoints=np.array(reduce(lambda x,y:x+y,geo))
	bbox={"min":geopoints.min(axis=0),"max":geopoints.max(axis=0)}
	area=np.prod(bbox["max"]-bbox["min"])
	center=(bbox["max"]+bbox["min"])*0.5
	
	#room_template=json.loads(open(os.path.join("rooms",index[rtype]["meta"][roomid]["file"]),"r").read())
	origin=index[rtype]["meta"][roomid]["origin"]
	roomname=index[rtype]["meta"][roomid]["roomid"]
	level=index[rtype]["meta"][roomid]["level"]
	#pdb.set_trace()
	room_template=[r for r in loadjson(os.path.join("test","%s-l%s.json"%(origin,level)))["rooms"] if r["modelId"]==roomname][0]
	rotate=index[rtype]["meta"][roomid]["rotate"]
	
	((ymin_template,ymax_template),geopoints_template)=getroomcontour(origin,roomname)
	geopoints_template=np.array(reduce(lambda x,y:x+y,geopoints_template))
	bbox_template={"min":geopoints_template.min(axis=0),"max":geopoints_template.max(axis=0)}	
	center_template=(bbox_template["max"]+bbox_template["min"])*0.5
	
	
	scale=(area/index[rtype]["meta"][roomid]["area"])**0.5
	
	
	for obj in room_template["objList"]:
		rx,ry,rz=obj["rotate"]
		ry+=rotate/180*np.pi

		translate=np.array([[cos(rotate/180*np.pi),0,sin(rotate/180*np.pi)],[0,1,0],[-sin(rotate/180*np.pi),0,cos(rotate/180*np.pi)]]).dot(np.array(obj["translate"])-[center_template[0],ymin_template,center_template[1]])+[center[0],0,center[1]]

		obj["translate"]=translate.tolist()
	room_template["roomTypes"]=[rtype]
	room_template["contour"]=geo
	return room_template
def rate_transferred(room):
	#obj in room
	
	paths=pyclipper.scale_to_clipper(room["contour"])
	objpos=pyclipper.scale_to_clipper([[o["translate"][0],o["translate"][2]] for o in room["objList"]])
	
	tolerance=((np.array(paths).max(axis=1)-np.array(paths).min(axis=1)).min()*0.01).astype("int")
	pco = pyclipper.PyclipperOffset()
	pco.AddPaths(paths, pyclipper.JT_SQUARE, pyclipper.ET_CLOSEDPOLYGON)
	offsetpath = pco.Execute(tolerance)
	
	flags=[any([pyclipper.PointInPolygon(pos,path) for path in offsetpath]) for pos in objpos]
	score=np.log(np.std(np.array(objpos),axis=0)+0.000001).sum()+np.mean(flags)*10
	return score
def transfer(geo,rtype,seed=0):
	#extract geo feature
	candidates=find_candidates(geo,rtype)
	transferred=[exec_transfer(geo,rtype,i) for i in candidates]
	rates=[(r,rate_transferred(r)) for r in transferred]
	rs=np.random.RandomState(seed)
	probs=np.array([r[1] for r in rates])
	probs-=probs.mean()
	probs=np.exp(probs*2)
	probs/=probs.sum()
	return rates[rs.choice(np.arange(len(rates)),p=probs)][0]
'''
def generate_():
	data={'roomtype': 'Bathroom', 'origin': '00e1559bdd1539323f3efba225af0531', 'roomid': 'fr_0rm_1'}
	#data=json.loads(flask.request.data)["body"]
	((ymin,ymax),contour_to_transfer)=getroomcontour(data["origin"],data["roomid"])
	ret=transfer(contour_to_transfer,data["roomtype"],int(data["seed"]) if "seed" in data else 0)
	for obj in ret["objList"]:
		obj["translate"][1]+=ymin
	print(data,ret["objList"])
	return json.dumps(ret["objList"])	

generate_()
'''
@app.route("/generate", methods=['GET', 'POST'])
def generate():
	#data={'roomtype': 'Living_Room', 'origin': '00e1559bdd1539323f3efba225af0531', 'roomid': 'fr_0rm_0'}
	data=json.loads(flask.request.data)["body"]
	((ymin,ymax),contour_to_transfer)=getroomcontour(data["origin"],data["roomid"])
	ret=transfer(contour_to_transfer,data["roomtype"],int(data["seed"]) if "seed" in data else 0)
	for obj in ret["objList"]:
		obj["translate"][1]+=ymin
	print(data,ret["objList"])
	return json.dumps(ret["objList"])
app.run(host="0.0.0.0",port=11426,debug=True)


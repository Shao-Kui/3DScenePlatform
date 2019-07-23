import os
import json
import pdb
import sqlite3
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import ForeignKey
from nltk.corpus import wordnet
from sqlalchemy.orm import backref


engine = create_engine('sqlite:///database.db', echo=True)
Session = sessionmaker(bind=engine)

Base = declarative_base()

class Category(Base):
	__tablename__ = 'Categories'
	id=Column(Integer, primary_key=True)
	wordnetSynset=Column(String)
	name=Column(String)
	keywords=relationship("Keyword",back_populates="category")
	parent_id = Column(Integer, ForeignKey(id))
	children = relationship(
		"Category",
		cascade="all, delete-orphan",
		backref=backref("parent", remote_side=id))
	models=relationship("Model3D",back_populates="category")
	
	def __init__(self, wordnetSynset,name, keywords,parent=None):
		self.wordnetSynset=wordnetSynset
		self.name = name
		self.parent = parent
		self.keywords = [Keyword(w,self) for w in keywords]
		self.models=[]


class Keyword(Base):
	__tablename__ = 'Keywords'
	id=Column(Integer, primary_key=True)
	keyword=Column(String)
	category_id = Column(Integer, ForeignKey('Categories.id'))
	category=relationship("Category",back_populates="keywords")
	def __init__(self,keyword,category):
		self.category=category
		self.keyword=keyword

class Model3D(Base):
	__tablename__ = 'Model3Ds'
	id=Column(Integer, primary_key=True)
	category_id=Column(Integer, ForeignKey('Categories.id'))
	category=relationship("Category",back_populates="models")
	name=Column(String)
	format=Column(String)
	resources=Column(String)
	meta=Column(String)
	
	def __init__(self,name,format,resources,meta):
		self.name=name
		self.format=format
		self.resources=resources
		self.meta=meta
Base.metadata.create_all(engine)

with open("categories.txt","r") as inf:
	obj_categories=[line.split("\t") for line in inf]
fine_dict={}
for line in obj_categories:
	name=line[2]
	if(not name in fine_dict):
		fine_dict[name]={"synsets":[]}
	dct=fine_dict[name]
	if(line[6]!="-" and not [x for x in dct["synsets"] if x["name"]==line[6]]):
		dct["synsets"].append({"name":line[6]})

wndict={}
categoryitems=[]
def wordnetregister(synsetid):
	if(synsetid in wndict):
		return wndict[synsetid]
	wnsynset=wordnet.synset_from_pos_and_offset('n',synsetid)
	if not(wnsynset.name()):
		pdb.set_trace()
	if(wnsynset.hypernyms()):
		wndict[synsetid]=Category(str(wnsynset.offset()),wnsynset.name(),wnsynset.lemma_names(),wordnetregister(wnsynset.hypernyms()[0].offset()))
	else:
		wndict[synsetid]=Category(str(wnsynset.offset()),wnsynset.name(),wnsynset.lemma_names(),None)
	return wndict[synsetid]
for cls in fine_dict:
	for synset in fine_dict[cls]["synsets"]:
		wnsynsetid=int(synset["name"][1:])
		item=Category(cls,None,[cls],wordnetregister(wnsynsetid))
		synset["item"]=item
		categoryitems.append(item)
for line in obj_categories:
	obj=line[1]
	name=line[2]
	dct=fine_dict[name]
	if(line[6]!="-"):
		item=[i for i in dct["synsets"] if i["name"]==line[6]][0]["item"]
		item.models.append(Model3D(
			obj,
			"OBJ",
			json.dumps({"mesh":os.path.join(".","suncg","object",obj,"%s.obj"%obj),"mtl":os.path.join(".","suncg","object",obj,"%s.mtl"%obj),"texture":os.path.join(".","suncg","texture")}),
			json.dumps({})
		))
session = Session()
session.add_all([v for v in wndict.values()]+categoryitems)
session.commit()

'''
with open("categories.txt","r") as inf:
	obj_categories=[line.split("\t") for line in inf]

Base.metadata.create_all(engine)
coarse_dict={}
for line in obj_categories:
	name=line[3]
	if(not name in coarse_dict):
		coarse_dict[name]={"synsets":[]}
	dct=coarse_dict[name]
	if(line[6]!="-"):
		dct["synsets"].append(line[6])
for cls in coarse_dict:
	synsets=list(set(coarse_dict[cls]["synsets"]))
	if(len(synsets)==0):
		coarse_dict[cls]=CoarseObjClass(name=cls,wordnetSynset="",keywords=cls.replace("_"," "))
		continue
	synsets=[wordnet.synset_from_pos_and_offset('n',int(i[1:])) for i in synsets]
	common_hypernyms=functools.reduce(lambda x,y:x.lowest_common_hypernyms(y)[0],synsets)
	coarse_dict[cls]=CoarseObjClass(name=cls,wordnetSynset="%s%08d"%(common_hypernyms.pos(),common_hypernyms.offset()),keywords="|".join(map(lambda x:x.replace("_"," "),common_hypernyms.lemma_names())))
session = Session()
session.add_all([v for v in coarse_dict.values()])
session.commit()

fine_dict={}
for line in obj_categories:
	name=line[2]
	if(not name in fine_dict):
		fine_dict[name]={"synsets":[],"coarse_id":-1}
	dct=fine_dict[name]
	dct["coarse_id"]=coarse_dict[line[3]].id
	if(line[6]!="-"):
		dct["synsets"].append(line[6])

for cls in fine_dict:
	synsets=list(set(fine_dict[cls]["synsets"]))
	if(len(synsets)==0):
		fine_dict[cls]=FineObjClass(name=cls,wordnetSynset="",keywords=cls.replace("_"," "),coarse_id=fine_dict[cls]["coarse_id"])
		continue
	synsets=[wordnet.synset_from_pos_and_offset('n',int(i[1:])) for i in synsets]
	synset=synsets[0]
	fine_dict[cls]=FineObjClass(name=cls,wordnetSynset="%s%08d"%(synset.pos(),synset.offset()),keywords="|".join(map(lambda x:x.replace("_"," "),synset.lemma_names())),coarse_id=fine_dict[cls]["coarse_id"])
session.add_all([v for v in fine_dict.values()])
session.commit()
'''
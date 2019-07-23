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


def query_models(keyword,rg):
	session=Session()
	keywords=session.query(Keyword).filter(Keyword.keyword.like(keyword)).all()
	categories=[]
	categories_this=[k.category for k in keywords]
	while(categories_this):
		categories_next=session.query(Category).filter(Category.parent_id.in_(tuple([k.id for k in categories_this]))).all()
		categories=categories+categories_this
		categories_this=categories_next
	models=session.query(Model3D).filter(Model3D.category_id.in_(tuple([k.id for k in categories]))).slice(rg[0],rg[1]).all()
	return models

def query_model_by_id(id):
	session=Session()
	return session.query(Model3D).filter(Model3D.id==id).first()

def query_model_by_name(name):
	session=Session()
	return session.query(Model3D).filter(Model3D.name==name).first()
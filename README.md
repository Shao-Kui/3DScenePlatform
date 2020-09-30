# Introduction
This is the repository of the paper ``Geometry-Based Layout Generation with Hyper-Relations AMONG Objects". Our platform is web-based. 

We assume developers and researchers would first deploy this platform. The [manuals](#Manuals) are available in the latter of this doc if you wish to directly use a ready clone. 

# Requirements
Requirements are mainly for running the back-end including the algorithm. Dependencies at front-end are already included, but Chrome is still recommended. The server is easily run by "python main.py", if the following requirements are satisfied:  
numpy  
PyTorch  

# Datasets
This section discuss how we organize datasets. Note that we have no copyright to distribute datasets, especially SUNCG. 3D-Front is available, please refer to their [website][3dfront] for downloading.  
## Models
Since models are reuseble in multiple scenes. The repository of models be separated from the repo of scenes. Please organize models in the ```object``` folder of the ```dataset``` folder:  
<pre>
root
|  main.py
|  otherpythonfiles.py
|  ...
|  dataset
|    room
|    <b>object</b>
|    |  objname1
|    |    <b>objname1.obj</b>
|    |    <b>objname1.mtl</b>
|    |    rendered_images
|    |  objname2
|    |  objname3
|    |  ...
|    texture
|  latentspace
|  static
|  ...
</pre>
Each obj-folder in ```object``` belongs to a single 3D model, e.g., a chair or a table. Each obj-folder in ```object``` has a **unique** name or id that exclusively refers to this model, e.g., `objectname1`. Currently, our platform supports only `wavefront .obj files`, so each obj-folder includes at least a .obj file and a .mtl file, e.g., 'modelname1.obj' and 'modelname1.mtl' in 'modelname1'.  

Note that textures are also reusable by another ```texture``` folder in ```dataset```. Links of textures are url with respect to the server, e.g.,  
```
../texture/wood_1.jpg
```

## Priors
Priors are origanized in ... ... ...
## Layout Configuration
A 'layout-config' file is a json including essential attributes of a scene. The stucture of a config file is presented below: 
```
origin
bbox:{
  min
  max
}
up
front
rooms:[
  room1:{
  |  id
  |  modelId
  |  roomTypes:[...]
  |  bbox:{
  |    min
  |    max
  |  }
  |  roomId
  |  objList:[
  |    object1:{
  |    |  id
  |    |  type
  |    |  modelId
  |    |  bbox
  |    |  translate
  |    |  scale
  |    |  rotate
  |    |  rotateOrder
  |    |  orient
  |    |  coarseSemantic
  |    |  roomId
  |    |  inDatabase
  |    },
  |    object2:{...},
  |    object3:{...},
  |    ...
  |  ]
  },
  room2:{...},
  room3:{...},
  ...
]
```

# Layout Framework
Our layout framework is mainly included in the following files:
```
root
  autolayout.py
  relayout.py
  patternChain.py
  alutil.py
  projection2d.py
```
# Manuals  
**MouseClick-Left**:  
**MouseClick-Right**:  
**↑**:  
**↓**:  
**←**:  
**→**:  

[3dfront]:https://pages.tmall.com/wow/cab/tianchi/promotion/alibaba-3d-scene-dataset

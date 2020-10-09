# Introduction
Platform Overview             |  Viewing & Roaming
:-------------------------:|:-------------------------:
![Overview](http://cg.cs.tsinghua.edu.cn/course/vis/Shao-Kui/3dscenesys/1.png "Platform Overview")  |  ![Viewing](http://cg.cs.tsinghua.edu.cn/course/vis/Shao-Kui/3dscenesys/2.png "Viewing & Roaming")

Manipulating             |  Rendering
:-------------------------:|:-------------------------:
![Manipulating](http://cg.cs.tsinghua.edu.cn/course/vis/Shao-Kui/3dscenesys/4.png "Manipulating")  |  ![Rendering](http://cg.cs.tsinghua.edu.cn/course/vis/Shao-Kui/3dscenesys/5.png "Rendering")

This is the repository of the paper "Geometry-Based Layout Generation with Hyper-Relations AMONG Objects". Our platform is web-based. We hope this repository could help researches on 3D scenes and reproducing our framework. Our group is small. This repo may potentially contain enginneering bugs and this doc may not cover all your confusions. Please do issue us if you have problems with this repo. 

We assume developers and researchers would first deploy this platform. The [manuals](#Manuals) are available in the latter of this doc if you wish to directly use a ready clone. 

# Requirements
Requirements are mainly for running the back-end including the algorithm. Dependencies at front-end are already included, but Chrome is still recommended. The server is easily run by ```python main.py```, if the following requirements are satisfied:  
```
numpy==1.17.2
SQLAlchemy==1.2.13
Flask_Cors==3.0.7
trimesh==3.7.14
Shapely==1.7.0
torch==1.2.0+cu92
Flask==1.0.2
scipy==1.0.1
joblib==0.12.5
nltk==3.4.1
pyclipper==1.1.0.post1
matplotlib==2.2.2
Pillow==7.2.0
scikit_learn==0.23.2
```  
This platform is under cooperations with other organizations, so other packages may be required, e.g., ```baidu_aip```, ```librosa```, etc. Such features are not mandatory. Thus, you can simply `comment` the unnecessary packages. Note that for running the server, especially the algorithm, some packages are mandatory such as ```torch```, ```flask```, etc. We still recommend you installing the entire 'requirements.txt' on the safe side. To install packages, you needn't strictly match the versions above, those versions work for our deployment. Please issue us if you have troubles of deploying. 

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
  |  modelId
  |  roomTypes:[...]
  |  bbox:{
  |    min
  |    max
  |  }
  |  roomId
  |  objList:[
  |    object1:{
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
In sum, each config contains a list of rooms and a room contains a list of objects. Each config file has an ```origin``` denoting where it derives from, since our platform has it own supported data structure. For instance, in 3D-Front, it could be ```ffca6fce-0adb-48e4-be68-17343d6efffd```. A ```bbox``` denotes AABB bounding box of an entire layout, a room or an object. ```up``` and ```front``` are used by the perspective camera denoting 'up vector' and 'camera direction', which is typically '[0,1,0]' and '[0,0,1]'.  

Each room optionally has a ```roomTypes```, e.g., '['living room', 'kitchen']'. A 'modelId' of a room indexes to its ceiling, floor and wall. In this platform, similar to SUNCG, we split a room mesh into a ceiling, a floor and a wall. For example, a room with ```modelId: KidsRoom-1704``` has a 'KidsRoom-1704c.obj', 'KidsRoom-1704f.obj' and a 'KidsRoom-1704w.obj' in the 'root/dataset/room/{```origin```}/' directory. This simply separate room meshes with objects and separate floors, ceilling and walls, which is a enginneering and design decision for researches on scene synthesis or layout generation. If this separation is not necessary in your reasearch, you can simply ignore this attribute and take all meshes as 'objects' in ```objList```. ```roomId``` is necessary in our platform. It is the index of this room in ```rooms``` list of a config file. This attribute is used for fast indexing rooms and objects. Similarly each object also has a ```roomId``` denoting its room. 

Each object must has a ```modelId``` indexing its mesh in directory 'root/dataset/object/{```modelId```}'. ```translate```, ```scale``` and ```rotate``` are also mandatory. They are all lists with 3 element, e.g., ```"rotate": [0.0,-0.593,0.0],```. ```type``` is optional, we use this attribute to separate ordinary objects, windows, doors, etc. ```rotateOrder``` is typically 'XYZ' in our platform, but we allow custom rotating orders. ```coarseSemantic``` is optional if you would label objects, e.g., 'armchair'. 
# Layout Framework
Our layout framework in the paper "Geometry-Based Layout Generation with Hyper-Relations AMONG Objects" is included in the following files: 
```
root
  autolayout.py
  patternChain.py
  alutil.py
  relayout.py
  projection2d.py
```
**autolayout.py**: coherent grouping, prior loading, prior caching, setting up and bounding box generating, etc;  
**patternChain.py**: the code to dynamically check and generate hyper-relations;  
**alutil.py** and **relayout.py**: geometric arranging;  
**projection2d.py**: converting room meshes to polygons (room shape);  
# Manuals  
Our platform is split into two panel: operation & 3D scene. In operation panel, we allow rendering, layouting, saving, loading scenes. We also allow searching objects by semantics and names(id). One could add more objects by left clicking a searched result and left clicking a position in a scene. 3D scene panel uses an orbital controller, where interactions follows:  
**MouseClick-Left**: Left-click has multiple behaviors in this platform. If clicking an objects in the scene, a 'revolver' is shown waiting for further operations, such as transition(XoZ), transition(Y), rotation, deletion, etc. After clicking a button such as 'transition(XoZ)', the selected object moves following the mouse cursor. By another left-click, object is fixed at the user-wanted position and this routin is finished.  
**MouseClick-RightHold**: Right click and hold in the scene results in transiting the perspective camera.  
**↑**: Camera moving up;  
**↓**: Camera moving down;  
**←**: Camera moving left;  
**→**: Camera moving right;  
# Future works
[3dfront]:https://pages.tmall.com/wow/cab/tianchi/promotion/alibaba-3d-scene-dataset

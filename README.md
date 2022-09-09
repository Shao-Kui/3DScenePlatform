# Introduction
Platform Overview             |  Viewing & Roaming
:-------------------------:|:-------------------------:
![Overview](http://cg.cs.tsinghua.edu.cn/course/vis/Shao-Kui/3dscenesys/PlatformOverview.png "Platform Overview")  |  ![Viewing](http://cg.cs.tsinghua.edu.cn/course/vis/Shao-Kui/3dscenesys/viewing2.png "Viewing & Roaming")

Manipulating             |  Synthesis
:-------------------------:|:-------------------------:
![Manipulating](http://cg.cs.tsinghua.edu.cn/course/vis/Shao-Kui/3dscenesys/manipulating.png "Manipulating & Searching")  |  ![Synthesis](http://cg.cs.tsinghua.edu.cn/course/vis/Shao-Kui/3dscenesys/algorithm.png "Synthesis")

This is the repository of the paper "**MageAdd: Real-Time Interaction Simulation for Scene Synthesis**" and "**Geometry-Based Layout Generation with Hyper-Relations AMONG Objects**". Our platform is web-based. We hope this repository could help researches on 3D scenes and reproducing our framework. Because our group is small, this repo may potentially contain enginneering bugs and this doc may not cover all your confusions. Please do issue us if you have problems with this repo or e-mails us by zhangsk18@mails.tsinghua.edu.cn. 

We assume developers and researchers would first deploy this platform. The [manuals](#Manuals) are available in the latter of this doc if you wish to directly use a ready clone. 

This platform is **NOT** aimming at photo-realistic illumination, though we are continously improving the rendering. Instead, we provide an interactive environment for visualizing and debugging algorithms or frameworks related to 3D scenes. 

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
This platform is under cooperations with other organizations, so other packages may be required, e.g., ```baidu_aip```, ```librosa```, etc. Such features are not mandatory. Thus, you can simply `comment` the unnecessary packages. Note that for running the server, especially the algorithm, some packages are mandatory such as ```torch```, ```flask```, etc. We still recommend you installing the entire 'requirements.txt' on the safe side. To install packages, you needn't strictly match the versions above. We attached those versions simply because they work for our deployment. Please issue us if you have troubles of deploying. 

# Datasets
This section discusses how we organize datasets. This platform follows **S**hao**K**ui-Format, the Scalable and Kross-Platform Format. Note that we have no copyright to distribute datasets, especially SUNCG. 3D-Front is available, please refer to their [website][3dfront] for downloading. Our platform has its own organizations of datasets, so the downloaded datasets should be re-organized to 'root/dataset'. A [script][3dfront2suncg] exists for converting 3D-Front to SK-Format. The below paragraphs also illustrate our format in detail. 

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
In 3D-Front, we currently have found only geometries and textures of 3D objects, i.e., '.obj' and '.png'. Mateirals, i.e., '.mtl' files are automatically generated by our scripts. 

## Priors
Priors are organized in 'root/latentspace/pos-orient-3/'. In this directory, each .json file with a single object name contains pairwise priors for this object as a dominate object. For example, a .json file named '1435.json' contain priors for the dominate object named 1435, where several attributes exist such as '2497' and '2356' which are secondary objects related to the dominate objects. Thus, using two names of a dominate object and a secondary obejct index to a list of priors. Our priors are discrete as discussed in our paper. An item in a prior list (set) between two objects has four values: X, Y, Z, theta. The former three values are transitions and the fourth one is rotation of Y-axis. Though our platform support different rotating orders in engineering, but our layout framework ONLY support the 'XYZ' rotation. 

In the same directory, each .json file with two object names is a prior set of a pattern chain. Each pattern chain file is a list of another list. The 'outer' list has a number of chains and the 'inner' list includes indices to the source pairwise relations. Hpyer-Priors are organized in 'root/latentspace/pos-orient-3/hyper'. Similaly, the 'outer' list has a number of hyper-priors, but the 'inner' one is a dict object indexing to different source pairwise relations. Note that hyper-relations are generated online when our framework requires. 

The pre-learnt priors can be downloaded in [Tsinghua-Cloud][thucpriorlink] or [Google-Drive][googlepriorlink]. 

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
In sum, each config contains a list of rooms and a room contains a list of objects. Each config file has an ```origin``` denoting where it derives from, since our platform has it own supported data structure. For instance, in 3D-Front, it could be ```ffca6fce-0adb-48e4-be68-17343d6efffd```. A ```bbox``` denotes AABB bounding box of an entire layout, a room or an object. Although ```bbox``` is optional, it is still useful if users wish to [automatic calibrate the camera][#manuals]. ```up``` and ```front``` are used by the perspective camera denoting 'up vector' and 'camera direction', which is typically '[0,1,0]' and '[0,0,1]'.  

Each room optionally has a ```roomTypes```, e.g., '['living room', 'kitchen']'. A 'modelId' of a room indexes to its ceiling, floor and wall. In this platform, similar to SUNCG, we split a room mesh into a ceiling, a floor and a wall. For example, a room with ```modelId: KidsRoom-1704``` has a 'KidsRoom-1704c.obj', 'KidsRoom-1704f.obj' and a 'KidsRoom-1704w.obj' in the 'root/dataset/room/{```origin```}/' directory. This simply separate room meshes with objects and separate floors, ceilling and walls, which is a enginneering and design decision for researches on scene synthesis or layout generation. If this separation is not necessary in your reasearch, you can simply ignore this attribute and take all meshes as 'objects' in ```objList```. ```roomId``` is necessary in our platform. It is the index of this room in ```rooms``` list of a config file. This attribute is used for fast indexing rooms and objects. Similarly each object also has a ```roomId``` denoting its room. 

Each object must has a ```modelId``` indexing its mesh in directory 'root/dataset/object/{```modelId```}'. ```translate```, ```scale``` and ```rotate``` are also mandatory. They are all lists with 3 element, e.g., ```"rotate": [0.0,-0.593,0.0],```. ```type``` is optional, we use this attribute to separate ordinary objects, windows, doors, etc. ```rotateOrder``` is typically 'XYZ' in our platform, but we allow custom rotating orders. ```coarseSemantic``` is optional if you would label objects, e.g., 'armchair'. 

# Layout Framework

![GBA](http://cg.cs.tsinghua.edu.cn/course/vis/Shao-Kui/gba.png "Graphical Models")

[\[Paper\]][graphicalmodels] [\[Pre\]][gbaPre] [\[Supp\]][graphicalmodels]

Our layout framework in the paper "Geometry-Based Layout Generation with Hyper-Relations AMONG Objects" is included in the following files: 
```
root/
--autolayoutv2.py
--patternChainv2.py
--projection2d.py
--layoutmethods/
----alutil.py
----relayout.py
```
**autolayoutv2.py**: coherent grouping, prior loading, prior caching and bounding box generating, etc;  
**patternChainv2.py**: the code to dynamically check and generate hyper-relations;  
**alutil.py** and **relayout.py**: geometric arranging;  
**projection2d.py**: converting room meshes to polygons (room shape); 

If all dependencies are satisfied, our layout method can be run by clicking the **layout1** button in the front-end GUI. Note that you have to select a room first. The 'autolayout.py' and 'patternChain.py' are also usable, but only for SUNCG dataset. The 'v2' version of our method is specifically for 3D-Front. 

Our layout framework is accepted as an oral presentation in [Computational Visual Media 2021][cvm2021], and is publicated in [Graphical Models][gmod]. Please cite our paper if this repository helps! 
```
@article{ZHANG2021101104,
title = {Geometry-Based Layout Generation with Hyper-Relations AMONG Objects},
journal = {Graphical Models},
volume = {116},
pages = {101104},
year = {2021},
issn = {1524-0703},
doi = {https://doi.org/10.1016/j.gmod.2021.101104},
url = {https://www.sciencedirect.com/science/article/pii/S1524070321000096},
author = {Shao-Kui Zhang and Wei-Yu Xie and Song-Hai Zhang}
}
```
# MageAdd

![MageAdd](http://cg.cs.tsinghua.edu.cn/course/vis/Shao-Kui/teasermm.png "ACM MM 2021 Oral")

[\[Paper\]][mageaddPaper] [\[Video\]][mageaddVideo] [\[Supp\]][mageaddSupp]

This project is also the container for MageAdd, which is a interactive modelling tool for 3D scene synthesis. The source code of the MageAdd is included in the following files:
```
root/
--main_magic.py
--static/
----js/
------MageAdd.js
```
The .py file corrsponds to the **Piror Update** and the .js file contains the main logic of inference of MageAdd. The front-end dependencies are already included in the index.html. Please first install the back-end dependencies in the back-end (main_magic.py). 

Our paper is accepted as an oral presentation in [ACM MM 2021][acmmm2021]. Please cite our paper if this repository helps! 
```
@inproceedings{shaokui2021mageadd,
  title={MageAdd: Real-Time Interaction Simulation for Scene Synthesis},
  author={Zhang, Shao-Kui and Li, Yi-Xiao and He, Yu and Yang Yong-Liang and Zhang Song-Hai},
  booktitle={Proceedings of the 29th ACM International Conference on Multimedia, October 20--24, 2021, Virtual Event, China},
  year={2021},
  doi={10.1145/3474085.3475194}
}
```
# SceneViewer
![SceneViewer](http://cg.cs.tsinghua.edu.cn/course/vis/Shao-Kui/OPPNTPP.png "OPPNTPP")

\[Paper\] \[Video\] \[Supp\] (Coming Soon)

This project is also the container for our work on Photography in 3D residential scenes. The related source code includes:
```
root/
--autoview.py
--sceneviewer/
----constraints.py
----inset.py
----utils.py
----views.py
```
The "autoview.py" contains the fundamental logics of our method, which will call functions for deriving probe views and use constraints for evaluating views. It also organizes the generated views and renders the views. One could consider it as a controller. The "views.py" contains how we generate probe views based on one-point perspective and two-point perspective. The "constraints.py" contains the measurements, i.e., the content constraints and aesthetic constraints. The "utiles.py" contrains several functions for geometrical computing. Finally, "inset.py" contains the "mapping" algorithm proposed in the paper. 
# Manuals  
Our platform is split into two panel: operation & 3D scene. In operation panel, we allow rendering, layouting, saving, loading scenes. We also allow searching objects by semantics and names(id). One could add more objects by left clicking a searched result and left clicking a position in a scene. 3D scene panel uses an orbital controller, where interactions follows:  
**Axis**: The `Axis` button display/hide the world axis (Red: X, Blue: Z, Green, Y);   
**MouseClick-Left**: Left-click has multiple behaviors in this platform. If clicking an objects in the scene, a 'revolver' is shown waiting for further operations, such as transition(XoZ), transition(Y), rotation, deletion, etc. After clicking a button such as 'transition(XoZ)', the selected object moves following the mouse cursor. By another left-click, object is fixed at the user-wanted position and this routin is finished. If clicking a room, the platform with take the room as the current operational room, e.g., layout.  
**ScenePanel**: The scene panel on the left shows meta-data of current scenes, rooms and objects, e.g., room types, object categories.  
**MouseClick-LeftHold**: Left click and rotate the perspective camera for various views. The rotation (eulerangles) supports 'pitch' and 'yaw'.  
**MouseClick-RightHold**: Right click and hold in the scene results in transiting the perspective camera.  
**Space**: Automatically align the camera with respect to the selected room, and adjust the height of the camera.  
**Mouse Wheel**: Zoom In & Zoom Out.  
**↑**: Camera moving up;  
**↓**: Camera moving down;  
**←**: Camera moving left;  
**→**: Camera moving right;  
**Q**: Anti-clockwisely rotating 'yaw' of the perspective camera;  
**E**: Clockwisely rotating 'yaw' of the perspective camera;  
**C**: Disable/Enable the orbital controller. This is very useful if you wish to freeze your view, transform several objects and render, instead of mistakenly tuning views; 
**R**: Shortcut for Rendering;   

# Future works
We will improve the rendering in the future. We do have tried libraries of [Three.js][threejsweb] and several related 3rd-party repositories. Yet, better effects are still not generated. We will continue investigating this to figure out whether we got enginneering problems or we need resort to global rendering in the back-end. We will be extremely grateful if you have better ideas of improving rendering! We will also swap to a production WSGI server at the back-end. 

This repo will also be continuously updated, with more functions, features and open-source researches. We also welcome more collaborators, especially if you want to merge your algorithms or functionalities. 

## Known Problems or Bugs

* The `click` event of the scene canvas may be defunct of unknown reasons. 
* The navigation of mini-map (Bottom-Left) is defunct currently. 

# Acknowledgement
This platform is designed, structured and implemented by [Shao-Kui Zhang][shaokui](zhangsk18@mails.tsinghua.edu.cn), [Song-Hai Zhang][songhai] and Yuan Liang. Wei-Yu Xie is involved for voice-based model retrieval, room mesh processing and object recommendation using latent space (TBD). Yi-Ke Li and Yu-Fei Yang is involved for the Unity-based client for VR. Tian-Xing Xu is involved for the format conversion of 3D-Front. Xiang-Li Li is involved for sketch searching, refining datasets and dataset converting. 

Our layout framework is designed and implemented by [Shao-Kui Zhang][shaokui], Wei-Yu Xie and Song-Hai Zhang. We also appreciate Kai Wang for the experiment. 

The MageAdd is designed, implemented and publicated by [Shao-Kui Zhang][shaokui], Yi-Xiao Li, Yu He, [Yong-Liang Yang][yongliang], Song-Hai Zhang. 
# Copyright
This platform is developed for researches, though our license follows [GNU GPL 3.0][GNUGPL3]. The back-end is NOT security guaranteed if you have sensitive or private data, which is significant if you wish to deploy this platform publicly. 

[3dfront]:https://pages.tmall.com/wow/cab/tianchi/promotion/alibaba-3d-scene-dataset
[threejsweb]:https://threejs.org/
[shaokui]:https://shao-kui.github.io/
[songhai]:https://www.cs.tsinghua.edu.cn/info/1117/3538.htm
[GNUGPL3]:http://www.gnu.org/licenses/gpl-3.0.html
[cvm2021]:http://iccvm.org/2021/
[gmod]:https://www.journals.elsevier.com/graphical-models
[thucpriorlink]:https://cloud.tsinghua.edu.cn/f/36a3e973fe014bd89fcf/
[googlepriorlink]:https://drive.google.com/drive/folders/15WBBqGS79C9nG8m_41Bn43rzv3Cxb4xH?usp=sharing
[3dfront2suncg]:https://github.com/Shao-Kui/3DScenePlatform/blob/master/assets/3dfuture2suncg.py
[graphicalmodels]:https://cg.cs.tsinghua.edu.cn/course/vis/Shao-Kui/GBA.pdf
[mageaddPaper]:https://cg.cs.tsinghua.edu.cn/course/vis/Shao-Kui/MageAdd.pdf
[mageaddVideo]:https://www.bilibili.com/video/BV1JP4y1x78p/
[mageaddSupp]:https://cg.cs.tsinghua.edu.cn/course/vis/Shao-Kui/DocMageAdd.pdf
[gbaPre]:https://www.bilibili.com/video/BV1FU4y1a7A1/
[acmmm2021]:https://2021.acmmm.org/
[yongliang]:http://yongliangyang.net/

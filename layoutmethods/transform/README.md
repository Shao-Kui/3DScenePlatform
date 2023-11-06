#### 结构

当前项目结构应该如下：

```
.
├── docs/
├── object/
├── outputs/
├── scenes/
├── tmp_images/
├── videos/
├── .gitignore
├── calc_result.txt
├── calculate.py
├── data.py
├── dataset.json
├── main.py
├── object-spatial-relation-dataset.txt
├── object-spatial-relation-handler.py
└── README.md
```

其中比较重要的如下：

`object/`存放所有形变模组数据。记得定期从平台上拉取有效的模组，并且更新其中的`validlist.txt`。里面的json文件存储了所有预处理的结果。

`outputs/`是默认的输出路径。

`scenes/`中存放用于输入的场景，注意在`main.py`中配置。

`tmp_images/`和`videos/`用于简单的可视化。正式生成时记得在`main.py`中关掉。

`data.py`用于数据预处理。

`main.py`是全部逻辑代码。

`object-spatial-relation-handler.py`处理`object-spatial-relation-dataset.txt`后可以得到原始的先验数据`dataset.json`。记得定期从平台上拉取最新的`object-spatial-relation-dataset.txt`。

#### 数据

`data.py`计算每个模组所有状态的精细多边形，并且抄了一遍先验，将每一个模组的信息对应输出到一个json中保存。

不用管纹理确实之类的报错，不会影响。

#### 主逻辑

根据输入场景确定所有带搜索的功能节点（编码）。对每个节点，进行若干次以下尝试：首先尽可能根据先验摆布局，然后尝试输入场景到该布局的形变转移，全部成功则将其记录。最后组织所有的形变动画并输出一系列json。

#### 房间布置

入口是single_search()，里面先有一个匹配先验的预处理preprocess()，然后开始摆action()。

preprocess()是一个随机匹配的过程。它尝试将各个物体选作主物体然后遍历该物体的先验，看场景中有无合适的从物体，并且将其匹配。

action()主体是个不断尝试按先验摆放主从物体的过程。具体而言是先按墙摆主物体，然后考虑摆从物体，最后再考虑从物体的级联关系（仅考虑一层）。如果失败则反复尝试。对于失败的物体，最后统一贴墙摆。

最后需要确定的只是**每个模组在场景中的位置、朝向和状态**。

**注意需要考虑缩放**。

#### 形变过程

暂时不用管
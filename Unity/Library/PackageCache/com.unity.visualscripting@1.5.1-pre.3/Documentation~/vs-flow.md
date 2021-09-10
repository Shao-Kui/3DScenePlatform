#Developing game flow using script graphs

| **Note**                                                     |
| :----------------------------------------------------------- |
| For versions 2019/2020 LTS, download the visual scripting solution from the [Unity Asset Store](https://assetstore.unity.com/packages/tools/visual-bolt-163802). |

Script Graphs are the main tool for creating interactions in projects. Using unit-based actions and values, these graphs execute logic in a specified order, either at every frame or when an event occurs.

###Units as building blocks

[Units](vs-units.md) are the most basic element of computation in visual scripting. They are represented as nodes with input and output [ports](vs-units.md) in script graphs.

###Connecting units

[Connections](vs-connections.md) are formed by linking output and input ports on compatible units. 

###Using relations to debug

Although [relations](vs-relations.md) are predefined for each type of unit and cannot be edited, relations are useful to understanding the dependencies between each port of a unit. As well, visual scripting uses relation information in the background for predictive debugging.

###Predictive debugging

Visual scripting [predicts](vs-debugging.md) and indicates units that cause errors before entering play mode. 

###Reuse graphs with super units

[Super Units](vs-super-units.md) are script graphs that are nested in a parent script graph as a single unit. They are a powerful feature for you to re-use and organize your script graphs.

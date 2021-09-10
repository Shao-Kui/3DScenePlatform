#Object Types

There are hundreds of types available in Unity and visual scripting. Below is a summary table of the some of the most common types.

| Type         | Description                                                  |
| ------------ | ------------------------------------------------------------ |
| Float        | A number with or without decimal values, e.g. 0.5 or 13.25.  |
| Integer      | A number without any decimal value, e.g. 3 or 200.           |
| Boolean      | A value that can only be either true or false. Commonly used in logic or in toggles. |
| String       | A piece of text, e.g. a name or a message.                   |
| Char         | One single character in a string, often alphabetic or numeric. Rarely used. |
| Enums        | There are many enums. Each one is a finite enumeration of options that are often seen in dropdowns.<br />For example, in Unity the "Force Mode" enum can be either "Force", "Impulse", "Acceleration" or "Velocity Change". |
| Vectors      | Vectors represent a set of float coordinates, e.g. for positions or directions.<br />There are 3 vectors in Unity:<br />Vector 2, with X and Y coordinates for 2D;<br />Vector 3, with X, Y and Z coordinates for 3D;<br />Vector 4, with X, Y, Z and W coordinates, rarely used. |
| GameObject   | Gameobjects are the base entity in Unity scenes. Each game object has a name, a transform for its position and rotation, and a list of components. |
| Lists        | A list is an ordered collection of elements. The elements can be of any type, but most often, all elements of a list must be of the same type. Retrieve and assign each element in a list by its zero-based index (position). |
| Dictionaries | A dictionary is a collection in which element has a unique key that maps to its value. For example, you could have a dictionary of age (integer values) by name (string key). Retrieve and assign each element by its key. |
| Object       | "Object" is a special type. When a node asks for an object, it usually means that it doesn't care about the type of that object. |

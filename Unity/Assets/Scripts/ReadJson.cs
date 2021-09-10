using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using LitJson;
using System;
using System.IO;
using AsImpL;

public class ReadJson : MonoBehaviour
{
    private class_JSON myJson;
    public string url = "http://166.111.71.40:11425";

    public List<GameObject> roomFloor;
    public List<GameObject> roomWall;
    public List<GameObject> obj;
    public Dictionary<string, int> uuid_index;

    private int roomCount;
    public int objCount;
    private int obj_index;

    private bool sceneJsonDownload = true;

    private List<bool> roomFloorBuilt;
    private List<bool> roomWallBuilt;
    private List<bool> objBuilt;
    private List<bool> objLoaded;
    private List<bool> roomFloorExisted;
    private List<bool> roomWallExisted;
    private List<bool> objExisted;

    [SerializeField]
    private ImportOptions importOptions = new ImportOptions();

    // Start is called before the first frame update
    void Start()
    {
        GameObject.Find("http").GetComponent<http>().DownloadFilePOST(url + "/online/shaokui", Application.dataPath + "/Resources/shaokui.json"); 
        uuid_index = new Dictionary<string, int>();
        roomFloor = new List<GameObject>();
        roomWall = new List<GameObject>();
        obj = new List<GameObject>();
        roomFloorBuilt = new List<bool>();
        roomWallBuilt = new List<bool>();
        objBuilt = new List<bool>();
        objLoaded = new List<bool>();
        roomFloorExisted = new List<bool>();
        roomWallExisted = new List<bool>();
        objExisted = new List<bool>();
        if (!System.IO.Directory.Exists(Application.dataPath+"/Resources/../../texture/"))
            System.IO.Directory.CreateDirectory(Application.dataPath+"/Resources/../../texture/");
        importOptions.hideWhileLoading = false;
        importOptions.localPosition = new Vector3(0f, 0f, 0f);
        download_and_build();
    }

    void Update()
    {
        build();
        // if (GetComponent<ObjectImporter>().allLoaded)
        // {
        //     if (!setup)
        //         setup_objects();
        // }
    }

    // Update is called once per frame
    public void download_and_build()
    { 
        if (sceneJsonDownload)
        {
            StreamReader streamreader = new StreamReader(Application.dataPath + "/Resources/shaokui.json");
            JsonReader js = new JsonReader(streamreader);
            myJson = JsonMapper.ToObject<class_JSON>(js);
        }
        
        obj_index = 0;
        roomCount = myJson.rooms.Count;
        for (int i = 0; i < roomCount; i++)
        {
            class_room myRoom = myJson.rooms[i];

            roomFloor.Add(new GameObject());
            roomFloorBuilt.Add(false);
            roomFloorExisted.Add(false);
            if (!File.Exists(Application.dataPath+"/Resources/"+myRoom.modelId.ToString()+"f.obj"))
            {               
                roomFloor[i].AddComponent<HttpRequest>();
                roomFloor[i].GetComponent<HttpRequest>().setHttpRequest(
                    url+"/room/"+myRoom.origin.ToString()+"/"+myRoom.modelId.ToString()+"f.obj", 
                    Application.dataPath+"/Resources/"+myRoom.modelId.ToString()+"f.obj", 
                    null);
                roomFloor[i].GetComponent<HttpRequest>().StartDownloadAsyn();
                // GameObject.Find("http").GetComponent<http>().DownloadFile
                //     (url+"/room/"+myRoom.origin.ToString()+"/"+myRoom.modelId.ToString()+"f.obj", 
                //     Application.dataPath+"/Resources/"+myRoom.modelId.ToString()+"f.obj");
            }
            else
                roomFloorExisted[i] = true;

            roomWall.Add(new GameObject());
            roomWallBuilt.Add(false);
            roomWallExisted.Add(false);
            if (!File.Exists(Application.dataPath+"/Resources/"+myRoom.modelId.ToString()+"w.obj"))
            {
                roomWall[i].AddComponent<HttpRequest>();
                roomWall[i].GetComponent<HttpRequest>().setHttpRequest(
                    url+"/room/"+myRoom.origin.ToString()+"/"+myRoom.modelId.ToString()+"w.obj", 
                    Application.dataPath+"/Resources/"+myRoom.modelId.ToString()+"w.obj", 
                    null);
                roomWall[i].GetComponent<HttpRequest>().StartDownloadAsyn();
                // GameObject.Find("http").GetComponent<http>().DownloadFile
                //     (url+"/room/"+myRoom.origin.ToString()+"/"+myRoom.modelId.ToString()+"w.obj", 
                //     Application.dataPath+"/Resources/"+myRoom.modelId.ToString()+"w.obj");
            }
            else
                roomWallExisted[i] = true;

            if (myRoom.objList.Count > 1)
            {
                for (int j = 0; j < myRoom.objList.Count; j++)
                {
                    class_obj myObj = myRoom.objList[j];

                    if (myObj.inDatabase)
                    {
                        obj.Add(new GameObject());
                        obj[obj_index].name = myObj.modelId + ": downloader&importer";
                        objBuilt.Add(false);
                        objLoaded.Add(false);
                        objExisted.Add(false);
                        if (!File.Exists(Application.dataPath+"/Resources/"+myObj.modelId.ToString()+".obj") || !File.Exists(Application.dataPath+"/Resources/"+myObj.modelId.ToString()+".mtl") || !File.Exists(Application.dataPath+"/Resources/../../texture/"+myObj.modelId.ToString()+".jpg"))
                        {
                            obj[obj_index].AddComponent<HttpRequest>();
                            obj[obj_index].AddComponent<HttpRequest>();
                            obj[obj_index].AddComponent<HttpRequest>();
                            obj[obj_index].GetComponents<HttpRequest>()[0].setHttpRequest(
                                url+"/mesh/"+myObj.modelId.ToString(), 
                                Application.dataPath+"/Resources/"+myObj.modelId.ToString()+".obj", 
                                null);
                            obj[obj_index].GetComponents<HttpRequest>()[0].StartDownloadAsyn();
                            obj[obj_index].GetComponents<HttpRequest>()[1].setHttpRequest(
                                url+"/mtl/"+myObj.modelId.ToString(), 
                                Application.dataPath+"/Resources/"+myObj.modelId.ToString()+".mtl", 
                                null);
                            obj[obj_index].GetComponents<HttpRequest>()[1].StartDownloadAsyn();
                            obj[obj_index].GetComponents<HttpRequest>()[2].setHttpRequest(
                                url+"/texture/"+myObj.modelId.ToString()+".jpg",
                                Application.dataPath+"/Resources/../../texture/"+myObj.modelId.ToString()+".jpg",
                                null);
                            obj[obj_index].GetComponents<HttpRequest>()[2].StartDownloadAsyn();
                            // bool flag;
                            // flag = GameObject.Find("http").GetComponent<http>().DownloadFile
                            //     (url+"/mesh/"+myObj.modelId.ToString(), 
                            //     Application.dataPath+"/Resources/"+myObj.modelId.ToString()+".obj");
                            // myObj.inDatabase = flag;
                        }
                        else
                            objExisted[obj_index] = true;
                        objCount += 1;
                        obj_index += 1;
                    }
                    
                    // if (myObj.inDatabase)
                    // {
                    //     if (!File.Exists(Application.dataPath+"/Resources/"+myObj.modelId.ToString()+".mtl"))
                    //     {
                    //         GameObject.Find("http").GetComponent<http>().DownloadFile
                    //             (url+"/mtl/"+myObj.modelId.ToString(),
                    //             Application.dataPath+"/Resources/"+myObj.modelId.ToString()+".mtl");
                    //     }
                        
                    //     if (!File.Exists(Application.dataPath+"/Resources/../../texture/"+myObj.modelId.ToString()+".jpg"))
                    //     {
                    //         GameObject.Find("http").GetComponent<http>().DownloadFile
                    //             (url+"/texture/"+myObj.modelId.ToString()+".jpg",
                    //             Application.dataPath+"/Resources/../../texture/"+myObj.modelId.ToString()+".jpg");
                    //     }
                        
                    //     objCount += 1;
                    // }
                }
            }
        }
        //roomFloor = new GameObject[roomCount];
        //roomWall = new GameObject[roomCount];

        //build();
    }

    public void build_floor(int i, class_room myRoom)
    {
        roomFloor[i].name = myRoom.modelId.ToString()+"f";
        roomFloor[i].AddComponent<MeshFilter>();
        roomFloor[i].AddComponent<MeshRenderer>();
        roomFloor[i].GetComponent<MeshFilter>().mesh = GetComponent<ObjImporter>().ImportFile(Application.dataPath+"/Resources/"+myRoom.modelId.ToString()+"f.obj");
        roomFloor[i].GetComponent<MeshRenderer>().material = new Material(Shader.Find("Standard"));
        roomFloorBuilt[i] = true;
    }

    public void build_wall(int i, class_room myRoom)
    {
        roomWall[i].name = myRoom.modelId.ToString()+"w";
        roomWall[i].AddComponent<MeshFilter>();
        roomWall[i].AddComponent<MeshRenderer>();
        roomWall[i].GetComponent<MeshFilter>().mesh = GetComponent<ObjImporter>().ImportFile(Application.dataPath+"/Resources/"+myRoom.modelId.ToString()+"w.obj");
        roomWall[i].GetComponent<MeshRenderer>().material = new Material(Shader.Find("Standard"));
        roomWallBuilt[i] = true;
    }


    public void build()
    {
        obj_index = 0;

        for (int i = 0; i < myJson.rooms.Count; i++)
        {
            class_room myRoom = myJson.rooms[i];
            
            if (!roomFloorBuilt[i] && (roomFloorExisted[i] || roomFloor[i].GetComponent<HttpRequest>().isDownloaded))
                build_floor(i, myRoom);

            if (!roomWallBuilt[i] && (roomWallExisted[i] || roomWall[i].GetComponent<HttpRequest>().isDownloaded))
                build_wall(i, myRoom);

            for (int j = 0; j < myRoom.objList.Count; j++)
            {
                class_obj myObj = myRoom.objList[j];
                
                if (myObj.inDatabase)
                {
                    if (!objLoaded[obj_index] && (objExisted[obj_index] || (obj[obj_index].GetComponents<HttpRequest>()[0].isDownloaded && obj[obj_index].GetComponents<HttpRequest>()[1].isDownloaded && obj[obj_index].GetComponents<HttpRequest>()[2].isDownloaded)))
                    {
                        obj[obj_index].AddComponent<ObjectImporter>(); 
                        obj[obj_index].GetComponent<ObjectImporter>().ImportModelAsync(myObj.modelId + ": " + myObj.key, Application.dataPath+"/Resources/"+myObj.modelId.ToString()+".obj", null, importOptions);
                        uuid_index.Add(myObj.key, obj_index);
                        objLoaded[obj_index] = true;
                    }
                    if (!objBuilt[obj_index] && objLoaded[obj_index] && obj[obj_index].GetComponent<ObjectImporter>().allLoaded)
                    {
                        GameObject.Destroy(obj[obj_index]);
                        obj[obj_index] = GameObject.Find(myObj.modelId + ": " + myObj.key);
                        obj[obj_index].transform.localPosition = new Vector3((float)myObj.translate[0], (float)myObj.translate[1], (float)myObj.translate[2]);
                        obj[obj_index].transform.localScale = new Vector3((float)myObj.scale[0], (float)myObj.scale[1], -(float)myObj.scale[2]);
                        obj[obj_index].transform.Rotate((float)(myObj.rotate[0]/Mathf.PI*180)%360f, 0f, 0f, Space.Self);
                        obj[obj_index].transform.Rotate(0f, (float)(myObj.rotate[1]/Mathf.PI*180)%360f, 0f, Space.Self);
                        obj[obj_index].transform.Rotate(0f, 0f, (float)(myObj.rotate[2]/Mathf.PI*180)%360f, Space.Self);

                        obj[obj_index].AddComponent<emit>();
                        obj[obj_index].GetComponent<emit>().uuid = myObj.key;
                        if (myObj.rotate[0] == 0)
                            obj[obj_index].GetComponent<emit>().rotateMode = true;
                        else
                            obj[obj_index].GetComponent<emit>().rotateMode = false;
                        
                        objBuilt[obj_index] = true;
                    }
                    obj_index += 1;
                }
            }
        }
    }

    public void setup_objects()
    {
        obj_index = 0;

        for (int i = 0; i < myJson.rooms.Count; i++)
        {
            class_room myRoom = myJson.rooms[i];
            for (int j = 0; j < myRoom.objList.Count; j++)
            {
                class_obj myObj = myRoom.objList[j];
                if (myObj.inDatabase)
                {
                    obj[obj_index].name = myObj.modelId + ": " + myObj.key;
                    obj[obj_index].transform.localPosition = new Vector3((float)myObj.translate[0], (float)myObj.translate[1], (float)myObj.translate[2]);
                    obj[obj_index].transform.localScale = new Vector3((float)myObj.scale[0], (float)myObj.scale[1], -(float)myObj.scale[2]);
                    obj[obj_index].transform.Rotate((float)(myObj.rotate[0]/Mathf.PI*180)%360f, 0f, 0f, Space.Self);
                    obj[obj_index].transform.Rotate(0f, (float)(myObj.rotate[1]/Mathf.PI*180)%360f, 0f, Space.Self);
                    obj[obj_index].transform.Rotate(0f, 0f, (float)(myObj.rotate[2]/Mathf.PI*180)%360f, Space.Self);

                    obj[obj_index].AddComponent<emit>();
                    obj[obj_index].GetComponent<emit>().uuid = myObj.key;
                    if (myObj.rotate[0] == 0)
                        obj[obj_index].GetComponent<emit>().rotateMode = true;
                    else
                        obj[obj_index].GetComponent<emit>().rotateMode = false;
                    
                    objBuilt[obj_index] = true;

                    obj_index += 1;
                }
            }
        }
    }

    public void sceneRefresh(string sceneJson)
    {
        for (int i = 0; i < roomFloor.Count; i++)
            GameObject.Destroy(roomFloor[i]);
        for (int i = 0; i < roomWall.Count; i++)
            GameObject.Destroy(roomWall[i]);
        for (int i = 0; i < obj.Count; i++)
            GameObject.Destroy(obj[i]);

        roomFloor.Clear();
        roomWall.Clear();
        obj.Clear();
        uuid_index.Clear();
        roomCount = 0;
        objCount = 0;
        obj_index = 0;

        roomFloorBuilt.Clear();
        roomWallBuilt.Clear();
        objBuilt.Clear();
        objLoaded.Clear();
        roomFloorExisted.Clear();
        roomWallExisted.Clear();
        objExisted.Clear();

        sceneJsonDownload = false;
        myJson = JsonMapper.ToObject<class_JSON>(sceneJson);

        download_and_build();
    }
}

public class class_JSON
{
    public string origin { get; set; }
    public string id { get; set; }
    public class_bbox bbox { get; set; }
    public List<int> up { get; set; }
    public List<int> front { get; set; }
    public List<class_room> rooms { get; set; }
    public double coarseWallHeight { get; set; }
    public class_PerspectiveCamera PerspectiveCamera { get; set; }
    public class_canvas canvas { get; set; }
}

public class class_bbox
{
    public List<double> min;
    public List<double> max;
}

public class class_room
{
    public string id { get; set; }
    public string modelId { get; set; }
    public List<string> roomTypes { get; set; }
    public class_bbox bbox { get; set; }
    public string origin { get; set; }
    public int roomId { get; set; }
    public List<class_obj> objList { get; set; }
}

public class class_obj
{
    public string id { get; set; }
    public string type { get; set; }
    public string modelId { get; set; }
    public class_bbox bbox { get; set; }
    public List<double> translate { get; set; }
    public List<double> scale { get; set; } 
    public List<double> rotate { get; set; } 
    public string rotateOrder { get; set; } 
    public double orient { get; set; } 
    public string coarseSemantic { get; set; } 
    public int roomId { get; set; } 
    public bool inDatabase { get; set; } 
    public List<int> roomIds { get; set; }
    public double width { get; set; }
    public double length { get; set; }
    public double height { get; set; }
    public string key { get; set; }
    public string mageAddDerive { get; set; }
    public Dictionary<string, int> childnum { get; set; }
    public class_obj myparent { get; set; }
    public bool isHeu { get; set; }
}

public class class_PerspectiveCamera
{
    public int fov { get; set; }
    public int focalLength { get; set; }
    public List<double> origin { get; set; }
    public List<double> rotate { get; set; }
    public List<double> target { get; set; }
    public int roomId { get; set; }
    public List<double> up { get; set; }
}

public class class_canvas
{
    public int width { get; set; }
    public int height { get; set; }
}

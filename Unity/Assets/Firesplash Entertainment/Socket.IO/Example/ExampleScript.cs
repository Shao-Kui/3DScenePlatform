using Firesplash.UnityAssets.SocketIO;
using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using LitJson;
using AsImpL;

public class ExampleScript : MonoBehaviour
{
    public SocketIOCommunicator sioCom;
    private GameObject ReadJson;
    private GameObject empty;
    public string url = "http://166.111.71.40:11425";
    private Dictionary<string, List<class_animateObj>> animateObj;
    private Dictionary<string, Transform> transforms;
    private Dictionary<string, Transform> origins;
    private List<class_addObj> addObjList;

    [Serializable]
    struct ItsMeData
    {
        public string version;
    }

    [Serializable]
    struct ServerTechData
    {
        public string timestamp;
        public string podName;
    }

    [SerializeField]
    private ImportOptions importOptions = new ImportOptions();

    // Start is called before the first frame update
    void Start()
    {
        ReadJson = GameObject.Find("ReadJson");
        empty = GameObject.Find("empty");
        animateObj = new Dictionary<string, List<class_animateObj>>();
        transforms = new Dictionary<string, Transform>();
        origins = new Dictionary<string, Transform>();
        addObjList = new List<class_addObj>();
        importOptions.hideWhileLoading = true;
        importOptions.localPosition = new Vector3(0f, -10f, 0f);

        //sioCom is assigned via inspector so no need to initialize it.
        //We just fetch the actual Socket.IO instance using its integrated Instance handle and subscribe to the connect event
        sioCom.Instance.On("connect", (string data) => {
            Debug.Log("LOCAL: Hey, we are connected!");

            //NOTE: All those emitted and received events (except connect and disconnect) are made to showcase how this asset works. The technical handshake is done automatically.

            //First of all we knock at the servers door
            //EXAMPLE 1: Sending an event without payload data
            sioCom.Instance.Emit("KnockKnock");
            sioCom.Instance.Emit("join", "shaokui");
            //Debug.Log(data);
            sioCom.Instance.Emit("sktest", "ghost");
        });

        sioCom.Instance.On("functionCall", (string data) => {
            //Debug.Log("LOCAL: Hey, we received a functionCall!");
            //Debug.Log(data);

            string result = data.Replace(',',' ').Replace('"',' ').Replace('[',' ').Replace(']',' ').Replace('{',' ').Replace('}',' ').Replace(':',' ');
            string[] resultList = result.Split(' ');

            result = "";
            foreach (string s in resultList)
            {
                if (s != "")
                    result += s + " ";
            }
            resultList = result.Split(' ');

            string functionName = resultList[0];

            if (functionName == "transformObjectByUUID")
            {
                // string uuid = resultList[1];
                // int obj_index = ReadJson.GetComponent<ReadJson>().uuid_index[uuid];
                // GameObject myObj = ReadJson.GetComponent<ReadJson>().obj[obj_index];

                // double[] translate = {double.Parse(resultList[3]), double.Parse(resultList[4]), double.Parse(resultList[5])};
                // double[] scale = {double.Parse(resultList[7]), double.Parse(resultList[8]), double.Parse(resultList[9])};
                // double[] rotate = {double.Parse(resultList[11]), double.Parse(resultList[12]), double.Parse(resultList[13])};

                // myObj.transform.position = new Vector3((float)translate[0], (float)translate[1], (float)translate[2]);
                // myObj.transform.localScale = new Vector3(-(float)scale[0], (float)scale[1], (float)scale[2]);
                // myObj.transform.localRotation = Quaternion.Euler(new Vector3(0f, 0f, 0f));
                // myObj.transform.Rotate((float)(rotate[0]/Mathf.PI*180)%360f, 0f, 0f, Space.Self);
                // myObj.transform.Rotate(0f, (float)(rotate[1]/Mathf.PI*180)%360f, 0f, Space.Self);
                // myObj.transform.Rotate(0f, 0f, (float)(rotate[2]/Mathf.PI*180)%360f, Space.Self);

                // if (!transforms.ContainsKey(uuid))
                //     transforms.Add(uuid, myObj.transform);
                // else
                //     transforms[uuid] = myObj.transform;
            }

            if (functionName == "removeObjectByUUID")
            {
                string uuid = resultList[1];
                int obj_index = ReadJson.GetComponent<ReadJson>().uuid_index[uuid];
                GameObject.Destroy(ReadJson.GetComponent<ReadJson>().obj[obj_index]);
            }

            if (functionName == "addObjectFromCache")
            {
                class_addObj addObj = new class_addObj();
                addObj.modelId = resultList[1];
                addObj.translate = new double[3];
                addObj.rotate = new double[3];
                addObj.scale = new double[3];
                addObj.translate[0] = double.Parse(resultList[3]); 
                addObj.translate[1] = double.Parse(resultList[4]);
                addObj.translate[2] = double.Parse(resultList[5]);
                addObj.rotate[0] = double.Parse(resultList[7]);
                addObj.rotate[1] = double.Parse(resultList[8]);
                addObj.rotate[2] = double.Parse(resultList[9]);
                addObj.scale[0] = double.Parse(resultList[11]);
                addObj.scale[1] = double.Parse(resultList[12]);
                addObj.scale[2] = double.Parse(resultList[13]);
                addObj.uuid = resultList[14];
                addObjList.Add(addObj);

                GameObject.Find("http").GetComponent<http>().DownloadFile
                    (url+"/mesh/"+addObj.modelId.ToString(), 
                    Application.dataPath+"/Resources/"+addObj.modelId.ToString()+".obj");
                GameObject.Find("http").GetComponent<http>().DownloadFile
                    (url+"/mtl/"+addObj.modelId.ToString(),
                    Application.dataPath+"/Resources/"+addObj.modelId.ToString()+".mtl");            
                GameObject.Find("http").GetComponent<http>().DownloadFile
                    (url+"/texture/"+addObj.modelId.ToString()+".jpg",
                    Application.dataPath+"/Resources/../../texture/"+addObj.modelId.ToString()+".jpg");
                
                ReadJson.GetComponent<ReadJson>().objCount += 1;
                
                ReadJson.GetComponent<ReadJson>().uuid_index.Add(addObj.uuid, ReadJson.GetComponent<ReadJson>().objCount - 1);

                GetComponent<ObjectImporter>().ImportModelAsync(addObj.modelId + ": " + addObj.uuid, Application.dataPath+"/Resources/"+addObj.modelId.ToString()+".obj", null, importOptions);
            }

            if (functionName == "animateObject3DOnly")
            {
                int n = (int)(resultList.Length / 10);
                for (int i = 0; i < n; i++)
                {
                    class_animateObj temp = new class_animateObj();
                    temp.x = double.Parse(resultList[i*10+4]);
                    temp.y = double.Parse(resultList[i*10+5]);
                    temp.z = double.Parse(resultList[i*10+6]);
                    temp.duration = float.Parse(resultList[i*10+8]) * 0.001f;
                    temp.mode = resultList[i*10+10];
                    if (temp.mode == "scale")
                        temp.z = -temp.z;
                    string uuid = resultList[i*10+2];
                    if (!animateObj.ContainsKey(uuid))
                        animateObj.Add(uuid, new List<class_animateObj>());
                    animateObj[uuid].Add(temp);
                    if (!origins.ContainsKey(uuid))
                    {
                        int obj_index = ReadJson.GetComponent<ReadJson>().uuid_index[uuid];
                        GameObject myObj = ReadJson.GetComponent<ReadJson>().obj[obj_index];
                        origins.Add(uuid, myObj.transform);
                    }
                }
            }
        });

        sioCom.Instance.On("sceneRefresh", (string sceneJson) => {
            animateObj.Clear();
            transforms.Clear();
            origins.Clear();
            ReadJson.GetComponent<ReadJson>().sceneRefresh(sceneJson);
        });

        //When the conversation is done, the server will close our connection after we said Goodbye
        sioCom.Instance.On("disconnect", (string payload) => {
            if (payload.Equals("io server disconnect"))
            {
                Debug.Log("Disconnected from server.");
            } 
            else
            {
                Debug.LogWarning("We have been unexpecteldy disconnected. This will cause an automatic reconnect. Reason: " + payload);
            }
        });


        //We are now ready to actually connect
        sioCom.Instance.Connect();
    }

    public void emitFunctionCall(string emitString)
    {
        sioCom.Instance.Emit("functionCallUnity", emitString, false);
    }

    public void setup_selected_object(class_addObj addObj)
    {
        int objCount = ReadJson.GetComponent<ReadJson>().objCount;

        ReadJson.GetComponent<ReadJson>().obj.Add(GameObject.Find(addObj.modelId + ": " + addObj.uuid));
        ReadJson.GetComponent<ReadJson>().obj[objCount - 1].transform.position = new Vector3((float)addObj.translate[0], (float)addObj.translate[1], (float)addObj.translate[2]);
        ReadJson.GetComponent<ReadJson>().obj[objCount - 1].transform.localScale = new Vector3((float)addObj.scale[0], (float)addObj.scale[1], -(float)addObj.scale[2]);
        ReadJson.GetComponent<ReadJson>().obj[objCount - 1].transform.Rotate((float)(addObj.rotate[0]/Mathf.PI*180)%360f, 0f, 0f, Space.Self);
        ReadJson.GetComponent<ReadJson>().obj[objCount - 1].transform.Rotate(0f, (float)(addObj.rotate[1]/Mathf.PI*180)%360f, 0f, Space.Self);
        ReadJson.GetComponent<ReadJson>().obj[objCount - 1].transform.Rotate(0f, 0f, (float)(addObj.rotate[2]/Mathf.PI*180)%360f, Space.Self);

        ReadJson.GetComponent<ReadJson>().obj[objCount - 1].AddComponent<emit>();
        ReadJson.GetComponent<ReadJson>().obj[objCount - 1].GetComponent<emit>().uuid = addObj.uuid;
        if (addObj.rotate[0] == 0)
            ReadJson.GetComponent<ReadJson>().obj[objCount - 1].GetComponent<emit>().rotateMode = true;
        else
            ReadJson.GetComponent<ReadJson>().obj[objCount - 1].GetComponent<emit>().rotateMode = false;
    }

    void Update()
    {
        foreach (KeyValuePair<string, List<class_animateObj>> kvp in animateObj)
        {
            string uuid = kvp.Key;
            int obj_index = ReadJson.GetComponent<ReadJson>().uuid_index[uuid];
            GameObject myObj = ReadJson.GetComponent<ReadJson>().obj[obj_index];

            if (kvp.Value.Count > 0)
            {
                Vector3 target = new Vector3((float)kvp.Value[0].x, (float)kvp.Value[0].y, (float)kvp.Value[0].z);
                // Transform origin;
                // if (!origins.ContainsKey(uuid))
                //     origin = transforms[uuid];
                // else
                //     origin = origins[uuid];
                Transform origin = origins[uuid];

                if (kvp.Value[0].mode == "position")
                {
                    float distance = Vector3.Distance(origin.position, target);
                    float speed = distance / kvp.Value[0].duration;
                    myObj.transform.position = Vector3.MoveTowards(origin.position, target, Time.deltaTime * speed);
                    if (myObj.transform.position == target)
                    {
                        kvp.Value.RemoveAt(0);
                        if (!origins.ContainsKey(uuid))
                            origins.Add(uuid, myObj.transform);
                        else
                            origins[uuid] = myObj.transform;
                    }
                }
                else if (kvp.Value[0].mode == "scale")
                {
                    float distance = Vector3.Distance(origin.localScale, target);
                    float speed = distance / kvp.Value[0].duration;
                    myObj.transform.localScale = Vector3.MoveTowards(origin.localScale, target, Time.deltaTime * speed);
                    if (myObj.transform.localScale == target)
                    {
                        kvp.Value.RemoveAt(0);
                        if (!origins.ContainsKey(uuid))
                            origins.Add(uuid, myObj.transform);
                        else
                            origins[uuid] = myObj.transform;
                    }
                }
                else
                {
                    empty.transform.localRotation = Quaternion.Euler(new Vector3(0f, 0f, 0f));
                    empty.transform.Rotate((float)(target[0]/Mathf.PI*180)%360f, 0f, 0f, Space.Self);
                    empty.transform.Rotate(0f, (float)(target[1]/Mathf.PI*180)%360f, 0f, Space.Self);
                    empty.transform.Rotate(0f, 0f, (float)(target[2]/Mathf.PI*180)%360f, Space.Self);
                    target = empty.transform.localEulerAngles;
                    float distance = Vector3.Distance(origin.localEulerAngles, target);
                    float speed = distance / kvp.Value[0].duration;
                    myObj.transform.localEulerAngles = Vector3.MoveTowards(origin.localEulerAngles, target, Time.deltaTime * speed);
                    if (Vector3.Distance(myObj.transform.localEulerAngles, target) < 1E-04)
                    {
                        kvp.Value.RemoveAt(0);
                        if (!origins.ContainsKey(uuid))
                            origins.Add(uuid, myObj.transform);
                        else
                            origins[uuid] = myObj.transform;
                    }
                }
            }
        }

        if (GetComponent<ObjectImporter>().allLoaded)
        {
            if (addObjList.Count > 0)
            {
                setup_selected_object(addObjList[0]);
                addObjList.RemoveAt(0);
            }
        }
    }
}

public class class_animateObj
{
    public double x { get; set; }
    public double y { get; set; }
    public double z { get; set; }
    public float duration { get; set; }
    public string mode { get; set; }
}

public class class_addObj
{
    public string modelId { get; set; }
    public double[] translate { get; set; }
    public double[] rotate { get; set; }
    public double[] scale { get; set; }
    public string uuid { get; set; }
}
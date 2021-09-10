using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using LitJson;

public class emit : MonoBehaviour
{
    private GameObject ExampleScript;

    public int mode = 0; //1: position; 2: scale; 3: rotation
    private int premode = 0;
    private float timer = 0f;
    private float interval = 0.1f;
    private class_emitString emitString;
    public string uuid;
    public bool rotateMode;
    private class_animateObjWithUUID animateObj;
    private int argNum = 0;

    // Start is called before the first frame update
    void Start()
    {
        ExampleScript = GameObject.Find("SocketIOSample");
        animateObj = new class_animateObjWithUUID();
        animateObj.xyz = new double[3];
        emitString = new class_emitString();
        emitString.fname = "animateObject3DOnly";
        emitString.groupName = "shaokui";
        emitString.arguments = "[";
    }

    void Update()
    {
        if (mode != premode && premode != 0 && mode != 0)
        {
            if (argNum != 0)
            {
                emitString.arguments = emitString.arguments.Substring(0, emitString.arguments.Length - 1) + "]";
                ExampleScript.GetComponent<ExampleScript>().emitFunctionCall(JsonMapper.ToJson(emitString));
                //Debug.Log(JsonMapper.ToJson(emitString));
            }
            emitString.arguments = "[";
            timer = 0f;
        }
        
        if (mode != 0)
        {
            timer += Time.deltaTime;

            animateObj.uuid = uuid;
            if (mode == 1)
            {
                animateObj.xyz[0] = (double)transform.position.x;
                animateObj.xyz[1] = (double)transform.position.y;
                animateObj.xyz[2] = (double)transform.position.z;
                animateObj.mode = "position";
            }
            else if (mode == 2)
            {
                animateObj.xyz[0] = (double)transform.localScale.x;
                animateObj.xyz[1] = (double)transform.localScale.y;
                animateObj.xyz[2] = -(double)transform.localScale.z;
                animateObj.mode = "scale";
            }
            else if (mode == 3)
            {
                if (rotateMode)
                {
                   animateObj.xyz[0] = 0;
                   animateObj.xyz[1] = (double)transform.localEulerAngles.y / 180 * Mathf.PI;
                   animateObj.xyz[2] = 0;
                }
                else
                {
                   animateObj.xyz[0] = Mathf.PI;
                   animateObj.xyz[1] = (double)(180 - transform.localEulerAngles.y) / 180 * Mathf.PI;
                   animateObj.xyz[2] = Mathf.PI;
                }
                animateObj.mode = "rotation";
            }
            animateObj.duration = (double)Time.deltaTime;

            emitString.arguments = emitString.arguments + JsonMapper.ToJson(animateObj) + ",";
            argNum++;

            if (timer >= interval)
            {
                emitString.arguments = emitString.arguments.Substring(0, emitString.arguments.Length - 1) + "]";
                ExampleScript.GetComponent<ExampleScript>().emitFunctionCall(JsonMapper.ToJson(emitString));
                //Debug.Log(JsonMapper.ToJson(emitString));
                emitString.arguments = "[";
                timer = 0f;
            }
        }

        premode = mode;
    }
}

public class class_animateObjWithUUID
{
    public string uuid { get; set; }
    public double[] xyz { get; set; }
    public double duration { get; set; }
    public string mode { get; set; }
}

public class class_emitString
{
    public string fname { get; set; }
    public string arguments { get; set; }
    public string groupName { get; set; }
}
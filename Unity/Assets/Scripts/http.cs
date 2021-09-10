using System.Collections;
using System.Collections.Generic;
using System.Net;
using System.IO;
using UnityEngine;
using UnityEditor;

public class http : MonoBehaviour
{
    private GameObject myObj;  
    private bool flag;
    private bool built;

    // Start is called before the first frame update
    void Start()
    {
        //DownloadFile(@"http://166.111.71.40:11425/texture/1280.jpg", @"C:/Users/hp/Downloads/1280.jpg");
        //flag = DownloadFile(@"http://166.111.71.40:11425/mesh/8263", Application.dataPath+"/Resources/8263.obj");
        //DownloadFile(@"http://166.111.71.40:11425/mtl/1280", @"C:/Users/hp/Downloads/1280.mtl");
        //StartCoroutine("StartDownload");
        //DownloadFile(@"http://166.111.71.40:11425/online/shaokui", @"C:/Users/hp/Downloads/shaokui.json");
    }

    // Update is called once per frame
    void Update()
    {

    }

    IEnumerator StartDownload ()
    {
        flag = DownloadFile(@"http://166.111.71.40:11425/mesh/8263", Application.dataPath+"/Resources/8263.obj");
        yield return 1;
    }

    ///<summary>
    /// 下载文件
    /// </summary>
    /// <param name="URL">下载文件地址</param>
    /// <param name="Filename">下载后另存为（全路径）</param>
    public bool DownloadFilePOST(string URL, string filename)
    {
        try
        {
            HttpWebRequest Myrq = (System.Net.HttpWebRequest)System.Net.HttpWebRequest.Create(URL);
            Myrq.Method = "POST";
            HttpWebResponse myrp = (System.Net.HttpWebResponse)Myrq.GetResponse();
            Stream st = myrp.GetResponseStream();
            Stream so = new System.IO.FileStream(filename, System.IO.FileMode.Create);
            byte[] by = new byte[1024];
            int osize = st.Read(by, 0, (int)by.Length);
            while (osize > 0)
            {
                so.Write(by, 0, osize);
                osize = st.Read(by, 0, (int)by.Length);
            }
            so.Close();
            st.Close();
            myrp.Close();
            Myrq.Abort();
            #if UNITY_EDITOR 
                UnityEditor.AssetDatabase.Refresh();//刷新Unity的资产目录 
            #endif 
            return true;
        }
        catch (System.Exception e)
        {
            return false;
        }
    }

    public bool DownloadFile(string URL, string filename)
    {
        try
        {
            HttpWebRequest Myrq = (System.Net.HttpWebRequest)System.Net.HttpWebRequest.Create(URL);
            HttpWebResponse myrp = (System.Net.HttpWebResponse)Myrq.GetResponse();
            Stream st = myrp.GetResponseStream();
            Stream so = new System.IO.FileStream(filename, System.IO.FileMode.Create);
            byte[] by = new byte[1024];
            int osize = st.Read(by, 0, (int)by.Length);
            while (osize > 0)
            {
                so.Write(by, 0, osize);
                osize = st.Read(by, 0, (int)by.Length);
            }
            so.Close();
            st.Close();
            myrp.Close();
            Myrq.Abort();
            #if UNITY_EDITOR 
                UnityEditor.AssetDatabase.Refresh();//刷新Unity的资产目录 
            #endif
            return true;
        }
        catch (System.Exception e)
        {
            return false;
        }
    }
}

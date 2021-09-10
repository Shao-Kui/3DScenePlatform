using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;
using System.Net;
using System.IO;
using System.Text;
using System.Threading;


public class HttpRequest : MonoBehaviour
{
    private const int mBufferSize = 1024;

    private string mUri = string.Empty;
    private string mSaveFilePath = string.Empty;
    private FileStream mFileStream = null;
    private System.Action mDownloadCompleted = null;

    public bool isDownloaded = false;

    public void setHttpRequest(string uri, string path, System.Action downloadCompleted)
    {
        mUri = uri;
        mSaveFilePath = path;
        mDownloadCompleted = downloadCompleted;
    }


    public void StartDownloadAsyn()
    {
        try
        {
            HttpWebRequest hwr = (HttpWebRequest)WebRequest.Create(mUri);

            HttpRequestState hrs = new HttpRequestState();
            hrs.mRequest = hwr;

            System.IAsyncResult result = (System.IAsyncResult)hwr.BeginGetResponse(new System.AsyncCallback(RespCallback), hrs);
        }
        catch(System.Exception e)
        {
        }
    }


    void RespCallback(System.IAsyncResult result)
    {
        try
        {
            HttpRequestState hrs = (HttpRequestState)result.AsyncState;
            HttpWebRequest hwr = hrs.mRequest;

            hrs.mResponse = (HttpWebResponse)hwr.EndGetResponse(result);

            Stream responseStream = hrs.mResponse.GetResponseStream();
            hrs.mStreamResponse = responseStream;

            System.IAsyncResult ret = responseStream.BeginRead(hrs.mBufferRead, 0, mBufferSize, new System.AsyncCallback(ReadCallBack), hrs);
        }
        catch (System.Exception e)
        {
        }
    }


    void ReadCallBack(System.IAsyncResult result)
    {
        try
        {
            HttpRequestState hrs = (HttpRequestState)result.AsyncState;
            Stream responseStream = hrs.mStreamResponse;
            int read = responseStream.EndRead(result);

            if (read > 0)
            {
                if (mFileStream == null)
                    mFileStream = new FileStream(mSaveFilePath, FileMode.OpenOrCreate);

                mFileStream.Write(hrs.mBufferRead, 0, mBufferSize);
                mFileStream.Flush();

                //Debug.Log("进度处理");

                hrs.mBufferRead = new byte[mBufferSize];
                System.IAsyncResult ret = responseStream.BeginRead(hrs.mBufferRead, 0, mBufferSize, new System.AsyncCallback(ReadCallBack), hrs);
            }
            else
            {
                Debug.Log("下载完成");
                isDownloaded = true;
                mFileStream.Flush();
                mFileStream.Close();
                mDownloadCompleted();
            }
        }
        catch(System.Exception e)
        {
        }
    }
}


public class HttpRequestState
{
    const int mBufferSize = 1024;
    public byte[] mBufferRead;

    public HttpWebRequest mRequest;
    public HttpWebResponse mResponse;
    public Stream mStreamResponse;


    public HttpRequestState()
    {
        mBufferRead = new byte[mBufferSize];
        mRequest = null;
        mStreamResponse = null;
    } 
}
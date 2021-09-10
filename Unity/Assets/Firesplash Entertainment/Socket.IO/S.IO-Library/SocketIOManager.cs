using System;
using System.Collections.Generic;
using UnityEngine;

namespace Firesplash.UnityAssets.SocketIO.Internal
{
    internal class SocketIOManager
    {
        private static readonly object padlock = new object();
        private static SocketIOManager _instance = null;
        private static Dictionary<string, SocketIOInstance> SIOInstances;

        public static SocketIOManager Instance
        {
            get
            {
                if (_instance == null) lock (padlock)
                {
                    if (_instance == null) _instance = new SocketIOManager();
                }
                return _instance;
            }
        }

#if UNITY_WEBGL
        [System.Runtime.InteropServices.DllImport("__Internal")]
        private static extern void InstallSocketIO();

        [System.Runtime.InteropServices.DllImport("__Internal")]
        private static extern void InitializeSIOVars();
#endif

        internal static void LogDebug(string text)
        {
            Debug.Log("[Socket.IO Implementation] " + text);
        }
        internal static void LogWarning(string text)
        {
            Debug.LogWarning("[Socket.IO Implementation] " + text);
        }
        internal static void LogError(string text)
        {
            Debug.LogError("[Socket.IO Implementation] " + text);
        }

        private SocketIOManager()
        {
            //TODO implement editor fallback to native mode
            SIOInstances = new Dictionary<string, SocketIOInstance>();

#if UNITY_WEBGL
            if (Application.platform == RuntimePlatform.WebGLPlayer)
            {
                LogDebug("Installing JS-Based Socket.IO subsystem");
                InstallSocketIO(); //loads socket.io client library
                InitializeSIOVars(); //initializes window level arrays for usage
            }
#endif
        }

        internal void Verify()
        {
            //Dummy
        }

        internal SocketIOInstance CreateSIOInstance(string instanceName, string targetAddress)
        {
            
            if (SIOInstances.ContainsKey(instanceName))
            {
                LogWarning("You are creating an instance named " + instanceName + " which has already been created before. This will overwrite the existing instance. Was this supposed? If no, rename one of your Game Objects (instances are identified by the name of the GameObject where the SocketIOCommunicator Component is attached)");
                //We need to replace this connection
                SIOInstances[instanceName]?.Close();
                SIOInstances.Remove(instanceName);
            }

            SocketIOInstance inst = null;

            if (Application.platform == RuntimePlatform.WebGLPlayer)
            {
#if UNITY_WEBGL
                inst = new SocketIOWebGLInstance(instanceName, targetAddress);
#endif
            }
            else
            {
                inst = new SocketIONativeInstance(instanceName, targetAddress);
            }

            try
            {
                SIOInstances.Add(instanceName, inst); //keep a handle
            }
            catch (ArgumentException)
            {
                //This should not happen - but it can.
                if (SIOInstances.ContainsKey(instanceName)) SIOInstances[instanceName] = inst;
            }
            return inst;
        }
    }
}

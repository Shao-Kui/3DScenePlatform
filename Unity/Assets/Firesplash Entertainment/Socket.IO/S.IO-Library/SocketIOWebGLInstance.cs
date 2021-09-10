using System;

namespace Firesplash.UnityAssets.SocketIO.Internal
{
#if UNITY_WEBGL
    internal class SocketIOWebGLInstance : SocketIOInstance
    {
        [System.Runtime.InteropServices.DllImport("__Internal")]
        private static extern void CreateSIOInstance(string instanceName, string targetAddress);

        [System.Runtime.InteropServices.DllImport("__Internal")]
        private static extern void ConnectSIOInstance(string instanceName);

        [System.Runtime.InteropServices.DllImport("__Internal")]
        private static extern void RegisterSIOEvent(string instanceName, string eventName);

        [System.Runtime.InteropServices.DllImport("__Internal")]
        private static extern void UnregisterSIOEvent(string instanceName, string eventName);

        [System.Runtime.InteropServices.DllImport("__Internal")]
        private static extern void SIOEmitWithData(string instanceName, string eventName, string data, int parseAsJSON);

        [System.Runtime.InteropServices.DllImport("__Internal")]
        private static extern void SIOEmitNoData(string instanceName, string eventName);

        internal SocketIOWebGLInstance(string instanceName, string targetAddress) : base(instanceName, targetAddress)
        {
            SocketIOManager.LogDebug("Creating WebGL-Based Socket.IO instance for " + instanceName);
            this.InstanceName = instanceName;
            CreateSIOInstance(instanceName, targetAddress);
        }

        public override void Connect()
        {
            ConnectSIOInstance(InstanceName);
            base.Connect();
        }

        public override void On(string EventName, SocketIOEvent Callback)
        {
            //Create JS-Representation
            RegisterSIOEvent(InstanceName, EventName);

            //Now register the callback to the base class's dictionary
            base.On(EventName, Callback);
        }

        public override void Off(string EventName)
        {
            //Create JS-Representation
            UnregisterSIOEvent(InstanceName, EventName);

            //Now register the callback to the base class's dictionary
            base.Off(EventName);
        }

        public override void Emit(string EventName, string Data, bool DataIsPlainText)
        {
            SIOEmitWithData(InstanceName, EventName, Data, DataIsPlainText ? 0 : 1);
        }

#if !HAS_JSON_NET
        [Obsolete]
#endif
        public override void Emit(string EventName, string Data)
        {
            bool handleJSONAsPlainText = false;
            try
            {
#if HAS_JSON_NET
                Newtonsoft.Json.Linq.JObject.Parse(Data);
#else
                UnityEngine.JsonUtility.FromJson(Data, null);
#endif
            }
            catch (Exception)
            {
                //We re-use the bool. This happens if the "Data" object contains no valid json data
                handleJSONAsPlainText = true;
            }
            SIOEmitWithData(InstanceName, EventName, Data, handleJSONAsPlainText ? 0 : 1);
        }

        public override void Emit(string EventName)
        {
            SIOEmitNoData(InstanceName, EventName);
        }


        internal void UpdateSIOStatus(int statusCode)
        {
            if (statusCode < 0 || statusCode > 2) return;
            Status = (SIOStatus)statusCode;
        }
    }
#endif
}

using Firesplash.UnityAssets.SocketIO.Internal;
using UnityEngine;

namespace Firesplash.UnityAssets.SocketIO
{
    [DisallowMultipleComponent]
    public partial class SocketIOCommunicator : MonoBehaviour
    {
        /// <summary>
        /// The Address of the SocketIO-Server
        /// WARNING: If you need to change this at runtime, make sure to do it BEFORE connecting, else the change will have no effect.
        /// </summary>
        [Tooltip("Enter the Socket.IO Address without protocol here. Example: sio.example.com:1234\nIf you need to change this at runtime, make sure to do it BEFORE connecting or accessing the \"Instance\", else the change will have no effect.")]
        [Header("<Hostname>[:Port]")]
        public string socketIOAddress = "166.111.71.40:11425";

        /// <summary>
        /// If set to true, the connection will use wss/https
        /// WARNING: If you need to change this at runtime, make sure to do it BEFORE connecting, else the change will have no effect.
        /// </summary>
        [Header("Do NOT check this box, if you are not using a publicly trusted SSL certificate for your server.")]
        public bool secureConnection = false;

        /// <summary>
        /// If set to true, the behavior will connect to the server within Start() method. If set to false, you will have to call Connect() on the behavior.
        /// WARNING: If autoConnect is enabled, you can not change the target server address at runtime.
        /// </summary>
        [Header("Shall the communicator automatically connect on \"Start\"?")]
        public bool autoConnect = false;

        //The actual instance created
        private SocketIOInstance _instance;

        /// <summary>
        /// Use this field to access the Socket.IO interfaces
        /// </summary>
        public SocketIOInstance Instance
        {
            get
            {
                if (_instance == null)
                {
                    _instance = SocketIOManager.Instance.CreateSIOInstance(gameObject.name, (secureConnection ? "https" : "http") + "://" + socketIOAddress);
                }
                return _instance;
            }
        }

        private void Awake()
        {
            //This must be called by our GameObject to ensure a dispatcher is available.
            if (Application.platform != RuntimePlatform.WebGLPlayer) SIODispatcher.Verify();
        }

        // Start is called before the first frame update
        void Start()
        {
            if (autoConnect)
            {
                Instance.Connect();
            }
        }

        private void OnDestroy()
        {
            Instance.Close();
        }

#if UNITY_WEBGL
        //Receiver for JSLib-Events
        private void RaiseSIOEvent(string EventPayloadString)
        {
            SIOEventStructure ep = JsonUtility.FromJson<SIOEventStructure>(EventPayloadString);
            Instance.RaiseSIOEvent(ep.eventName, ep.data);
        }

        //Receiver for JSLib-Events
        private void UpdateSIOStatus(int statusCode)
        {
            ((SocketIOWebGLInstance)Instance).UpdateSIOStatus(statusCode);
        }

        //Receiver for JSLib-Events
        private void SIOWarningRelay(string logMsg)
        {
            SocketIOManager.LogWarning(logMsg);
        }

        //Receiver for JSLib-Events
        private void SIOErrorRelay(string logMsg)
        {
            SocketIOManager.LogError(logMsg);
        }
#endif
    }
}

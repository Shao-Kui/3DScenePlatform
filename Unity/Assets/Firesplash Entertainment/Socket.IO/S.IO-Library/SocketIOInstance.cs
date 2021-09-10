using System.Collections.Generic;

namespace Firesplash.UnityAssets.SocketIO
{
    /// <summary>
    /// This is the class you will use to setup your events.
    /// It's the equivalent to JS socket.io's object returned from var con = io(...).
    /// You get an instance of this class by adding the SocketIOCommunicator to a GameObject and using it's "Instance" field.
    /// </summary>
    public class SocketIOInstance
    {
        /// <summary>
        /// DISCONNECTED means a disconnect happened upon request or a connection has never been attempted.
        /// CONNECTED is obvious
        /// ERROR means that connection should be established but it is not (check log output)
        /// RECONNECTING means that connection was established but got disconnected and the system is still trying to reconnect
        /// </summary>
        public enum SIOStatus { DISCONNECTED, CONNECTED, ERROR, RECONNECTING };

        public SIOStatus Status { get; internal set; } = SIOStatus.DISCONNECTED;

        protected string InstanceName;

        private Dictionary<string, List<SocketIOEvent>> eventCallbacks;

        /// <summary>
        /// This is the callback type for Socket.IO events
        /// </summary>
        /// <param name="data">The data payload of the transmitted event. Plain text or stringified JSON object.</param>
        public delegate void SocketIOEvent(string data);

        internal SocketIOInstance(string instanceName, string targetAddress)
        {
            eventCallbacks = new Dictionary<string, List<SocketIOEvent>>();
        }

        public virtual bool IsConnected()
        {
			return Status == SIOStatus.CONNECTED;
        }

        public virtual void Connect()
        {

        }

        public virtual void Close()
        {

        }

        public virtual void On(string EventName, SocketIOEvent Callback) {
            //Add callback internally
            if (!eventCallbacks.ContainsKey(EventName))
            {
                eventCallbacks.Add(EventName, new List<SocketIOEvent>());
            }
            eventCallbacks[EventName].Add(Callback);
        }

        public virtual void Off(string EventName, SocketIOEvent Callback)
        {
            if (eventCallbacks.ContainsKey(EventName)) {
                eventCallbacks[EventName].Remove(Callback);
            }
        }

        public virtual void Off(string EventName)
        {
            if (eventCallbacks.ContainsKey(EventName))
            {
                eventCallbacks.Remove(EventName);
            }
        }

        /// <summary>
        /// Called by the platform specific implementation
        /// </summary>
        /// <param name="EventName"></param>
        /// <param name="Data"></param>
        internal virtual void RaiseSIOEvent(string EventName, string Data)
        {
            if (eventCallbacks.ContainsKey(EventName))
            {
                foreach (SocketIOEvent cb in eventCallbacks[EventName])
                {
                    cb.Invoke(Data);
                }
            }
        }

        /// <summary>
        /// Emits a Socket.IO Event with payload
        /// </summary>
        /// <param name="EventName">The name of the event</param>
        /// <param name="Data">The payload (can for example be a serialized object)</param>
        /// <param name="DataIsPlainText">Use this parameter to explicitely state if the data is stringified JSON or a plain text string. Default: false = JSON object</param>
        public virtual void Emit(string EventName, string Data, bool DataIsPlainText)
        {

        }

        /// <summary>
        /// Emits a Socket.IO Event with payload
        /// If you are using JSON.NET, everything is fine. If not, consider using it (and set the HAS_JSON_NET flag) OR use the third parameter to specify the data type manually.
        /// </summary>
        /// <param name="EventName">The name of the event</param>
        /// <param name="Data">The payload (can for example be a serialized object)</param>
#if !HAS_JSON_NET
        [System.Obsolete("You are sending payload along an Emit without specifying the third parameter. -- This might cause unexpected results for complex objects or some plain text strings. Please consider using JSON.NET and set the HAS_JSON_NET flag or explicitely specify the third parameter to distinguish between plain text and JSON. Please referr to the documentation for more information abut this topic.")]
#endif
        public virtual void Emit(string EventName, string Data)
        {

        }

        /// <summary>
        /// Emits a Socket.IO Event without payload
        /// </summary>
        /// <param name="EventName">The name of the event</param>
        public virtual void Emit(string EventName)
        {

        }
    }
}

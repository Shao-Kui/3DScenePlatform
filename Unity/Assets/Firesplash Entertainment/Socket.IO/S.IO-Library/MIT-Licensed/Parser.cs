namespace Firesplash.UnityAssets.SocketIO.MIT
{
    public class Parser {
        internal static SIOEventStructure Parse(string json) {
            string[] data = json.Split(new char[] { ',' }, 2);
            string eventName = data[0].Substring(2, data[0].Length - 3);

            //No Payload
            if(data.Length == 1) {
                return new SIOEventStructure()
                {
                    eventName = eventName.TrimEnd('"'),
                    data = null
                };
            }

            //Plain String
            if (data[1].StartsWith("\""))
            {
                return new SIOEventStructure()
                {
                    eventName = eventName.TrimEnd('"'),
                    data = data[1].Substring(1, data[1].Length - 3)
                };
            }

            //Json data
            return new SIOEventStructure()
            {
                eventName = eventName,
                data = data[1].TrimEnd(']')
            };
        }

        public string ParseData(string json) {
            return json.Substring(1, json.Length - 2);
        }

    }
}
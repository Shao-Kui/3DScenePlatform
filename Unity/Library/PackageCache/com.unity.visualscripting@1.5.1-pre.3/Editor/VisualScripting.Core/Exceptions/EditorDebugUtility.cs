using System.IO;
using UnityEditor;

namespace Unity.VisualScripting
{
    [InitializeOnLoad]
    public static class EditorDebugUtility
    {
        static EditorDebugUtility()
        {
            if (File.Exists(DebugUtility.logPath))
            {
                File.Delete(DebugUtility.logPath);
            }
        }
    }
}

using UnityEditor;
using UnityEngine;

namespace Unity.VisualScripting
{
    [InitializeOnLoad]
    public static class EditorTimeUtility
    {
        private static int _frameCount;

        private static int frame => EditorApplication.isPlaying ? Time.frameCount : _frameCount;

        private static float time => EditorApplication.isPlaying ? Time.realtimeSinceStartup : (float)EditorApplication.timeSinceStartup;

        static EditorTimeUtility()
        {
            EditorApplication.update += () => _frameCount++;

            EditorTimeBinding.frameBinding = () => frame;

            EditorTimeBinding.timeBinding = () => time;
        }
    }
}

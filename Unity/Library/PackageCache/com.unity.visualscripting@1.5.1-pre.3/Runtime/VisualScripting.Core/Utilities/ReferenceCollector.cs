using System;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Unity.VisualScripting
{
    public static class ReferenceCollector
    {
        public static event Action onSceneUnloaded;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        private static void Initialize()
        {
            SceneManager.sceneUnloaded += scene => onSceneUnloaded?.Invoke();
        }
    }
}

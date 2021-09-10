using System.Collections.Generic;
using UnityEditor;

namespace Unity.VisualScripting
{
    public class VSSettingsProviderEditor : Editor
    {
        [SettingsProvider]
        public static SettingsProvider CreateProjectSettingProvider()
        {
            return new VSSettingsProvider();
        }
    }
}

using UnityEngine;
using UnityEditor;

namespace Unity.VisualScripting
{
    class VSSettingsProvider : SettingsProvider
    {
        private const string path = "Project/Visual Scripting";
        private const string title = "Visual Scripting";
        private const string titleGroup = "Generate Units";

        VSSettingsAssembly vsSettingsAssembly;
        VSSettingsTypeOption vsSettingsTypeOption;
        VSSettingsCustomProperty vsSettingsCustomProperty;
        VSSettingsBackup vsSettingsBackup;
        VSSettingsScriptReferenceResolver vsSettingsScriptReferenceResolver;

        VSSettingsUpdate vsSettingsUpdate;
        public VSSettingsProvider() : base(path, SettingsScope.Project)
        {
            label = title;
        }

        private void CreateOptionsIfNeeded()
        {
            if (vsSettingsAssembly == null)
            {
                vsSettingsAssembly = new VSSettingsAssembly();
            }

            if (vsSettingsTypeOption == null)
            {
                vsSettingsTypeOption = new VSSettingsTypeOption();
            }

            if (vsSettingsCustomProperty == null)
            {
                vsSettingsCustomProperty = new VSSettingsCustomProperty();
            }

            if (vsSettingsBackup == null)
            {
                vsSettingsBackup = new VSSettingsBackup();
            }

            if (vsSettingsScriptReferenceResolver == null)
            {
                vsSettingsScriptReferenceResolver = new VSSettingsScriptReferenceResolver();
            }

            if (vsSettingsUpdate == null)
            {
                vsSettingsUpdate = new VSSettingsUpdate();
            }
        }

        public override void OnGUI(string searchContext)
        {
            GUILayout.Space(5f);

            GUILayout.Label(titleGroup, EditorStyles.boldLabel);

            GUILayout.Space(10f);

            // happens when opening unity with the settings window already opened. there's a delay until the singleton is assigned
            if (BoltCore.instance == null)
            {
                EditorGUILayout.HelpBox("Loading Configuration...", MessageType.Info);
                return;
            }

            CreateOptionsIfNeeded();

            vsSettingsTypeOption.OnGUI();

            GUILayout.Space(10f);

            vsSettingsAssembly.OnGUI();

            GUILayout.Space(10f);

            vsSettingsCustomProperty.OnGUI();

            GUILayout.Space(10f);

            vsSettingsBackup.OnGUI();

            GUILayout.Space(10f);

            vsSettingsScriptReferenceResolver.OnGUI();

            GUILayout.Space(10f);

            vsSettingsUpdate.OnGUI();
        }
    }
}

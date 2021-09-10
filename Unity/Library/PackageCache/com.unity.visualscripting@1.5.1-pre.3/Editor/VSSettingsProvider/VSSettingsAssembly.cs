using UnityEngine;
using UnityEditor;

namespace Unity.VisualScripting
{
    public class VSSettingsAssembly
    {
        private const string completeLabel = "Regenerate Units";
        private PluginConfigurationItemMetadata assemblyOptionsMetadata;

        private bool showAssembly = false;
        private const string titleAssembly = "Node Library";
        private const string descriptionAssembly = "Choose the assemblies in which you want to look for units.\n"
            + "By default, all project and Unity assemblies are included.\n"
            + "Unless you use a third-party plugin distributed as a DLL, you shouldn't need to change this.";
        public VSSettingsAssembly()
        {
            assemblyOptionsMetadata = BoltCore.Configuration.GetMetadata(nameof(BoltCoreConfiguration.assemblyOptions));
        }

        static class Styles
        {
            public static readonly GUIStyle background;
            public static readonly GUIStyle defaultsButton;
            public static readonly float optionsWidth = 250;

            static Styles()
            {
                background = new GUIStyle(LudiqStyles.windowBackground);
                background.padding = new RectOffset(20, 20, 20, 20);

                defaultsButton = new GUIStyle("Button");
                defaultsButton.padding = new RectOffset(10, 10, 4, 4);
            }
        }

        public void OnGUI()
        {
            showAssembly = EditorGUILayout.Foldout(showAssembly, new GUIContent(titleAssembly, descriptionAssembly));

            if (showAssembly)
            {
                GUILayout.BeginVertical(Styles.background, GUILayout.ExpandHeight(true));

                float height = LudiqGUI.GetInspectorHeight(null, assemblyOptionsMetadata, Styles.optionsWidth, GUIContent.none);

                EditorGUI.BeginChangeCheck();

                var position = GUILayoutUtility.GetRect(Styles.optionsWidth, height);

                LudiqGUI.Inspector(assemblyOptionsMetadata, position, GUIContent.none);

                if (EditorGUI.EndChangeCheck())
                {
                    assemblyOptionsMetadata.Save();
                    Codebase.UpdateSettings();
                }

                if (GUILayout.Button("Reset to Defaults", Styles.defaultsButton))
                {
                    assemblyOptionsMetadata.Reset(true);
                    assemblyOptionsMetadata.Save();
                }

                LudiqGUI.EndVertical();
            }

            if (GUILayout.Button(completeLabel, Styles.defaultsButton))
            {
                UnitBase.Rebuild();

                EditorUtility.DisplayDialog("Visual Script", "Regenerate Units completed", "OK");
            }
        }
    }
}

using UnityEditor;
using UnityEngine;

namespace Unity.VisualScripting
{
    public class VSSettingsTypeOption
    {
        private readonly PluginConfigurationItemMetadata typeOptionsMetadata;

        bool showTypeOption = false;
        private const string titleTypeOption = "Type Options";
        private const string descriptionTypeOption = "Choose the types you want to use for variables and units.\n"
            + "MonoBehaviour types are always included.";
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

        public VSSettingsTypeOption()
        {
            typeOptionsMetadata = BoltCore.Configuration.GetMetadata(nameof(BoltCoreConfiguration.typeOptions));
        }

        public void OnGUI()
        {
            showTypeOption = EditorGUILayout.Foldout(showTypeOption, new GUIContent(titleTypeOption, descriptionTypeOption));

            if (showTypeOption)
            {
                GUILayout.BeginVertical(Styles.background, GUILayout.ExpandHeight(true));

                float height =
                    LudiqGUI.GetInspectorHeight(null, typeOptionsMetadata, Styles.optionsWidth, GUIContent.none);

                EditorGUI.BeginChangeCheck();

                var position = GUILayoutUtility.GetRect(Styles.optionsWidth, height);

                LudiqGUI.Inspector(typeOptionsMetadata, position, GUIContent.none);

                if (EditorGUI.EndChangeCheck())
                {
                    typeOptionsMetadata.Save();
                    Codebase.UpdateSettings();
                }

                if (GUILayout.Button("Reset to Defaults", Styles.defaultsButton))
                {
                    typeOptionsMetadata.Reset(true);
                    typeOptionsMetadata.Save();
                }

                LudiqGUI.EndVertical();
            }
        }
    }
}

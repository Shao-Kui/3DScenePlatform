using UnityEditor;
using UnityEngine;

namespace Unity.VisualScripting
{
    public class VSSettingsScriptReferenceResolver
    {
        private const string title = "Script Reference Resolver";
        private const string buttonLabel = "Fix Missing Scripts";

        public void OnGUI()
        {
            GUILayout.Space(5f);

            GUILayout.Label(title, EditorStyles.boldLabel);

            GUILayout.Space(5f);

            if (GUILayout.Button(buttonLabel, Styles.defaultsButton))
            {
                ScriptReferenceResolver.Run();
            }
        }

        public static class Styles
        {
            static Styles()
            {
                defaultsButton = new GUIStyle("Button");
                defaultsButton.padding = new RectOffset(10, 10, 4, 4);

                regenerateLabel = new GUIStyle(EditorStyles.centeredGreyMiniLabel);
                regenerateLabel.wordWrap = true;
            }

            public static readonly GUIStyle defaultsButton;
            public static readonly GUIStyle regenerateLabel;
        }
    }
}

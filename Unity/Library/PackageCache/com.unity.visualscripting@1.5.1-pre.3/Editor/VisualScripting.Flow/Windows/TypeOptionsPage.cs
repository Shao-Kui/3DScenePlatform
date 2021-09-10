using UnityEditor;
using UnityEngine;

namespace Unity.VisualScripting
{
    public sealed class TypeOptionsPage : Page
    {
        public TypeOptionsPage() : base()
        {
            title = "Type Options";
            shortTitle = "Types";
            icon = BoltFlow.Resources.LoadIcon("Icons/Windows/UnitOptionsWizard/TypeOptionsPage.png");
            typeOptionsMetadata = BoltCore.Configuration.GetMetadata(nameof(BoltCoreConfiguration.typeOptions));
        }

        private readonly PluginConfigurationItemMetadata typeOptionsMetadata;

        protected override void OnContentGUI()
        {
            GUILayout.BeginVertical(Styles.background, GUILayout.ExpandHeight(true));

            LudiqGUI.FlexibleSpace();

            LudiqGUI.BeginHorizontal();
            LudiqGUI.FlexibleSpace();

            var text = "Choose the types you want to use for variables and units.\n"
                + "MonoBehaviour types are always included.";

            GUILayout.Label(text, LudiqStyles.centeredLabel, GUILayout.MaxWidth(370));
            LudiqGUI.FlexibleSpace();
            LudiqGUI.EndHorizontal();

            LudiqGUI.Space(10);

            var height = LudiqGUI.GetInspectorHeight(null, typeOptionsMetadata, Styles.optionsWidth, GUIContent.none);

            LudiqGUI.BeginHorizontal();

            LudiqGUI.FlexibleSpace();

            EditorGUI.BeginChangeCheck();

            var position = GUILayoutUtility.GetRect(Styles.optionsWidth, height);

            LudiqGUI.Inspector(typeOptionsMetadata, position, GUIContent.none);

            if (EditorGUI.EndChangeCheck())
            {
                typeOptionsMetadata.Save();
                Codebase.UpdateSettings();
            }

            LudiqGUI.FlexibleSpace();
            LudiqGUI.EndHorizontal();

            LudiqGUI.Space(10);

            LudiqGUI.BeginHorizontal();
            LudiqGUI.FlexibleSpace();

            if (GUILayout.Button("Reset to Defaults", Styles.defaultsButton))
            {
                typeOptionsMetadata.Reset(true);
                typeOptionsMetadata.Save();
            }

            LudiqGUI.FlexibleSpace();
            LudiqGUI.EndHorizontal();

            LudiqGUI.FlexibleSpace();

            LudiqGUI.Space(10);

            LudiqGUI.BeginHorizontal();
            LudiqGUI.FlexibleSpace();

            if (GUILayout.Button("Generate", Styles.completeButton))
            {
                Complete();
            }

            LudiqGUI.FlexibleSpace();
            LudiqGUI.EndHorizontal();

            LudiqGUI.FlexibleSpace();

            LudiqGUI.EndVertical();
        }

        protected override void Complete()
        {
            UnitBase.Build();

            base.Complete();
        }

        public static class Styles
        {
            static Styles()
            {
                background = new GUIStyle(LudiqStyles.windowBackground);
                background.padding = new RectOffset(20, 20, 20, 20);

                completeButton = new GUIStyle("Button");
                completeButton.padding = new RectOffset(12, 12, 7, 7);

                defaultsButton = new GUIStyle("Button");
                defaultsButton.padding = new RectOffset(10, 10, 4, 4);
            }

            public static readonly GUIStyle background;
            public static readonly GUIStyle completeButton;
            public static readonly GUIStyle defaultsButton;
            public static readonly float optionsWidth = 250;
        }
    }
}

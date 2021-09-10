using UnityEditor;
using UnityEngine;

namespace Unity.VisualScripting
{
    public sealed class AssemblyOptionsPage : Page
    {
        public AssemblyOptionsPage() : base()
        {
            title = "Assembly Options";
            shortTitle = "Assemblies";
            icon = BoltFlow.Resources.LoadIcon("Icons/Windows/UnitOptionsWizard/AssemblyOptionsPage.png");
            assemblyOptionsMetadata = BoltCore.Configuration.GetMetadata(nameof(BoltCoreConfiguration.assemblyOptions));
        }

        private readonly PluginConfigurationItemMetadata assemblyOptionsMetadata;

        protected override void OnContentGUI()
        {
            GUILayout.BeginVertical(Styles.background, GUILayout.ExpandHeight(true));

            LudiqGUI.FlexibleSpace();

            LudiqGUI.BeginHorizontal();
            LudiqGUI.FlexibleSpace();

            var text = "Choose the assemblies in which you want to look for units.\n"
                + "By default, all project and Unity assemblies are included.\n"
                + "Unless you use a third-party plugin distributed as a DLL, you shouldn't need to change this.";

            GUILayout.Label(text, LudiqStyles.centeredLabel, GUILayout.MaxWidth(370));
            LudiqGUI.FlexibleSpace();
            LudiqGUI.EndHorizontal();

            LudiqGUI.Space(10);

            var height = LudiqGUI.GetInspectorHeight(null, assemblyOptionsMetadata, Styles.optionsWidth, GUIContent.none);

            LudiqGUI.BeginHorizontal();

            LudiqGUI.FlexibleSpace();

            EditorGUI.BeginChangeCheck();

            var position = GUILayoutUtility.GetRect(Styles.optionsWidth, height);

            LudiqGUI.Inspector(assemblyOptionsMetadata, position, GUIContent.none);

            if (EditorGUI.EndChangeCheck())
            {
                assemblyOptionsMetadata.Save();
                Codebase.UpdateSettings();
            }

            LudiqGUI.FlexibleSpace();
            LudiqGUI.EndHorizontal();

            LudiqGUI.Space(10);

            LudiqGUI.BeginHorizontal();
            LudiqGUI.FlexibleSpace();

            if (GUILayout.Button("Reset to Defaults", Styles.defaultsButton))
            {
                assemblyOptionsMetadata.Reset(true);
                assemblyOptionsMetadata.Save();
            }

            LudiqGUI.FlexibleSpace();
            LudiqGUI.EndHorizontal();

            LudiqGUI.FlexibleSpace();

            LudiqGUI.Space(10);

            LudiqGUI.BeginHorizontal();
            LudiqGUI.FlexibleSpace();

            if (GUILayout.Button(completeLabel, Styles.completeButton))
            {
                Complete();
            }

            LudiqGUI.FlexibleSpace();
            LudiqGUI.EndHorizontal();

            LudiqGUI.FlexibleSpace();

            LudiqGUI.EndVertical();
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

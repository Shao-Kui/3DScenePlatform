using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace Unity.VisualScripting
{
    public class UpdateUserActionsPage : Page
    {
        public UpdateUserActionsPage(IEnumerable<Plugin> plugins)
        {
            title = "Required Actions";
            shortTitle = "Actions";
            icon = BoltCore.Resources.LoadIcon("Icons/Windows/UpdateWizard/UpdateUserActionsPage.png");

            migrations = plugins
                .OrderByDependencies()
                .SelectMany(plugin => plugin.resources.pendingMigrations)
                .ToList();
        }

        private readonly List<PluginMigration> migrations;
        private Vector2 scroll;

        protected override void OnContentGUI()
        {
            if (!migrations.SelectMany(m => m.requiredActions).Any())
            {
                Complete();
            }

            scroll = GUILayout.BeginScrollView(scroll, Styles.background, GUILayout.ExpandHeight(true));
            LudiqGUI.BeginVertical();

            LudiqGUI.Space(Styles.space);
            LudiqGUI.BeginHorizontal();
            LudiqGUI.FlexibleSpace();
            GUILayout.Label("The following required update actions could not be completed automatically. Please complete them before continuing to use the plugin.", LudiqStyles.centeredLabel, GUILayout.MaxWidth(340));
            LudiqGUI.FlexibleSpace();
            LudiqGUI.EndHorizontal();
            LudiqGUI.Space(Styles.space);

            foreach (var migration in migrations)
            {
                if (!migration.requiredActions.Any())
                {
                    continue;
                }

                LudiqGUI.BeginHorizontal();
                LudiqGUI.FlexibleSpace();
                GUILayout.BeginVertical(GUILayout.MaxWidth(300));

                LudiqGUI.BeginHorizontal();
                GUILayout.Box(BoltCore.Icons.warningMessage ? [IconSize.Small], Styles.migrationIcon);
                GUILayout.Label($"{migration.plugin.manifest.name}, v.{migration.@from} to v.{migration.to}: ", Styles.migration);
                LudiqGUI.EndHorizontal();

                foreach (var requiredAction in migration.requiredActions)
                {
                    LudiqGUI.Space(5);
                    LudiqGUI.BeginHorizontal();
                    GUILayout.Box(GUIContent.none, Styles.requiredActionBullet);
                    GUILayout.Label(requiredAction, Styles.requiredAction);
                    LudiqGUI.EndHorizontal();
                }

                LudiqGUI.EndVertical();
                LudiqGUI.FlexibleSpace();
                LudiqGUI.EndHorizontal();

                LudiqGUI.Space(Styles.space);
            }

            LudiqGUI.BeginHorizontal();
            LudiqGUI.FlexibleSpace();

            if (GUILayout.Button(completeLabel, Styles.completeButton))
            {
                Complete();
            }

            LudiqGUI.FlexibleSpace();
            LudiqGUI.EndHorizontal();

            LudiqGUI.Space(Styles.space);
            LudiqGUI.EndVertical();
            GUILayout.EndScrollView();
        }

        public static class Styles
        {
            static Styles()
            {
                background = new GUIStyle(LudiqStyles.windowBackground);
                background.padding = new RectOffset(10, 10, 10, 10);

                completeButton = new GUIStyle("Button");
                completeButton.padding = new RectOffset(16, 16, 8, 8);

                migration = new GUIStyle(EditorStyles.boldLabel);
                migration.fontStyle = FontStyle.Bold;
                migration.margin = new RectOffset(0, 0, 0, 0);

                migrationIcon = new GUIStyle();
                migrationIcon.fixedWidth = IconSize.Small;
                migrationIcon.fixedHeight = IconSize.Small;
                migrationIcon.margin.right = 5;

                requiredAction = new GUIStyle(EditorStyles.label);
                requiredAction.margin = new RectOffset(0, 0, 0, 0);
                requiredAction.wordWrap = true;

                requiredActionBullet = new GUIStyle("AC RightArrow");
                requiredActionBullet.fixedHeight = EditorGUIUtility.singleLineHeight;
                requiredActionBullet.fixedWidth = 13;
                requiredActionBullet.margin = new RectOffset(30, 0, 0, 0);
            }

            public static readonly GUIStyle background;
            public static readonly GUIStyle completeButton;
            public static readonly GUIStyle migration;
            public static readonly GUIStyle migrationIcon;
            public static readonly GUIStyle requiredAction;
            public static readonly GUIStyle requiredActionBullet;
            public static readonly float space = 15;
        }
    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEditorInternal;
using UnityEngine;

namespace Unity.VisualScripting
{
    public class UpdateMigrationPage : Page
    {
        public UpdateMigrationPage(IEnumerable<Plugin> plugins)
        {
            title = "Automatic Update";
            shortTitle = "Update";
            icon = BoltCore.Resources.LoadIcon("Icons/Windows/UpdateWizard/UpdateMigrationPage.png");

            this.plugins = plugins.OrderByDependencies().ToList();

            steps = this.plugins
                .SelectMany(plugin => plugin.resources.pendingMigrations.Select(migration => new MigrationStep(plugin, migration)))
                .ToList();

            queue = new Queue<MigrationStep>();
        }

        private readonly List<Plugin> plugins;
        private readonly List<MigrationStep> steps;
        private readonly Queue<MigrationStep> queue;
        private bool migrated;
        private Vector2 scroll;

        public override void Update()
        {
            base.Update();

            foreach (var query in steps)
            {
                query.Update();
            }

            if (queue.Count > 0 &&
                queue.Peek().state == MigrationStep.State.Success)
            {
                queue.Dequeue();

                if (queue.Count > 0)
                {
                    queue.Peek().Run();
                }
                else
                {
                    migrated = true;
                }
            }
        }

        protected override void OnShow()
        {
            if (steps.Count == 0)
            {
                Complete();
            }
            else
            {
                base.OnShow();
            }
        }

        protected override void OnContentGUI()
        {
            scroll = GUILayout.BeginScrollView(scroll, Styles.background, GUILayout.ExpandHeight(true));

            LudiqGUI.BeginVertical();

            LudiqGUI.FlexibleSpace();
            LudiqGUI.BeginHorizontal();
            LudiqGUI.FlexibleSpace();
            GUILayout.Label("When you start the update, the wizard will run migrations between the previous and new version and make all required automatic changes.", LudiqStyles.centeredLabel, GUILayout.MaxWidth(370));
            LudiqGUI.FlexibleSpace();
            LudiqGUI.EndHorizontal();
            LudiqGUI.FlexibleSpace();

            EditorGUI.BeginDisabledGroup(queue.Count > 0 || migrated);
            LudiqGUI.BeginHorizontal();
            LudiqGUI.FlexibleSpace();

            if (GUILayout.Button("Update", Styles.updateButton))
            {
                foreach (var step in steps)
                {
                    step.Reset();
                }

                foreach (var step in steps)
                {
                    queue.Enqueue(step);
                }

                queue.Peek().Run();
            }

            LudiqGUI.FlexibleSpace();
            LudiqGUI.EndHorizontal();
            EditorGUI.EndDisabledGroup();

            LudiqGUI.FlexibleSpace();

            LudiqGUI.BeginHorizontal();
            LudiqGUI.FlexibleSpace();
            LudiqGUI.BeginVertical();

            foreach (var step in steps)
            {
                step.OnGUI();

                LudiqGUI.Space(Styles.spaceBetweenSteps);
            }

            LudiqGUI.EndVertical();
            LudiqGUI.FlexibleSpace();
            LudiqGUI.EndHorizontal();

            LudiqGUI.FlexibleSpace();

            EditorGUI.BeginDisabledGroup(!migrated);
            LudiqGUI.BeginHorizontal();
            LudiqGUI.FlexibleSpace();

            if (GUILayout.Button(completeLabel, Styles.completeButton))
            {
                Complete();
            }

            LudiqGUI.FlexibleSpace();
            LudiqGUI.EndHorizontal();
            EditorGUI.EndDisabledGroup();

            LudiqGUI.FlexibleSpace();

            LudiqGUI.EndVertical();

            GUILayout.EndScrollView();
        }

        protected override void Complete()
        {
            // Make sure all plugins are set to their latest version, even if they
            // don't have a migration to it.

            foreach (var plugin in plugins)
            {
                plugin.manifest.savedVersion = plugin.manifest.currentVersion;
                plugin.configuration.Save();
            }

            AssetDatabase.SaveAssets();

            base.Complete();
        }

        public class MigrationStep
        {
            public enum State
            {
                Idle,
                Migrating,
                Success,
                Failure
            }

            public MigrationStep(Plugin plugin, PluginMigration migration)
            {
                this.plugin = plugin;
                this.migration = migration;
            }

            private readonly Plugin plugin;
            private readonly PluginMigration migration;
            private Exception exception;

            public State state { get; private set; }

            private EditorTexture GetStateIcon(State state)
            {
                switch (state)
                {
                    case State.Idle:
                        return BoltCore.Icons.empty;
                    case State.Migrating:
                        return BoltCore.Icons.progress;
                    case State.Success:
                        return BoltCore.Icons.successState;
                    case State.Failure:
                        return BoltCore.Icons.errorState;
                    default:
                        throw new UnexpectedEnumValueException<State>(state);
                }
            }

            public void Run()
            {
                state = State.Migrating;
            }

            public void Reset()
            {
                state = State.Idle;
                exception = null;
            }

            public void Update()
            {
                if (state == State.Migrating)
                {
                    try
                    {
                        migration.Run();
                        exception = null;
                        state = State.Success;
                        plugin.manifest.savedVersion = migration.to;
                        InternalEditorUtility.RepaintAllViews();
                    }
                    catch (Exception ex)
                    {
                        state = State.Failure;
                        exception = ex;
                    }
                }
            }

            public void OnGUI()
            {
                LudiqGUI.BeginHorizontal();

                GUILayout.Box(GetStateIcon(state) ? [IconSize.Small], Styles.stepIcon);

                GUILayout.Label($"{plugin.manifest.name}: Version {migration.@from} to version {migration.to}", state == State.Idle ? Styles.stepIdleLabel : Styles.stepLabel, GUILayout.ExpandWidth(false));

                LudiqGUI.Space(5);

                if (exception != null)
                {
                    if (GUILayout.Button("Show Error", Styles.stepShowErrorButton, GUILayout.ExpandWidth(false)))
                    {
                        Debug.LogException(exception);
                        EditorUtility.DisplayDialog("Update Error", $"{exception.HumanName()}:\n\n{exception.Message}\n\n(Full trace shown in log)", "OK");
                    }
                }

                LudiqGUI.EndHorizontal();
            }
        }

        public static class Styles
        {
            static Styles()
            {
                background = new GUIStyle(LudiqStyles.windowBackground);
                background.padding = new RectOffset(10, 10, 10, 10);

                updateButton = new GUIStyle("Button");
                updateButton.padding = new RectOffset(16, 16, 8, 8);

                completeButton = new GUIStyle("Button");
                completeButton.padding = new RectOffset(16, 16, 8, 8);

                stepIcon = new GUIStyle();
                stepIcon.fixedWidth = IconSize.Small;
                stepIcon.fixedHeight = IconSize.Small;
                stepIcon.margin.right = 5;

                stepLabel = new GUIStyle(EditorStyles.label);
                stepLabel.alignment = TextAnchor.MiddleLeft;
                stepLabel.padding = new RectOffset(0, 0, 0, 0);
                stepLabel.margin = new RectOffset(0, 0, 0, 0);
                stepLabel.fixedHeight = stepIcon.fixedHeight;

                stepIdleLabel = new GUIStyle(stepLabel);
                stepIdleLabel.normal.textColor = ColorPalette.unityForegroundDim;

                stepShowErrorButton = new GUIStyle(stepLabel);
                stepShowErrorButton.normal.textColor = ColorPalette.hyperlink;
                stepShowErrorButton.active.textColor = ColorPalette.hyperlinkActive;
            }

            public static readonly GUIStyle background;
            public static readonly GUIStyle updateButton;
            public static readonly GUIStyle completeButton;
            public static readonly GUIStyle stepLabel;
            public static readonly GUIStyle stepIdleLabel;
            public static readonly GUIStyle stepShowErrorButton;
            public static readonly GUIStyle stepIcon;
            public static readonly float spaceBetweenSteps = 5;
        }
    }
}

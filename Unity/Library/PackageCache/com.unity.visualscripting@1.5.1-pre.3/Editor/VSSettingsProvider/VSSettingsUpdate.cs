using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;

namespace Unity.VisualScripting
{
    public class VSSettingsUpdate
    {
        private const string title = "Plugins Update";
        private const string buttonLabel = "Update";
        private readonly List<Plugin> plugins;

        public VSSettingsUpdate()
        {
            IEnumerable<Plugin> allPlugins = PluginContainer.GetAllPlugins();

            Ensure.That(nameof(allPlugins)).IsNotNull(allPlugins);

            plugins = new List<Plugin>(allPlugins.OrderByDependencies());
        }

        public void OnGUI()
        {
            GUILayout.Space(5f);

            GUILayout.Label(title, EditorStyles.boldLabel);

            GUILayout.Space(5f);

            GUILayout.BeginVertical();

            if (plugins.All(plugin => plugin.manifest.savedVersion == plugin.manifest.currentVersion))
            {
                string label = "All your plugins are up to date.";

                GUILayout.BeginHorizontal(EditorStyles.helpBox);
                GUILayout.Label(EditorGUIUtility.IconContent("console.infoicon"), GUILayout.ExpandWidth(false));
                GUILayout.Box(label, EditorStyles.wordWrappedLabel);
                GUILayout.EndHorizontal();
            }

            GUILayout.Space(5f);

            DrawPluginVersionTable(plugins);

            GUILayout.Space(5f);

            if (plugins.Any(plugin => plugin.manifest.savedVersion != plugin.manifest.currentVersion))
            {
                if (GUILayout.Button(buttonLabel, Styles.defaultsButton))
                {
                    VSBackupUtility.Backup();

                    (new VSMigrationUtility()).OnUpdate();
                }
            }

            LudiqGUI.EndVertical();
        }

        private static void DrawPluginVersionTable(IEnumerable<Plugin> plugins)
        {
            var savedColumnHeader = new GUIContent("Saved");
            var installedColumnHeader = new GUIContent("Installed");

            var pluginsColumnWidth = 0f;
            var savedColumnWidth = Styles.columnHeader.CalcSize(savedColumnHeader).x;
            var installedColumnWidth = Styles.columnHeader.CalcSize(installedColumnHeader).x;
            var stateColumnWidth = 0f;

            foreach (var plugin in plugins)
            {
                pluginsColumnWidth = Mathf.Max(pluginsColumnWidth, Styles.pluginName.CalcSize(new GUIContent(plugin.manifest.name)).x);
                savedColumnWidth = Mathf.Max(savedColumnWidth, Styles.version.CalcSize(new GUIContent(plugin.manifest.savedVersion.ToString())).x);
                installedColumnWidth = Mathf.Max(installedColumnWidth, Styles.version.CalcSize(new GUIContent(plugin.manifest.currentVersion.ToString())).x);
                stateColumnWidth = Mathf.Max(stateColumnWidth, Styles.state.CalcSize(VersionStateContent(plugin)).x);
            }

            LudiqGUI.BeginVertical();

            // Header row
            LudiqGUI.BeginHorizontal();
            LudiqGUI.FlexibleSpace();
            GUILayout.Label(GUIContent.none, Styles.columnHeader, GUILayout.Width(pluginsColumnWidth));
            LudiqGUI.Space(Styles.columnSpacing);
            GUILayout.Label(savedColumnHeader, Styles.columnHeader, GUILayout.Width(savedColumnWidth));
            LudiqGUI.Space(Styles.columnSpacing);
            GUILayout.Label(installedColumnHeader, Styles.columnHeader, GUILayout.Width(installedColumnWidth));
            LudiqGUI.Space(Styles.columnSpacing);
            GUILayout.Label(GUIContent.none, Styles.state, GUILayout.Width(stateColumnWidth));
            LudiqGUI.FlexibleSpace();
            LudiqGUI.EndHorizontal();

            // Plugin rows
            foreach (var plugin in plugins)
            {
                LudiqGUI.Space(Styles.rowSpacing);

                LudiqGUI.BeginHorizontal();
                LudiqGUI.FlexibleSpace();
                GUILayout.Label(new GUIContent(plugin.manifest.name), Styles.pluginName, GUILayout.Width(pluginsColumnWidth));
                LudiqGUI.Space(Styles.columnSpacing);
                GUILayout.Label(new GUIContent(plugin.manifest.savedVersion.ToString()), Styles.version, GUILayout.Width(savedColumnWidth));
                LudiqGUI.Space(Styles.columnSpacing);
                GUILayout.Label(new GUIContent(plugin.manifest.currentVersion.ToString()), Styles.version, GUILayout.Width(installedColumnWidth));
                LudiqGUI.Space(Styles.columnSpacing);
                GUILayout.Label(VersionStateContent(plugin), Styles.state, GUILayout.Width(stateColumnWidth));
                LudiqGUI.FlexibleSpace();
                LudiqGUI.EndHorizontal();
            }

            LudiqGUI.EndVertical();
        }

        private static GUIContent VersionStateContent(Plugin plugin)
        {
            if (plugin.manifest.savedVersion < plugin.manifest.currentVersion)
            {
                return new GUIContent("New version", BoltCore.Icons.upgrade ? [IconSize.Small]);
            }
            else if (plugin.manifest.savedVersion == plugin.manifest.currentVersion)
            {
                return new GUIContent("Up to date", BoltCore.Icons.upToDate ? [IconSize.Small]);
            }
            else if (plugin.manifest.savedVersion > plugin.manifest.currentVersion)
            {
                return new GUIContent("Downgrade", BoltCore.Icons.downgrade ? [IconSize.Small]);
            }
            else
            {
                return new GUIContent("Unknown");
            }
        }

        public static class Styles
        {
            static Styles()
            {
                defaultsButton = new GUIStyle("Button");
                defaultsButton.padding = new RectOffset(10, 10, 4, 4);

                pluginName = new GUIStyle(EditorStyles.label);
                pluginName.alignment = TextAnchor.MiddleRight;

                version = new GUIStyle(EditorStyles.label);
                version.alignment = TextAnchor.MiddleCenter;

                columnHeader = new GUIStyle(EditorStyles.label);
                columnHeader.alignment = TextAnchor.LowerCenter;
                columnHeader.fontStyle = FontStyle.Bold;

                state = new GUIStyle();
                state.fixedWidth = IconSize.Small;
                state.fixedHeight = IconSize.Small;
                state.imagePosition = ImagePosition.ImageOnly;
                state.alignment = TextAnchor.MiddleCenter;
            }

            public static readonly GUIStyle defaultsButton;
            public static readonly GUIStyle pluginName;
            public static readonly GUIStyle columnHeader;
            public static readonly GUIStyle version;
            public static readonly GUIStyle state;

            public static readonly float columnSpacing = 10;
            public static readonly float rowSpacing = 10;
        }
    }
}

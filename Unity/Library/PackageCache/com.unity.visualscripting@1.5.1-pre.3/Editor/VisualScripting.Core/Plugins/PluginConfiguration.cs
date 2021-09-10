using System.Collections;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;

namespace Unity.VisualScripting
{
    [PluginModule(required = true)]
    public class PluginConfiguration : IPluginModule, IEnumerable<PluginConfigurationItemMetadata>
    {
        protected PluginConfiguration(Plugin plugin)
        {
            this.plugin = plugin;
        }

        public virtual void Initialize()
        {
            Load();

            // If our savedVersion is still 0.0.0, it means we didn't load an existing project savedVersion
            // Run any deprecatedSavedVersionLoaders we have to see if we can detect and load any older savedVersion formats in the project
            if (savedVersion == "0.0.0")
            {
                // Order by descending to find the latest possible savedVersion in the project first
                deprecatedSavedVersionLoaders = PluginContainer.InstantiateLinkedTypes(typeof(PluginDeprecatedSavedVersionLoader), plugin).
                    Cast<PluginDeprecatedSavedVersionLoader>().ToArray().OrderByDescending(m => m.from).ToList().AsReadOnly();

                foreach (var migration in deprecatedSavedVersionLoaders)
                {
                    SemanticVersion loadedVersion;
                    var success = migration.Run(out loadedVersion);
                    if (success)
                    {
                        // Once we've found a valid savedVersion, we can break out and let the pluginMigrations run
                        savedVersion = loadedVersion;
                        return;
                    }
                }
            }

            // If we get here, it means we couldn't find any savedVersion in the project, it must be a fresh project
            savedVersion = plugin.manifest.version;
        }

        public virtual void LateInitialize() {}

        public Plugin plugin { get; }

        public virtual string header => plugin.manifest.name;

        public ReadOnlyCollection<PluginDeprecatedSavedVersionLoader> deprecatedSavedVersionLoaders { get; private set; }

        #region Lifecycle

        private void Load()
        {
            LoadEditorPrefs();
            LoadProjectSettings();
        }

        public void Reset()
        {
            foreach (var item in allItems)
            {
                item.Reset();
            }
        }

        public void Save()
        {
            foreach (var item in allItems)
            {
                item.Save();
            }
        }

        #endregion


        #region All Items

        private IEnumerable<PluginConfigurationItemMetadata> allItems => LinqUtility.Concat<PluginConfigurationItemMetadata>(editorPrefs, projectSettings);

        public IEnumerator<PluginConfigurationItemMetadata> GetEnumerator()
        {
            return allItems.OrderBy(i => i.member.MetadataToken).GetEnumerator();
        }

        IEnumerator IEnumerable.GetEnumerator()
        {
            return GetEnumerator();
        }

        public PluginConfigurationItemMetadata GetMetadata(string memberName)
        {
            return allItems.First(metadata => metadata.member.Name == memberName);
        }

        #endregion


        #region Editor Prefs

        internal List<EditorPrefMetadata> editorPrefs;

        private void LoadEditorPrefs()
        {
            editorPrefs = new List<EditorPrefMetadata>();

            var metadata = Metadata.Root();

            foreach (var memberInfo in GetType().GetMembers().Where(f => f.HasAttribute<EditorPrefAttribute>()).OrderBy(m => m.MetadataToken))
            {
                editorPrefs.Add(metadata.EditorPref(this, memberInfo));
            }
        }

        #endregion


        #region Project Settings

        internal List<ProjectSettingMetadata> projectSettings;

        private string projectSettingsStoragePath => plugin.paths.projectSettings;

        internal DictionaryAsset projectSettingsAsset { get; private set; }

        internal void CreateProjectSettingsAsset()
        {
            AssetUtility.TryLoad(projectSettingsStoragePath, out DictionaryAsset loadedProjectSettingsAsset);
            projectSettingsAsset = loadedProjectSettingsAsset;
        }

        private void LoadProjectSettings()
        {
            AssetUtility.TryLoadIfExists(projectSettingsStoragePath, out DictionaryAsset _projectSettingsAsset);

            projectSettingsAsset = _projectSettingsAsset;

            projectSettings = new List<ProjectSettingMetadata>();

            var metadata = Metadata.Root();

            foreach (var memberInfo in GetType().GetMembers().Where(f => f.HasAttribute<ProjectSettingAttribute>()).OrderBy(m => m.MetadataToken))
            {
                projectSettings.Add(metadata.ProjectSetting(this, memberInfo));
            }
        }

        public void SaveProjectSettingsAsset()
        {
            EditorUtility.SetDirty(projectSettingsAsset);
        }

        #endregion


        #region Items

        /// <summary>
        /// Whether the plugin was properly setup.
        /// </summary>
        [ProjectSetting(visibleCondition = nameof(developerMode), resettable = false)]
        public bool projectSetupCompleted { get; internal set; }

        /// <summary>
        /// Whether the plugin was properly setup.
        /// </summary>
        [EditorPref(visibleCondition = nameof(developerMode), resettable = false)]
        public bool editorSetupCompleted { get; internal set; }

        /// <summary>
        /// The last version to which the plugin successfully upgraded.
        /// </summary>
        [ProjectSetting(visibleCondition = nameof(developerMode), resettable = false)]
        public SemanticVersion savedVersion { get; internal set; }

        protected bool developerMode => BoltCore.Configuration.developerMode;

        #endregion


        #region Menu

#if VISUAL_SCRIPT_INTERNAL
        [MenuItem("Tools/Bolt/Internal/Delete All Project Settings", priority = LudiqProduct.DeveloperToolsMenuPriority + 401)]
#endif
        public static void DeleteAllProjectSettings()
        {
            foreach (var plugin in PluginContainer.plugins)
            {
                AssetDatabase.DeleteAsset(PathUtility.FromProject(plugin.configuration.projectSettingsStoragePath));
            }
        }

#if VISUAL_SCRIPT_INTERNAL
        [MenuItem("Tools/Bolt/Internal/Delete All Editor Prefs", priority = LudiqProduct.DeveloperToolsMenuPriority + 402)]
#endif
        public static void DeleteAllEditorPrefs()
        {
            foreach (var plugin in PluginContainer.plugins)
            {
                // Delete all current editor prefs for this plugin
                foreach (var editorPref in plugin.configuration.editorPrefs)
                {
                    EditorPrefs.DeleteKey(editorPref.namespacedKey);
                }

                // If our plugin was renamed, delete all editor pref keys for the plugin using its previous names
                IEnumerable<RenamedFromAttribute> renamedFromAttributes;
                var fieldInfo = plugin.GetType().GetField("ID", BindingFlags.Public | BindingFlags.Static);
                renamedFromAttributes = fieldInfo.GetCustomAttributes(typeof(RenamedFromAttribute), true).Cast<RenamedFromAttribute>();
                foreach (var renamed in renamedFromAttributes)
                {
                    foreach (var editorPref in plugin.configuration.editorPrefs)
                    {
                        EditorPrefs.DeleteKey(EditorPrefMetadata.GetNamespacedKey(renamed.previousName, editorPref.key));
                    }
                }
            }
        }

#if VISUAL_SCRIPT_INTERNAL
        [MenuItem("Tools/Bolt/Internal/Delete All Player Prefs", priority = LudiqProduct.DeveloperToolsMenuPriority + 403)]
#endif
        public static void DeleteAllPlayerPrefs()
        {
            PlayerPrefs.DeleteAll();
        }

        #endregion
    }
}

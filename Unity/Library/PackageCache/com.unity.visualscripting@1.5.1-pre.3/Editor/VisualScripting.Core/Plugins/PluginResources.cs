using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityObject = UnityEngine.Object;

namespace Unity.VisualScripting
{
    [PluginModule(required = true)]
    public class PluginResources : IPluginModule
    {
        protected PluginResources(Plugin plugin)
        {
            this.plugin = plugin;
        }

        public virtual void Initialize()
        {
            acknowledgements = InstantiateLinkedTypes<PluginAcknowledgement>().OrderBy(a => a.title).ToList().AsReadOnly();
            migrations = InstantiateLinkedTypes<PluginMigration>().OrderBy(m => m).ToList().AsReadOnly();
            changelogs = InstantiateLinkedTypes<PluginChangelog>().OrderBy(m => m).ToList().AsReadOnly();

            var pluginType = plugin.GetType();
            assembly = new AssemblyResourceProvider(pluginType.Assembly, pluginType.Namespace, assemblyRoot);
            _providers.Add(assembly);

            if (Directory.Exists(plugin.paths.resourcesFolder))
            {
                editorAssets = new EditorAssetResourceProvider(plugin.paths.resourcesFolder);
                _providers.Add(editorAssets);
            }

            if (File.Exists(plugin.paths.resourcesBundle))
            {
                assetBundle = new AssetBundleResourceProvider(AssetBundle.LoadFromFile(plugin.paths.resourcesBundle));
                _providers.Add(assetBundle);
            }

            if (_providers.Count == 0)
            {
                Debug.LogWarning($"No plugin resources provider available for {plugin.id}.");
            }
            else
            {
                defaultProvider = _providers[0];
            }
        }

        public virtual void LateInitialize() {}

        public Plugin plugin { get; }


        #region Types

        public ReadOnlyCollection<PluginAcknowledgement> acknowledgements { get; private set; }

        public ReadOnlyCollection<PluginMigration> migrations { get; private set; }

        public ReadOnlyCollection<PluginChangelog> changelogs { get; private set; }

        public IEnumerable<PluginMigration> pendingMigrations => migrations.Where(m => m.from >= plugin.manifest.savedVersion && m.to <= plugin.manifest.currentVersion);

        protected IEnumerable<Type> GetLinkedTypes<T>() where T : IPluginLinked
        {
            return PluginContainer.GetLinkedTypes(typeof(T), plugin.id);
        }

        protected T[] InstantiateLinkedTypes<T>() where T : IPluginLinked
        {
            return PluginContainer.InstantiateLinkedTypes(typeof(T), plugin).Cast<T>().ToArray();
        }

        #endregion


        #region Files

        public IResourceProvider defaultProvider { get; private set; }

        private readonly List<IResourceProvider> _providers = new List<IResourceProvider>();

        public IEnumerable<IResourceProvider> providers => _providers;

        protected virtual string assemblyRoot => "Resources";

        public AssemblyResourceProvider assembly { get; private set; }

        public AssetBundleResourceProvider assetBundle { get; private set; }

        public EditorAssetResourceProvider editorAssets { get; private set; }

        public T LoadAsset<T>(string path, bool required) where T : UnityObject
        {
            foreach (var provider in providers)
            {
                var asset = provider.LoadAsset<T>(path);

                if (asset != null)
                {
                    return asset;
                }
            }

            if (required)
            {
                Debug.LogWarning($"Missing plugin asset: \n{path}.");
            }

            return null;
        }

        public EditorTexture LoadTexture(string path, CreateTextureOptions options, bool required = true)
        {
            return EditorTexture.Load(providers, path, options, required);
        }

        public EditorTexture LoadTexture(string path, TextureResolution[] resolutions, CreateTextureOptions options, bool required = true)
        {
            return EditorTexture.Load(providers, path, resolutions, options, required);
        }

        public EditorTexture LoadIcon(string path, bool required = true)
        {
            return EditorTexture.Load(providers, path, EditorTexture.StandardIconResolutions, CreateTextureOptions.PixelPerfect, required);
        }

        public static EditorTexture LoadSharedIcon(string path, bool required = true)
        {
            Ensure.That(nameof(path)).IsNotNull(path);

            foreach (var plugin in PluginContainer.plugins)
            {
                var pluginIcon = plugin.resources.LoadIcon(path, false);

                if (pluginIcon != null)
                {
                    return pluginIcon;
                }
            }

            if (required)
            {
                Debug.LogWarning($"Missing shared editor texture: \n{path}");
            }

            return null;
        }

        #endregion
    }
}

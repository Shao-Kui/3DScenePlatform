using System;
using System.CodeDom;
using System.CodeDom.Compiler;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Xml.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.Scripting;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEditor.Callbacks;
using JetBrains.Annotations;

namespace Unity.VisualScripting
{
    //Intended to be invoked through build-time reflection
    public class AotPreBuilder : IPreprocessBuildWithReport
    {
        private static AotPreBuilder instance;

        public int callbackOrder => 1;

        private string linkerPath => Path.Combine(BoltCore.Paths.persistentGenerated, "link.xml");
        private string aotStubsPath => Path.Combine(BoltCore.Paths.persistentGenerated, "AotStubs.cs");

        [UsedImplicitly]
        public AotPreBuilder()
        {
            instance = this;
        }

        [PostProcessBuild]
        public static void OnPostProcessBuild(BuildTarget target, string pathToBuiltProject)
        {
            instance.DeleteAotStubs();
        }

#if VISUAL_SCRIPT_INTERNAL
        [MenuItem("Tools/Bolt/Internal/AOT Pre-Build", priority = LudiqProduct.DeveloperToolsMenuPriority + 1001)]
#endif
        public static void GenerateFromInternalMenu()
        {
            if (instance == null)
            {
                instance = new AotPreBuilder();
            }

            instance.GenerateAotStubs();
        }

        public void OnPreprocessBuild(BuildReport report)
        {
            // If the user isn't using Visual Scripting, we don't do any of this
            if (!Directory.Exists(PluginPaths.generated)) return;

            if (PlayerSettings.GetScriptingBackend(report.summary.platformGroup) != ScriptingImplementation.IL2CPP)
            {
                return;
            }

            GenerateAotStubs();
        }

        private void GenerateAotStubs()
        {
            try
            {
                GenerateLinker();
                GenerateStubScript(aotStubsPath, FindAllProjectStubs().Distinct().Select(s => AotStubWriterProvider.instance.GetDecorator(s)));
            }
            catch (Exception ex)
            {
                Debug.LogException(ex);
                DeleteAotStubs();
            }
        }

        private void DeleteAotStubs()
        {
            PathUtility.DeleteProjectFileIfExists(linkerPath, true);
            PathUtility.DeleteProjectFileIfExists(aotStubsPath, true);
        }

        // Automatically generates the link.xml file to prevent stripping.
        // Currently only used for plugin assemblies, because blanket preserving
        // all setting assemblies sometimes causes the IL2CPP process to fail.
        // For settings assemblies, the AOT stubs are good enough to fool
        // the static code analysis without needing this full coverage.
        // https://docs.unity3d.com/Manual/iphone-playerSizeOptimization.html
        // However, for FullSerializer, we need to preserve our custom assemblies.
        // This is mostly because IL2CPP will attempt to transform non-public
        // property setters used in deserialization into read-only accessors
        // that return false on PropertyInfo.CanWrite, but only in stripped builds.
        // Therefore, in stripped builds, FS will skip properties that should be
        // deserialized without any error (and that took hours of debugging to figure out).
        private void GenerateLinker()
        {
            var linker = new XDocument();

            var linkerNode = new XElement("linker");

            foreach (var pluginAssembly in PluginContainer.plugins
                     .SelectMany(plugin => plugin.GetType()
                         .GetAttributes<PluginRuntimeAssemblyAttribute>()
                         .Select(a => a.assemblyName))
                     .Distinct())
            {
                var assemblyNode = new XElement("assembly");
                var fullnameAttribute = new XAttribute("fullname", pluginAssembly);
                var preserveAttribute = new XAttribute("preserve", "all");
                assemblyNode.Add(fullnameAttribute);
                assemblyNode.Add(preserveAttribute);
                linkerNode.Add(assemblyNode);
            }

            linker.Add(linkerNode);

            PathUtility.CreateDirectoryIfNeeded(BoltCore.Paths.transientGenerated);

            PathUtility.DeleteProjectFileIfExists(linkerPath, true);

            // Using ToString instead of Save to omit the <?xml> declaration,
            // which doesn't appear in the Unity documentation page for the linker.
            File.WriteAllText(linkerPath, linker.ToString());
        }

        private IEnumerable<object> FindAllProjectStubs()
        {
            EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo();

            // Settings

            EditorUtility.DisplayProgressBar("AOT Pre-Build", "Finding AOT stubs in settings...", 0);

            foreach (var settingStub in FindAllSettingsStubs())
            {
                yield return settingStub;
            }

            // Plugins

            EditorUtility.DisplayProgressBar("AOT Pre-Build", "Finding AOT stubs in plugins...", 0);

            foreach (var pluginStub in FindAllPluginStubs())
            {
                yield return pluginStub;
            }

            // Assets

            EditorUtility.DisplayProgressBar("AOT Pre-Build", "Finding AOT stubs in assets...", 0);

            foreach (var assetStub in FindAllAssetStubs())
            {
                yield return assetStub;
            }

            // Scenes

            var activeScenePath = SceneManager.GetActiveScene().path;

            var scenePaths = EditorBuildSettings.scenes.Select(s => s.path).ToArray();

            var sceneIndex = 0;

            foreach (var scenePath in scenePaths)
            {
                EditorUtility.DisplayProgressBar("AOT Pre-Build", $"Finding AOT stubs in '{scenePath}'...", (float)sceneIndex++ / scenePaths.Length);

                if (string.IsNullOrEmpty(scenePath))
                {
                    continue;
                }

                try
                {
                    EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
                }
                catch (Exception ex)
                {
                    Debug.LogWarning($"Failed to open scene '{scenePath}' during AOT pre-build, skipping.\n{ex}");
                }

                foreach (var sceneStub in FindAllSceneStubs())
                {
                    yield return sceneStub;
                }
            }

            if (!string.IsNullOrEmpty(activeScenePath))
            {
                EditorSceneManager.OpenScene(activeScenePath);
            }

            EditorUtility.ClearProgressBar();
        }

        private IEnumerable<object> FindAllSettingsStubs()
        {
            // Include all custom operators for the formula unit and generic math units
            // Also include all user defined conversion operators for the conversion utility
            var codebaseSubset = Codebase.Subset(Codebase.settingsTypes, TypeFilter.Any.Configured(), MemberFilter.Any.Configured());

            codebaseSubset.Cache();

            return codebaseSubset.members
                .Select(m => m.info)
                .OfType<MethodInfo>()
                .Where(m => m.IsOperator() || m.IsUserDefinedConversion());
        }

        private IEnumerable<object> FindAllPluginStubs()
        {
            return PluginContainer.plugins.SelectMany(p => p.aotStubs);
        }

        private IEnumerable<object> FindAllAssetStubs()
        {
            return LinqUtility.Concat<object>
                (
                    AssetUtility.GetAllAssetsOfType<IAotStubbable>()
                        .SelectMany(aot => aot.aotStubs),

                    AssetUtility.GetAllAssetsOfType<GameObject>()
                        .SelectMany(go => go.GetComponents<IAotStubbable>()
                            .SelectMany(component => component.aotStubs))
                );
        }

        private IEnumerable<object> FindAllSceneStubs()
        {
            return UnityObjectUtility.FindObjectsOfTypeIncludingInactive<IAotStubbable>()
                .SelectMany(aot => aot.aotStubs);
        }

        private void GenerateStubScript(string scriptPath, IEnumerable<AotStubWriter> stubWriters)
        {
            Ensure.That(nameof(stubWriters)).IsNotNull(stubWriters);

            var unit = new CodeCompileUnit();

            var @namespace = new CodeNamespace("Unity.VisualScripting.Generated.Aot");

            unit.Namespaces.Add(@namespace);

            var @class = new CodeTypeDeclaration("AotStubs")
            {
                IsClass = true
            };

            @class.CustomAttributes.Add(new CodeAttributeDeclaration(new CodeTypeReference(typeof(PreserveAttribute))));

            @namespace.Types.Add(@class);

            var usedMethodNames = new HashSet<string>();

            foreach (var stubWriter in stubWriters.OrderBy(sw => sw.stubMethodComment))
            {
                if (stubWriter.skip)
                {
                    continue;
                }

                var methodName = stubWriter.stubMethodName;

                var i = 0;

                while (usedMethodNames.Contains(methodName))
                {
                    methodName = stubWriter.stubMethodName + "_" + i++;
                }

                usedMethodNames.Add(methodName);

                @class.Comments.Add(new CodeCommentStatement(stubWriter.stubMethodComment));

                var @method = new CodeMemberMethod
                {
                    Name = methodName,
                    ReturnType = new CodeTypeReference(typeof(void)),
                    Attributes = MemberAttributes.Public | MemberAttributes.Static
                };

                @method.CustomAttributes.Add(new CodeAttributeDeclaration(new CodeTypeReference(typeof(PreserveAttribute), CodeTypeReferenceOptions.GlobalReference)));

                @method.Comments.Add(new CodeCommentStatement(stubWriter.stubMethodComment));

                @method.Statements.AddRange(stubWriter.GetStubStatements().ToArray());

                @class.Members.Add(@method);
            }

            PathUtility.CreateDirectoryIfNeeded(BoltCore.Paths.transientGenerated);

            PathUtility.DeleteProjectFileIfExists(aotStubsPath, true);

            using (var provider = CodeDomProvider.CreateProvider("CSharp"))
            {
                var options = new CodeGeneratorOptions
                {
                    BracingStyle = "C",
                    IndentString = "\t",
                    BlankLinesBetweenMembers = true,
                    ElseOnClosing = false,
                    VerbatimOrder = true
                };

                using (var scriptWriter = new StreamWriter(scriptPath))
                {
                    provider.GenerateCodeFromCompileUnit(new CodeSnippetCompileUnit("#pragma warning disable 219"), scriptWriter, options); // Disable unused variable warning
                    provider.GenerateCodeFromCompileUnit(unit, scriptWriter, options);
                }
            }

            AssetDatabase.Refresh();
        }
    }
}

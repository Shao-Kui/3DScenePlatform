using System.IO;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;

namespace Unity.VisualScripting
{
    [Plugin(BoltCore.ID)]
    internal class Migration_1_4_13_to_1_5_0 : PluginMigration
    {
        public Migration_1_4_13_to_1_5_0(Plugin plugin) : base(plugin) {}

        public override SemanticVersion @from => "1.4.13";
        public override SemanticVersion to => "1.5.1";

        public override void Run()
        {
            // Port our generated code (including project settings) to the new generated folder
            // Todo: Our generated projects settings need to be merged (old assemblies have been merged into Core)
            foreach (var p in PluginContainer.plugins)
            {
                var oldGeneratedDirectoryPath = Path.Combine(Paths.assets, "Ludiq", p.id, "Generated");
                if (Directory.Exists(oldGeneratedDirectoryPath))
                {
                    Directory.Delete(p.paths.persistentGenerated, true);
                    Directory.Move(oldGeneratedDirectoryPath, p.paths.persistentGenerated);
                }
            }

            // Fix script references
            ScriptReferenceResolver.Run();

            // TODO: Need to fix our EditorPrefs as they're stored outside the project (Registry for windows)

            foreach (var p in PluginContainer.plugins)
            {
                p.configuration.Initialize();
            }

            AssetDatabase.Refresh();
        }
    }

    [Plugin(BoltCore.ID)]
    internal class DeprecatedSavedVersionLoader_1_4_13_to_1_5_0 : PluginDeprecatedSavedVersionLoader
    {
        public DeprecatedSavedVersionLoader_1_4_13_to_1_5_0(Plugin plugin) : base(plugin) {}

        public override SemanticVersion @from => "1.5.1";

        public override bool Run(out SemanticVersion savedVersion)
        {
            savedVersion = new SemanticVersion();
            var OldProjectSettingsPath = Path.Combine(Paths.assets, "Ludiq", "Bolt.Core", "Generated", "ProjectSettings.asset");

            if (!File.Exists(OldProjectSettingsPath))
            {
                return false;
            }

            string projectSettingsText = System.IO.File.ReadAllText(OldProjectSettingsPath);
            int savedVersionIndex = projectSettingsText.IndexOf("savedVersion");
            if (savedVersionIndex == -1)
            {
                return false;
            }

            Match majorVersionMatch = new Regex(@"""major"":([0-9]*),").Match(projectSettingsText, savedVersionIndex);
            Match minorVersionMatch = new Regex(@"""minor"":([0-9]*),").Match(projectSettingsText, savedVersionIndex);
            Match patchVersionMatch = new Regex(@"""patch"":([0-9]*),").Match(projectSettingsText, savedVersionIndex);

            int majorVersion = int.Parse(majorVersionMatch.Groups[1].Value);
            int minorVersion = int.Parse(minorVersionMatch.Groups[1].Value);
            int patchVersion = int.Parse(patchVersionMatch.Groups[1].Value);

            savedVersion = new SemanticVersion(majorVersion, minorVersion, patchVersion, null, 0);

            return true;
        }
    }
}

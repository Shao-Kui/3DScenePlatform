using System;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;

namespace Unity.VisualScripting
{
    public abstract class PluginAcknowledgement : IPluginLinked
    {
        protected PluginAcknowledgement(Plugin plugin)
        {
            this.plugin = plugin;
        }

        public Plugin plugin { get; }

        public abstract string title { get; }
        public abstract string author { get; }

        public virtual int? copyrightYear => null;
        public virtual string url => null;
        public virtual string licenseName => null;
        public virtual string licenseText => null;

        public static void GenerateLicenseFile(string path)
        {
            var acknowledgements = PluginContainer.plugins
                .SelectMany(plugin => plugin.resources.acknowledgements)
                .Distinct()
                .ToArray();

            var sb = new StringBuilder();

            sb.AppendLine("The Unity Asset Store policy requires that all third-party");
            sb.AppendLine("licenses be contained in a single LICENSES files.");
            sb.AppendLine("This file is auto-generated for this purpose.");
            sb.AppendLine();
            sb.AppendLine("However, you can find a more readable version of each product's");
            sb.AppendLine("acknowledgements in its About window, found in the Tools menu.");
            sb.AppendLine();
            sb.AppendLine("Acknowledgements below:");

            foreach (var acknowledgement in acknowledgements)
            {
                sb.AppendLine(" - " + acknowledgement.title);
            }

            foreach (var acknowledgement in acknowledgements)
            {
                sb.AppendLine();
                sb.AppendLine("=============================");
                sb.AppendLine();
                sb.AppendLine(acknowledgement.title);

                var hasAuthor = !StringUtility.IsNullOrWhiteSpace(acknowledgement.author);
                var hasCopyright = acknowledgement.copyrightYear != null;

                if (hasAuthor && hasCopyright)
                {
                    sb.AppendLine($"Copyright \u00a9 {acknowledgement.copyrightYear} {acknowledgement.author}");
                }
                else if (hasAuthor)
                {
                    sb.AppendLine($"Author: {acknowledgement.author}");
                }
                else if (hasCopyright)
                {
                    sb.AppendLine($"Copyright \u00a9 {acknowledgement.copyrightYear}");
                }

                if (!StringUtility.IsNullOrWhiteSpace(acknowledgement.url))
                {
                    sb.AppendLine(acknowledgement.url);
                }

                if (!StringUtility.IsNullOrWhiteSpace(acknowledgement.licenseName))
                {
                    sb.AppendLine("License: " + acknowledgement.licenseName.Trim());
                }

                if (!StringUtility.IsNullOrWhiteSpace(acknowledgement.licenseText))
                {
                    var licenseText = string.Join("\n\n", acknowledgement.licenseText.Split(new[] { "\r\n\r\n", "\n\n" }, StringSplitOptions.RemoveEmptyEntries).Select(s => s.Replace("\r\n", "").Replace("\n", "")).ToArray());

                    sb.AppendLine();
                    sb.AppendLine(licenseText);
                }
            }

            if (path == null)
            {
                path = EditorUtility.SaveFilePanelInProject("License File", "LICENSES", "txt", null);
            }

            if (path != null)
            {
                File.WriteAllText(path, sb.ToString());
                AssetDatabase.Refresh();
            }
        }

#if VISUAL_SCRIPT_INTERNAL
        [MenuItem("Tools/Bolt/Internal/Generate License File (Deprecated)", priority = LudiqProduct.DeveloperToolsMenuPriority + 501)]
#endif
        private static void GenerateLicenseFile()
        {
            GenerateLicenseFile(null);
        }
    }
}

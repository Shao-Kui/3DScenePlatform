using UnityEditor;
using YamlDotNet.RepresentationModel;
using UnityObject = UnityEngine.Object;

namespace Unity.VisualScripting
{
    public class PluginIconMapper : AssetPostprocessor
    {
        private static void AddIconMap(YamlMappingNode iconMapNode, string assetGuid)
        {
            // Add our own mappings.
            // https://forum.unity3d.com/threads/custom-asset-icons.118656/#post-2443602

            iconMapNode.Add("fileID", "2800000");
            iconMapNode.Add("guid", assetGuid);
            iconMapNode.Add("type", "3");
        }
    }
}

using UnityObject = UnityEngine.Object;

namespace Unity.VisualScripting
{
    public static class GraphNesterDescriptor
    {
        public static string Title(IGraphNester nester)
        {
            var graph = nester.childGraph;

            if (!StringUtility.IsNullOrWhiteSpace(graph?.title))
            {
                return graph?.title;
            }

            if (nester.nest.source == GraphSource.Macro && (UnityObject)nester.nest.macro != null)
            {
                var macroName = ((UnityObject)nester.nest.macro).name;

                if (BoltCore.Configuration.humanNaming)
                {
                    return macroName.Prettify();
                }
                else
                {
                    return macroName;
                }
            }

            return nester.GetType().HumanName();
        }

        public static string Summary(IGraphNester nester)
        {
            var graph = nester.childGraph;

            if (!StringUtility.IsNullOrWhiteSpace(graph?.summary))
            {
                return graph?.summary;
            }

            return nester.GetType().Summary();
        }
    }
}

using UnityEngine;

namespace Unity.VisualScripting
{
    [CreateAssetMenu(menuName = "Visual Scripting/Script Graph", fileName = "New Script Graph", order = 81)]
    public sealed class ScriptGraphAsset : Macro<FlowGraph>
    {
        [ContextMenu("Show Data...")]
        protected override void ShowData()
        {
            base.ShowData();
        }

        public override FlowGraph DefaultGraph()
        {
            return FlowGraph.WithInputOutput();
        }
    }
}

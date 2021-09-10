using UnityEngine;

namespace Unity.VisualScripting
{
    [CreateAssetMenu(menuName = "Visual Scripting/State Graph", fileName = "New State Graph", order = 81)]
    public sealed class StateGraphAsset : Macro<StateGraph>
    {
        [ContextMenu("Show Data...")]
        protected override void ShowData()
        {
            base.ShowData();
        }

        public override StateGraph DefaultGraph()
        {
            return StateGraph.WithStart();
        }
    }
}

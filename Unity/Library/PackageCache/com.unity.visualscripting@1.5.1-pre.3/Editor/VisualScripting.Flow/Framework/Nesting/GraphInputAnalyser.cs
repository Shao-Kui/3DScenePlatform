using System.Collections.Generic;

namespace Unity.VisualScripting
{
    [Analyser(typeof(GraphInput))]
    public class GraphInputAnalyser : UnitAnalyser<GraphInput>
    {
        public GraphInputAnalyser(GraphReference reference, GraphInput unit) : base(reference, unit) {}

        protected override IEnumerable<Warning> Warnings()
        {
            foreach (var baseWarning in base.Warnings())
            {
                yield return baseWarning;
            }

            if (unit.graph != null)
            {
                foreach (var definitionWarning in UnitPortDefinitionUtility.Warnings(unit.graph, LinqUtility.Concat<IUnitPortDefinition>(unit.graph.controlInputDefinitions, unit.graph.valueInputDefinitions)))
                {
                    yield return definitionWarning;
                }
            }
        }
    }
}

using UnityObject = UnityEngine.Object;

namespace Unity.VisualScripting
{
    [FuzzyOption(typeof(INesterUnit))]
    public class NesterUnitOption<TNesterUnit> : UnitOption<TNesterUnit> where TNesterUnit : INesterUnit
    {
        public NesterUnitOption() : base() {}

        public NesterUnitOption(TNesterUnit unit) : base(unit) {}

        // TODO: Favoritable
        public override bool favoritable => false;

        protected override string Label(bool human)
        {
            return UnityAPI.Await(() =>
            {
                var macro = (UnityObject)unit.nest.macro;

                if (macro != null)
                {
                    return macro.name;
                }
                else
                {
                    return unit.GetType().HumanName();
                }
            });
        }
    }
}

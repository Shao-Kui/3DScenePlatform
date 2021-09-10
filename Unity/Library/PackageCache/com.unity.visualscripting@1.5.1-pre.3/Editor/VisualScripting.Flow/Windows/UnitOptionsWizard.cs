using UnityEditor;
using UnityEngine;

namespace Unity.VisualScripting
{
    public sealed class UnitOptionsWizard : Wizard
    {
        public static UnitOptionsWizard instance { get; }

        static UnitOptionsWizard()
        {
            instance = new UnitOptionsWizard();
        }

        public UnitOptionsWizard() : base()
        {
            pages.Add(new AssemblyOptionsPage());
            pages.Add(new TypeOptionsPage());
        }

        protected override void ConfigureWindow()
        {
            window.titleContent = new GUIContent("Unit Options Wizard");
            window.minSize = window.maxSize = new Vector2(500, 400);
        }
    }
}

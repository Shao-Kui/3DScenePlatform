namespace Unity.VisualScripting
{
    [Plugin(BoltCore.ID)]
    public sealed class BoltCoreResources : PluginResources
    {
        private BoltCoreResources(BoltCore plugin) : base(plugin)
        {
            icons = new Icons(this);
        }

        public Icons icons { get; private set; }

        public EditorTexture loader { get; private set; }

        public override void LateInitialize()
        {
            base.LateInitialize();

            icons.Load();

            loader = LoadTexture("Loader/Loader.png", CreateTextureOptions.PixelPerfect);
        }

        public class Icons
        {
            public EditorTexture variablesWindow { get; private set; }

            public EditorTexture variable { get; private set; }
            public EditorTexture flowVariable { get; private set; }
            public EditorTexture graphVariable { get; private set; }
            public EditorTexture objectVariable { get; private set; }
            public EditorTexture sceneVariable { get; private set; }
            public EditorTexture applicationVariable { get; private set; }
            public EditorTexture savedVariable { get; private set; }

            public EditorTexture window { get; private set; }
            public EditorTexture inspectorWindow { get; private set; }

            public EditorTexture empty { get; private set; }

            public EditorTexture progress { get; private set; }
            public EditorTexture errorState { get; private set; }
            public EditorTexture successState { get; private set; }
            public EditorTexture warningState { get; private set; }

            public EditorTexture informationMessage { get; private set; }
            public EditorTexture questionMessage { get; private set; }
            public EditorTexture warningMessage { get; private set; }
            public EditorTexture successMessage { get; private set; }
            public EditorTexture errorMessage { get; private set; }

            public EditorTexture upgrade { get; private set; }
            public EditorTexture upToDate { get; private set; }
            public EditorTexture downgrade { get; private set; }

            public EditorTexture supportWindow { get; private set; }
            public EditorTexture sidebarAnchorLeft { get; private set; }
            public EditorTexture sidebarAnchorRight { get; private set; }
            public EditorTexture editorPref { get; private set; }
            public EditorTexture projectSetting { get; private set; }

            public EditorTexture @null { get; private set; }

            public Icons(BoltCoreResources resources)
            {
                this.resources = resources;
            }

            private readonly BoltCoreResources resources;

            public void Load()
            {
                variablesWindow = resources.LoadIcon("Icons/Windows/VariablesWindow.png");

                variable = resources.LoadIcon("Icons/Variables/Variable.png");
                flowVariable = resources.LoadIcon("Icons/Variables/FlowVariable.png");
                graphVariable = resources.LoadIcon("Icons/Variables/GraphVariable.png");
                objectVariable = resources.LoadIcon("Icons/Variables/ObjectVariable.png");
                sceneVariable = resources.LoadIcon("Icons/Variables/SceneVariable.png");
                applicationVariable = resources.LoadIcon("Icons/Variables/ApplicationVariable.png");
                savedVariable = resources.LoadIcon("Icons/Variables/SavedVariable.png");

                window = resources.LoadIcon("Windows/GraphWindow.png");
                inspectorWindow = resources.LoadIcon("Windows/GraphInspectorWindow.png");

                if (GraphWindow.active != null)
                {
                    GraphWindow.active.titleContent.image = window ? [IconSize.Small];
                }

                empty = EditorTexture.Single(ColorPalette.transparent.GetPixel());

                // Messages
                informationMessage = resources.LoadIcon("Icons/Messages/Information.png");
                questionMessage = resources.LoadIcon("Icons/Messages/Question.png");
                warningMessage = resources.LoadIcon("Icons/Messages/Warning.png");
                successMessage = resources.LoadIcon("Icons/Messages/Success.png");
                errorMessage = resources.LoadIcon("Icons/Messages/Error.png");

                // States
                warningState = resources.LoadIcon("Icons/State/Warning.png");
                successState = resources.LoadIcon("Icons/State/Success.png");
                errorState = resources.LoadIcon("Icons/State/Error.png");
                progress = resources.LoadIcon("Icons/State/Progress.png");

                // Versioning
                upgrade = resources.LoadIcon("Icons/Versioning/Upgrade.png");
                upToDate = resources.LoadIcon("Icons/Versioning/UpToDate.png");
                downgrade = resources.LoadIcon("Icons/Versioning/Downgrade.png");

                // Windows
                supportWindow = resources.LoadIcon("Icons/Windows/SupportWindow.png");
                sidebarAnchorLeft = resources.LoadTexture("Icons/Windows/SidebarAnchorLeft.png", CreateTextureOptions.PixelPerfect);
                sidebarAnchorRight = resources.LoadTexture("Icons/Windows/SidebarAnchorRight.png", CreateTextureOptions.PixelPerfect);

                // Configuration
                editorPref = resources.LoadTexture("Icons/Configuration/EditorPref.png", new TextureResolution[] { 12, 24 }, CreateTextureOptions.PixelPerfect);
                projectSetting = resources.LoadTexture("Icons/Configuration/ProjectSetting.png", new TextureResolution[] { 12, 24 }, CreateTextureOptions.PixelPerfect);

                // Other
                @null = resources.LoadIcon("Icons/Null.png");
            }

            public EditorTexture VariableKind(VariableKind kind)
            {
                switch (kind)
                {
                    case VisualScripting.VariableKind.Flow : return flowVariable;
                    case VisualScripting.VariableKind.Graph: return graphVariable;
                    case VisualScripting.VariableKind.Object: return objectVariable;
                    case VisualScripting.VariableKind.Scene: return sceneVariable;
                    case VisualScripting.VariableKind.Application: return applicationVariable;
                    case VisualScripting.VariableKind.Saved: return savedVariable;
                    default: throw new UnexpectedEnumValueException<VariableKind>(kind);
                }
            }
        }
    }
}

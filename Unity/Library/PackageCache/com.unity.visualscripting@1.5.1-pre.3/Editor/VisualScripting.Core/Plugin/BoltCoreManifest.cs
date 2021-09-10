namespace Unity.VisualScripting
{
    [Plugin(BoltCore.ID)]
    public sealed class BoltCoreManifest : PluginManifest
    {
        private BoltCoreManifest(BoltCore plugin) : base(plugin) {}

        public override string name => "Bolt Core";
        public override string author => "";
        public override string description => "";
        public override SemanticVersion version => "1.5.1";
    }
}

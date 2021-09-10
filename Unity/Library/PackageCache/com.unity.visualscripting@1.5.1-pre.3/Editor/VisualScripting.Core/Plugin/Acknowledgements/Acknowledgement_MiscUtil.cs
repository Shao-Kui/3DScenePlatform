namespace Unity.VisualScripting
{
    [Plugin(BoltCore.ID)]
    internal class Acknowledgement_MiscUtil : PluginAcknowledgement
    {
        public Acknowledgement_MiscUtil(Plugin plugin) : base(plugin) {}

        public override string title => "MiscUtil";
        public override string author => "Jon Skeet";
        public override int? copyrightYear => 2008;
        public override string url => "http://www.yoda.arachsys.com/csharp/miscutil/index.html";
        public override string licenseText => Licenses.MiscUtil;
    }
}

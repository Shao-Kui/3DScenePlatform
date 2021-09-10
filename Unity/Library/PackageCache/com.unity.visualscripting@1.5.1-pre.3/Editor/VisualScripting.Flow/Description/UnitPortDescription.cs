using System;

namespace Unity.VisualScripting
{
    public sealed class UnitPortDescription : IDescription
    {
        private string _label;

        private bool _isLabelVisible = true;

        public string fallbackLabel { get; set; }

        public string label
        {
            get => _label ?? fallbackLabel;
            set => _label = value;
        }

        public bool showLabel
        {
            get => !BoltFlow.Configuration.hidePortLabels || _isLabelVisible;
            set => _isLabelVisible = value;
        }

        string IDescription.title => label;

        public string summary { get; set; }

        public EditorTexture icon { get; set; }

        public Func<Metadata, Metadata> getMetadata { get; set; }

        public void CopyFrom(UnitPortDescription other)
        {
            _label = other._label;
            _isLabelVisible = other._isLabelVisible;
            summary = other.summary;
            icon = other.icon ?? icon;
            getMetadata = other.getMetadata ?? getMetadata;
        }
    }
}

using System;

namespace Unity.VisualScripting
{
    [SerializationVersion("A")]
    public sealed class VariableDeclaration
    {
        [Obsolete(Serialization.ConstructorWarning)]
        public VariableDeclaration() {}

        public VariableDeclaration(string name, object value)
        {
            this.name = name;
            this.value = value;
        }

        [Serialize]
        public string name { get; private set; }

        [Serialize]
        public object value { get; set; }
    }
}

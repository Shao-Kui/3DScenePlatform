using System;

namespace Unity.VisualScripting
{
    [AttributeUsage(AttributeTargets.Class, Inherited = false, AllowMultiple = true)]
    public class BackgroundWorkerAttribute : Attribute
    {
        public BackgroundWorkerAttribute(string methodName = "BackgroundWork")
        {
            this.methodName = methodName;
        }

        public string methodName { get; }
    }
}

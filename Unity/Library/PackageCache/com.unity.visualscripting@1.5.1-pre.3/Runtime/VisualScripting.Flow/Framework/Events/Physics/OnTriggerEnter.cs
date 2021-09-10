using System;

namespace Unity.VisualScripting
{
    /// <summary>
    /// Called when a collider enters the trigger.
    /// </summary>
    public sealed class OnTriggerEnter : TriggerEventUnit
    {
        public override Type MessageListenerType => typeof(UnityOnTriggerEnterMessageListener);
        protected override string hookName => EventHooks.OnTriggerEnter;
    }
}

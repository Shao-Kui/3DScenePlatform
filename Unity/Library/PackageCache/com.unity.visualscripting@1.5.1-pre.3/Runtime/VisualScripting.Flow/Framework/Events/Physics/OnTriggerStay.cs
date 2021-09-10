using System;

namespace Unity.VisualScripting
{
    /// <summary>
    /// Called once per frame for every collider that is touching the trigger.
    /// </summary>
    public sealed class OnTriggerStay : TriggerEventUnit
    {
        public override Type MessageListenerType => typeof(UnityOnTriggerStayMessageListener);
        protected override string hookName => EventHooks.OnTriggerStay;
    }
}

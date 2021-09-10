using System;

namespace Unity.VisualScripting
{
    /// <summary>
    /// Called once per frame for every collider / rigidbody that is touching rigidbody / collider.
    /// </summary>
    public sealed class OnCollisionStay : CollisionEventUnit
    {
        public override Type MessageListenerType => typeof(UnityOnCollisionStayMessageListener);
        protected override string hookName => EventHooks.OnCollisionStay;
    }
}

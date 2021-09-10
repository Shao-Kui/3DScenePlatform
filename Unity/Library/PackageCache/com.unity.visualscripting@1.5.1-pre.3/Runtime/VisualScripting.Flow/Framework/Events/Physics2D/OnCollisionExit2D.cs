using System;

namespace Unity.VisualScripting
{
    /// <summary>
    /// Called when a collider on another object stops touching this object's collider.
    /// </summary>
    public sealed class OnCollisionExit2D : CollisionEvent2DUnit
    {
        public override Type MessageListenerType => typeof(UnityOnCollisionExit2DMessageListener);
        protected override string hookName => EventHooks.OnCollisionExit2D;
    }
}

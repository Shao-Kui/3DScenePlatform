using UnityEngine;

namespace Unity.VisualScripting
{
    [AddComponentMenu("")]
    public sealed class UnityOnJointBreak2DMessageListener : MessageListener
    {
        private void OnJointBreak2D(Joint2D brokenJoint)
        {
            EventBus.Trigger(EventHooks.OnJointBreak2D, gameObject, brokenJoint);
        }
    }
}

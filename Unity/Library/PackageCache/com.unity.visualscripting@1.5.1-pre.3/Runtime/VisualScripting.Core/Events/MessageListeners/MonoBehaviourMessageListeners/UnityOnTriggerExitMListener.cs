using UnityEngine;

namespace Unity.VisualScripting
{
    [AddComponentMenu("")]
    public sealed class UnityOnTriggerExitMessageListener : MessageListener
    {
        private void OnTriggerExit(Collider other)
        {
            EventBus.Trigger(EventHooks.OnTriggerExit, gameObject, other);
        }
    }
}

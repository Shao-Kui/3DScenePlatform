using UnityEngine;

namespace Unity.VisualScripting
{
    [AddComponentMenu("")]
    public sealed class UnityOnCollisionEnterMessageListener : MessageListener
    {
        private void OnCollisionEnter(Collision collision)
        {
            EventBus.Trigger(EventHooks.OnCollisionEnter, gameObject, collision);
        }
    }
}

using UnityEngine;

namespace Unity.VisualScripting
{
    [AddComponentMenu("")]
    public sealed class UnityOnTriggerEnter2DMessageListener : MessageListener
    {
        private void OnTriggerEnter2D(Collider2D other)
        {
            EventBus.Trigger(EventHooks.OnTriggerEnter2D, gameObject, other);
        }
    }
}

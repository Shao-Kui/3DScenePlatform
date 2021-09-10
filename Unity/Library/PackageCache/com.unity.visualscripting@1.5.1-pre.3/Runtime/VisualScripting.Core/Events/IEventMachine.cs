using UnityEngine;

namespace Unity.VisualScripting
{
    public interface IEventMachine : IMachine
    {
        void TriggerAnimationEvent(AnimationEvent animationEvent);
        void TriggerUnityEvent(string name);
    }
}

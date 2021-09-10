using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using HTC.UnityPlugin.Vive;

public class TestReceiveRayHandle : MonoBehaviour, IPointerEnterHandler, IPointerExitHandler, IPointerClickHandler, IPointerDownHandler, IPointerUpHandler
{
    private HashSet<PointerEventData> m_received = new HashSet<PointerEventData> ();

    private bool dragByTrigger;

    public void OnPointerEnter (PointerEventData eventData) 
    {
        if (m_received.Add (eventData) && m_received.Count == 1) 
        {
            Debug.Log ("ray received!");
        }
    }

    public void OnPointerExit (PointerEventData eventData) 
    {
        if (m_received.Remove (eventData) && m_received.Count == 0) 
        {
            Debug.Log ("ray released!");
        }
    }

    public void OnPointerClick (PointerEventData eventData) 
    {
        if(eventData.IsViveButton(HandRole.RightHand, ControllerButton.Trigger))
        {
            Debug.Log ("ray hited and trigger pressed !");
        }
    }

    public void OnPointerDown (PointerEventData eventData) 
    {
        if(eventData.IsViveButton(HandRole.RightHand, ControllerButton.Trigger))
        {
            Debug.Log ("ray hited and pad pressed !");

        }
    }

    public void OnPointerUp (PointerEventData eventData) 
    {
        if(eventData.IsViveButton(HandRole.RightHand, ControllerButton.Trigger))
        {
            Debug.Log ("ray hited and pad pressed !");

        }
    }
}

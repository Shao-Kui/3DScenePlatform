﻿using HTC.UnityPlugin.ColliderEvent;
using System.Collections.Generic;
using UnityEngine;

public class ShowMenuOnClick : MonoBehaviour
    , IColliderEventClickHandler
    , IColliderEventPressEnterHandler
    , IColliderEventPressExitHandler
{
    public GameObject effectMenu;
    public ControllerManagerSample controllerManager;
    [SerializeField]
    private ColliderButtonEventData.InputButton m_activeButton = ColliderButtonEventData.InputButton.Trigger;

    public Transform buttonObject;
    public Vector3 buttonDownDisplacement;

    private Vector3 buttonOriginPosition;
    private bool menuVisible = false;

    private HashSet<ColliderButtonEventData> pressingEvents = new HashSet<ColliderButtonEventData>();

    public ColliderButtonEventData.InputButton activeButton { get { return m_activeButton; } set { m_activeButton = value; } }

    private void Start()
    {
        buttonOriginPosition = buttonObject.position;
        SetMenuVisible(menuVisible);
    }

    public void SetMenuVisible(bool value)
    {
        menuVisible = value;
        effectMenu.gameObject.SetActive(value);
        controllerManager.rightLaserPointerActive = value;
        controllerManager.leftLaserPointerActive = value;
        controllerManager.UpdateActivity();
    }

    public void OnColliderEventClick(ColliderButtonEventData eventData)
    {
        if (pressingEvents.Contains(eventData) && pressingEvents.Count == 1)
        {
            SetMenuVisible(!menuVisible);
        }
    }

    public void OnColliderEventPressEnter(ColliderButtonEventData eventData)
    {
        if (eventData.button == m_activeButton && eventData.clickingHandlers.Contains(gameObject) && pressingEvents.Add(eventData) && pressingEvents.Count == 1)
        {
            buttonObject.position = buttonOriginPosition + buttonDownDisplacement;
        }
    }

    public void OnColliderEventPressExit(ColliderButtonEventData eventData)
    {
        if (pressingEvents.Remove(eventData) && pressingEvents.Count == 0)
        {
            buttonObject.position = buttonOriginPosition;
        }
    }
}
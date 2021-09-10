using System;
using UnityEngine;

namespace UnityEditor.Timeline
{
    abstract class RectangleTool : Manipulator
    {
        struct TimelinePoint
        {
            readonly double m_Time;
            readonly float m_YPos;
            readonly float m_YScrollPos;

            readonly WindowState m_State;
            readonly TimelineTreeViewGUI m_TreeViewGUI;

            public TimelinePoint(WindowState state, Vector2 mousePosition)
            {
                m_State = state;
                m_TreeViewGUI = state.GetWindow().treeView;

                m_Time = m_State.PixelToTime(mousePosition.x);
                m_YPos = mousePosition.y;
                m_YScrollPos = m_TreeViewGUI.scrollPosition.y;
            }

            public Vector2 ToPixel()
            {
                return new Vector2(m_State.TimeToPixel(m_Time), m_YPos - (m_TreeViewGUI.scrollPosition.y - m_YScrollPos));
            }
        }

        TimeAreaAutoPanner m_TimeAreaAutoPanner;

        TimelinePoint m_StartPoint;
        Vector2 m_EndPixel = Vector2.zero;

        Rect m_ActiveRect;

        protected abstract bool enableAutoPan { get; }
        protected abstract bool CanStartRectangle(Event evt);
        protected abstract bool OnFinish(Event evt, WindowState state, Rect rect);

        protected override bool MouseDown(Event evt, WindowState state)
        {
            if (state.IsCurrentEditingASequencerTextField())
                return false;

            m_ActiveRect = TimelineWindow.instance.sequenceContentRect;

            if (!m_ActiveRect.Contains(evt.mousePosition))
                return false;

            if (!CanStartRectangle(evt))
                return false;

            if (enableAutoPan)
                m_TimeAreaAutoPanner = new TimeAreaAutoPanner(state);

            m_StartPoint = new TimelinePoint(state, evt.mousePosition);
            m_EndPixel = evt.mousePosition;

            state.AddCaptured(this);

            return true;
        }

        protected override bool KeyDown(Event evt, WindowState state)
        {
            if (evt.keyCode == KeyCode.Escape)
            {
                m_TimeAreaAutoPanner = null;
                GUIUtility.hotControl = 0;
                state.RemoveCaptured(this);
                return true;
            }
            return false;
        }

        protected override bool MouseDrag(Event evt, WindowState state)
        {
            m_EndPixel = evt.mousePosition;
            return true;
        }

        protected override bool MouseUp(Event evt, WindowState state)
        {
            m_TimeAreaAutoPanner = null;

            Rect rect = CurrentRectangle();

            if (IsValidRect(rect))
                OnFinish(evt, state, rect);

            state.RemoveCaptured(this);

            return true;
        }

        public override void Overlay(Event evt, WindowState state)
        {
            var r = CurrentRectangle();

            if (evt.type == EventType.Repaint)
            {
                if (IsValidRect(r))
                {
                    using (new GUIViewportScope(m_ActiveRect))
                    {
                        DrawRectangle(r);
                    }
                }
            }

            m_TimeAreaAutoPanner?.OnGUI(evt);
        }

        static void DrawRectangle(Rect rect)
        {
            EditorStyles.selectionRect.Draw(rect, GUIContent.none, false, false, false, false);
        }

        static bool IsValidRect(Rect rect)
        {
            return rect.width >= 1.0f && rect.height >= 1.0f;
        }

        Rect CurrentRectangle()
        {
            var startPixel = m_StartPoint.ToPixel();
            return Rect.MinMaxRect(
                Math.Min(startPixel.x, m_EndPixel.x),
                Math.Min(startPixel.y, m_EndPixel.y),
                Math.Max(startPixel.x, m_EndPixel.x),
                Math.Max(startPixel.y, m_EndPixel.y));
        }
    }
}

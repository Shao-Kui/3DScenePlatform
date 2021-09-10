using UnityEditor;
using UnityEngine;

namespace Unity.VisualScripting
{
    [Inspector(typeof(bool))]
    public class BoolInspector : Inspector
    {
        public BoolInspector(Metadata metadata) : base(metadata) {}

        protected override float GetHeight(float width, GUIContent label)
        {
            return HeightWithLabel(metadata, width, EditorGUIUtility.singleLineHeight, label);
        }

        protected override void OnGUI(Rect position, GUIContent label)
        {
            bool newValue;

            if (metadata.HasAttribute<InspectorToggleLeftAttribute>())
            {
                BeginBlock(metadata, position, new GUIContent("", null, label.tooltip));
                var togglePosition = position.VerticalSection(ref y, EditorGUIUtility.singleLineHeight);
                var labelStyle = new GUIStyle(ProcessLabelStyle(metadata, null));
                labelStyle.padding.left = 2;
                newValue = EditorGUI.ToggleLeft(togglePosition, label, (bool)metadata.value, labelStyle);
            }
            else
            {
                position = BeginBlock(metadata, position, label);
                var togglePosition = position.VerticalSection(ref y, EditorGUIUtility.singleLineHeight);
                newValue = EditorGUI.Toggle(togglePosition, (bool)metadata.value);
            }

            if (EndBlock(metadata))
            {
                metadata.RecordUndo();
                metadata.value = newValue;
            }
        }

        public override float GetAdaptiveWidth()
        {
            if (metadata.HasAttribute<InspectorToggleLeftAttribute>())
            {
                return 20;
            }
            else
            {
                return 14;
            }
        }
    }
}

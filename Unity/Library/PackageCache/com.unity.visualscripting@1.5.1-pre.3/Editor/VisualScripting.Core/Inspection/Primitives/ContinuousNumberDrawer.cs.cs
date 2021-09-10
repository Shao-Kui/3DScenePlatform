using System;
using UnityEditor;
using UnityEngine;

namespace Unity.VisualScripting
{
    public abstract class ContinuousNumberInspector<T> : Inspector
    {
        protected ContinuousNumberInspector(Metadata metadata) : base(metadata) {}

        protected override void OnGUI(Rect position, GUIContent label)
        {
            position = BeginBlock(metadata, position, label);

            T newValue;
            var oldValue = Convert.ToSingle(metadata.value);

            var fieldPosition = new Rect
                (
                position.x,
                position.y,
                position.width,
                EditorGUIUtility.singleLineHeight
                );

            if (metadata.HasAttribute<InspectorRangeAttribute>())
            {
                var rangeAttribute = metadata.GetAttribute<InspectorRangeAttribute>();

                newValue = (T)Convert.ChangeType(EditorGUI.Slider(fieldPosition, oldValue, rangeAttribute.min, rangeAttribute.max), typeof(T));
            }
            else
            {
                newValue = (T)Convert.ChangeType(LudiqGUI.DraggableFloatField(fieldPosition, oldValue), typeof(T));
            }

            if (EndBlock(metadata))
            {
                metadata.RecordUndo();
                metadata.value = newValue;
            }
        }

        protected override float GetHeight(float width, GUIContent label)
        {
            return HeightWithLabel(metadata, width, EditorGUIUtility.singleLineHeight, label);
        }

        public override float GetAdaptiveWidth()
        {
            if (metadata.HasAttribute<InspectorRangeAttribute>())
            {
                return 100;
            }
            else
            {
                return LudiqGUI.GetTextFieldAdaptiveWidth(metadata.value);
            }
        }
    }
}

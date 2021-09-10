using System;
using UnityEditor;
using UnityEngine;

namespace Unity.VisualScripting
{
    public class SystemObjectInspector : Inspector
    {
        public SystemObjectInspector(Metadata metadata) : base(metadata) {}

        public override void Initialize()
        {
            base.Initialize();

            typeFilter = metadata.GetAttribute<TypeFilter>() ?? TypeFilter.Any;
            metadata.valueChanged += (previousType) => InferType();
        }

        private TypeFilter _typeFilter;

        private Type type;

        public bool chooseType => true;

        public bool showValue => type != null && InspectorProvider.instance.GetDecoratorType(type) != typeof(SystemObjectInspector);

        public TypeFilter typeFilter
        {
            get
            {
                return _typeFilter;
            }
            private set
            {
                value = value.Clone().Configured();
                value.Abstract = false;
                value.Interfaces = false;
                value.Object = false;
                _typeFilter = value;
            }
        }

        private IFuzzyOptionTree GetTypeOptions()
        {
            return new TypeOptionTree(Codebase.GetTypeSetFromAttribute(metadata), typeFilter);
        }

        private void InferType()
        {
            var value = metadata.value;

            if (value == null)
            {
                return;
            }

            type = value.GetType();

            EnforceType();

            SetHeightDirty();
        }

        private void EnforceType()
        {
            if (metadata.value?.GetType() == type)
            {
                return;
            }

            metadata.UnlinkChildren();

            if (type == null)
            {
                metadata.value = null;
            }
            else if (ConversionUtility.CanConvert(metadata.value, type, true))
            {
                metadata.value = ConversionUtility.Convert(metadata.value, type);
            }
            else
            {
                metadata.value = type.TryInstantiate();
            }

            metadata.InferOwnerFromParent();
        }

        protected override void OnGUI(Rect position, GUIContent label)
        {
            // Super hacky hotfix:
            // If the value changes in between OnGUI calls,
            // the OnValueChange event will not be called, because
            // we don't even look at the value until showField is true.
            // For example, an object that was null and becomes non-null
            // will be reset to null by the inspector unless this line is here,
            // because type will be null and showField will thus be false.
            var haxHotfix = metadata.value;
            // TL;DR: storing a local private type field that does not
            // take the actual, current variable type into consideration is a
            // very bad idea and will inevitably cause inspector v. codebase fighting
            // or inspector v. inspector fighting.

            var showLabels = !adaptiveWidth && position.width >= 120;

            BeginBlock(metadata, position, GUIContent.none);

            if (chooseType)
            {
                var x = position.x;
                var remainingWidth = position.width;

                if (showLabels)
                {
                    var typeLabel = label == GUIContent.none ? new GUIContent("Type") : new GUIContent(label.text + " Type");

                    var typeLabelPosition = new Rect
                        (
                        x,
                        y,
                        Styles.labelWidth,
                        EditorGUIUtility.singleLineHeight
                        );

                    GUI.Label(typeLabelPosition, typeLabel, ProcessLabelStyle(metadata, null));

                    x += typeLabelPosition.width;
                    remainingWidth -= typeLabelPosition.width;
                }

                var typePosition = new Rect
                    (
                    x,
                    y,
                    remainingWidth,
                    EditorGUIUtility.singleLineHeight
                    );

                EditorGUI.BeginChangeCheck();

                var newType = LudiqGUI.TypeField(typePosition, GUIContent.none, type, GetTypeOptions, new GUIContent("(Null)"));

                if (EditorGUI.EndChangeCheck())
                {
                    metadata.RecordUndo();
                    type = newType;
                    EnforceType();
                    SetHeightDirty();
                }

                y += typePosition.height;
            }

            if (chooseType && showValue)
            {
                y += Styles.spaceBetweenTypeAndValue;
            }

            if (showValue)
            {
                Rect valuePosition;

                if (chooseType)
                {
                    var x = position.x;
                    var remainingWidth = position.width;

                    if (showLabels)
                    {
                        var valueLabel = label == GUIContent.none ? new GUIContent("Value") : new GUIContent(label.text + " Value");

                        var valueLabelPosition = new Rect
                            (
                            x,
                            y,
                            Styles.labelWidth,
                            EditorGUIUtility.singleLineHeight
                            );

                        GUI.Label(valueLabelPosition, valueLabel, ProcessLabelStyle(metadata, null));

                        x += valueLabelPosition.width;
                        remainingWidth -= valueLabelPosition.width;
                    }

                    valuePosition = new Rect
                        (
                        x,
                        y,
                        remainingWidth,
                        EditorGUIUtility.singleLineHeight
                        );

                    LudiqGUI.Inspector(metadata.Cast(type), valuePosition, GUIContent.none);
                }
                else
                {
                    valuePosition = new Rect
                        (
                        position.x,
                        y,
                        position.width,
                        LudiqGUI.GetInspectorHeight(this, metadata.Cast(type), position.width, label)
                        );

                    LudiqGUI.Inspector(metadata.Cast(type), valuePosition, label);
                }

                y += valuePosition.height;
            }
            else
            {
                metadata.value = null;
            }

            EndBlock(metadata);
        }

        protected override float GetHeight(float width, GUIContent label)
        {
            var height = 0f;

            if (chooseType)
            {
                height += EditorGUIUtility.singleLineHeight;
            }

            if (chooseType && showValue)
            {
                height += Styles.spaceBetweenTypeAndValue;
            }

            if (showValue)
            {
                height += LudiqGUI.GetInspectorHeight(this, metadata.Cast(type), width, GUIContent.none);
            }

            return HeightWithLabel(metadata, width, height, label);
        }

        public override float GetAdaptiveWidth()
        {
            var width = 0f;

            if (chooseType)
            {
                width = Mathf.Max(width, LudiqGUI.GetTypeFieldAdaptiveWidth(type, new GUIContent("(Null)")));
            }

            if (showValue)
            {
                width = Mathf.Max(width, LudiqGUI.GetInspectorAdaptiveWidth(metadata.Cast(type)));
            }

            width += Styles.labelWidth;

            return width;
        }

        public static class Styles
        {
            public static readonly float spaceBetweenTypeAndValue = 2;
            public static readonly float labelWidth = 38;
        }
    }
}

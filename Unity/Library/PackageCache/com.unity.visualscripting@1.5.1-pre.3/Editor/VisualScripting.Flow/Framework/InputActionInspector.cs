#if PACKAGE_INPUT_SYSTEM_EXISTS
using System.Linq;
using Unity.VisualScripting.FullSerializer;
using Unity.VisualScripting.InputSystem;
using UnityEditor;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Unity.VisualScripting
{
    [Inspector(typeof(InputAction))]
    public class InputActionInspector : Inspector
    {
        private readonly GraphReference m_Reference;
        private readonly OnInputSystemEvent m_InputSystemUnit;

        public InputActionInspector(Metadata metadata, GraphReference reference, OnInputSystemEvent inputSystemUnit) : base(metadata)
        {
            m_Reference = reference;
            m_InputSystemUnit = inputSystemUnit;
        }

        protected override float GetHeight(float width, GUIContent label) => EditorGUIUtility.singleLineHeight;
        public override float GetAdaptiveWidth()
        {
            return Mathf.Max(100, metadata.value is InputAction action && action.name != null
                ? (EditorStyles.popup.CalcSize(new GUIContent(action.name)).x + 1)
                : 0);
        }

        protected override void OnGUI(Rect position, GUIContent label)
        {
            position = BeginBlock(metadata, position, label);

            var togglePosition = position.VerticalSection(ref y, EditorGUIUtility.singleLineHeight);

            var inputActionAsset = Flow.Predict<PlayerInput>(m_InputSystemUnit.Target, m_Reference)?.actions;

            if (!inputActionAsset)
                EditorGUI.LabelField(togglePosition, "No Actions found");
            else
            {
                var value = metadata.value is InputAction ? (InputAction)metadata.value : default;

                int currentIndex = -1;
                if (value != null && value.id != default)
                {
                    int i = 0;
                    foreach (var playerInputAction in inputActionAsset)
                    {
                        if (playerInputAction.id == value.id)
                        {
                            currentIndex = i;
                            break;
                        }
                        i++;
                    }
                }

                var displayedOptions = Enumerable.Repeat(new GUIContent("<None>"), 1).Concat(inputActionAsset.Select(a => new GUIContent(a.name))).ToArray();
                currentIndex = EditorGUI.Popup(togglePosition, currentIndex + 1, displayedOptions);
                if (EndBlock(metadata))
                {
                    metadata.RecordUndo();
                    if (currentIndex == 0)
                        metadata.value = default;
                    else
                    {
                        var inputAction = inputActionAsset.ElementAt(currentIndex - 1);

                        metadata.value =
                            InputAction_DirectConverter.MakeInputActionWithId(inputAction.id.ToString(),
                                inputAction.name, inputAction.expectedControlType);
                    }
                }
                return;
            }

            EndBlock(metadata);
        }
    }
}
#endif

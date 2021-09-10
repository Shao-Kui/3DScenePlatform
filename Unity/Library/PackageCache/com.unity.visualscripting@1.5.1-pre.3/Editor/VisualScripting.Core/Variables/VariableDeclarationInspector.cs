using UnityEditor;
using UnityEngine;

namespace Unity.VisualScripting
{
    [Inspector(typeof(VariableDeclaration))]
    public sealed class VariableDeclarationInspector : Inspector
    {
        public VariableDeclarationInspector(Metadata metadata) : base(metadata) {}

        private Metadata nameMetadata => metadata[nameof(VariableDeclaration.name)];

        private Metadata valueMetadata => metadata[nameof(VariableDeclaration.value)];

        protected override float GetHeight(float width, GUIContent label)
        {
            var height = 0f;

            using (LudiqGUIUtility.labelWidth.Override(Styles.labelWidth))
            {
                height += Styles.padding;
                height += GetNameHeight(width);
                height += Styles.spacing;
                height += GetValueHeight(width);
                height += Styles.padding;
            }

            return height;
        }

        private float GetNameHeight(float width)
        {
            return EditorGUIUtility.singleLineHeight;
        }

        private float GetValueHeight(float width)
        {
            return LudiqGUI.GetInspectorHeight(this, valueMetadata, width);
        }

        protected override void OnGUI(Rect position, GUIContent label)
        {
            position = BeginBlock(metadata, position, label);

            using (LudiqGUIUtility.labelWidth.Override(Styles.labelWidth))
            {
                y += Styles.padding;
                var namePosition = position.VerticalSection(ref y, GetNameHeight(position.width));
                y += Styles.spacing;
                var valuePosition = position.VerticalSection(ref y, GetValueHeight(position.width));
                y += Styles.padding;

                OnNameGUI(namePosition);
                OnValueGUI(valuePosition);
            }

            EndBlock(metadata);
        }

        public void OnNameGUI(Rect namePosition)
        {
            namePosition = BeginBlock(nameMetadata, namePosition);

            var newName = EditorGUI.DelayedTextField(namePosition, (string)nameMetadata.value);

            if (EndBlock(nameMetadata))
            {
                var variableDeclarations = (VariableDeclarationCollection)metadata.parent.value;

                if (StringUtility.IsNullOrWhiteSpace(newName))
                {
                    EditorUtility.DisplayDialog("Edit Variable Name", "Please enter a variable name.", "OK");
                    return;
                }
                else if (variableDeclarations.Contains(newName))
                {
                    EditorUtility.DisplayDialog("Edit Variable Name", "A variable with the same name already exists.", "OK");
                    return;
                }

                nameMetadata.RecordUndo();
                variableDeclarations.EditorRename((VariableDeclaration)metadata.value, newName);
                nameMetadata.value = newName;
            }
        }

        public void OnValueGUI(Rect valuePosition)
        {
            LudiqGUI.Inspector(valueMetadata, valuePosition, GUIContent.none);
        }

        public static class Styles
        {
            public static readonly float labelWidth = SystemObjectInspector.Styles.labelWidth;
            public static readonly float padding = 2;
            public static readonly float spacing = EditorGUIUtility.standardVerticalSpacing;
        }
    }
}

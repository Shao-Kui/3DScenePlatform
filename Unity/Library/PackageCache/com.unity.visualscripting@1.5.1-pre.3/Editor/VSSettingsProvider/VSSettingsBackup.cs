using System.Diagnostics;
using UnityEditor;
using UnityEngine;

namespace Unity.VisualScripting
{
    public class VSSettingsBackup
    {
        private const string title = "Backup Graphs";
        private const string buttonBackupLabel = "Create Backup";
        private const string buttonRestoreLabel = "Restore Backup";

        public void OnGUI()
        {
            GUILayout.Space(5f);

            GUILayout.Label(title, EditorStyles.boldLabel);

            GUILayout.Space(5f);

            if (GUILayout.Button(buttonBackupLabel, Styles.defaultsButton))
            {
                VSBackupUtility.Backup();

                EditorUtility.DisplayDialog("Backup", "Backup completed successfully.", "OK");
            }

            if (GUILayout.Button(buttonRestoreLabel, Styles.defaultsButton))
            {
                PathUtility.CreateDirectoryIfNeeded(Paths.backups);
                Process.Start(Paths.backups);
            }
        }

        public static class Styles
        {
            static Styles()
            {
                defaultsButton = new GUIStyle("Button");
                defaultsButton.padding = new RectOffset(10, 10, 4, 4);
            }

            public static readonly GUIStyle defaultsButton;
        }
    }
}

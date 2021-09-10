using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEngine.Timeline;
using UnityEngine.UIElements;
#if !UNITY_2020_2_OR_NEWER
using L10n = UnityEditor.Timeline.L10n;
#endif

/// <summary>
/// Store the settings for Timeline that will be stored with the Unity Project.
/// </summary>
[FilePath("ProjectSettings/TimelineSettings.asset", FilePathAttribute.Location.ProjectFolder)]
public class TimelineProjectSettings : ScriptableSingleton<TimelineProjectSettings>
{
    /// <summary>
    /// Define the default framerate when a Timeline asset is created.
    /// </summary>
    [SerializeField]
    public float assetDefaultFramerate = TimelineAsset.EditorSettings.kDefaultFps;

    internal static string[] framerateLabels = new string[]
    {
        L10n.Tr("Film (24)"),
        L10n.Tr("PAL (25)"),
        L10n.Tr("NTSC (29.97)"),
        L10n.Tr("Film (30)"),
        L10n.Tr("Film (50)"),
        L10n.Tr("Film (60)"),
        L10n.Tr("Custom")
    };

    internal static float[] framerateValues = new float[]
    {
        24.0f,
        25.0f,
        29.97f,
        30.0f,
        50.0f,
        60.0f
    };

    void OnDisable()
    {
        Save();
    }

    /// <summary>
    /// Save the timeline project settings file in the project directory.
    /// </summary>
    public void Save()
    {
        Save(true);
    }

    internal SerializedObject GetSerializedObject()
    {
        return new SerializedObject(this);
    }
}

class TimelineProjectSettingsProvider : SettingsProvider
{
    SerializedObject m_SerializedObject;
    SerializedProperty m_Framerate;

    bool m_customFramerate;

    private class Styles
    {
        public static readonly GUIContent DefaultFramerateLabel = L10n.TextContent("Default Framerate", "Framerate value used for new Timeline Assets.");
        public static readonly GUIContent CustomFramerateLabel = L10n.TextContent("Custom Framerate", "Custom framerate value used for new Timeline Assets.");
        public static readonly GUIContent TimelineAssetLabel = L10n.TextContent("Timeline Asset", "");
    }

    public TimelineProjectSettingsProvider(string path, SettingsScope scopes, IEnumerable<string> keywords = null)
        : base(path, scopes, keywords) {}

    public override void OnActivate(string searchContext, VisualElement rootElement)
    {
        TimelineProjectSettings.instance.Save();
        m_SerializedObject = TimelineProjectSettings.instance.GetSerializedObject();
        m_Framerate = m_SerializedObject.FindProperty("assetDefaultFramerate");
    }

    public override void OnGUI(string searchContext)
    {
        using (new SettingsWindow.GUIScope())
        {
            m_SerializedObject.Update();
            EditorGUI.BeginChangeCheck();
            EditorGUILayout.LabelField(Styles.TimelineAssetLabel , EditorStyles.boldLabel);

            int framerateIdx = Array.IndexOf(TimelineProjectSettings.framerateValues, m_Framerate.floatValue);
            if (m_customFramerate || framerateIdx == -1)
            {
                framerateIdx = TimelineProjectSettings.framerateValues.Length;
            }

            framerateIdx = EditorGUILayout.Popup(Styles.DefaultFramerateLabel, framerateIdx, TimelineProjectSettings.framerateLabels);

            if (framerateIdx == TimelineProjectSettings.framerateValues.Length || framerateIdx == -1)
            {
                m_customFramerate = true;
                float newFramerate = EditorGUILayout.FloatField(Styles.CustomFramerateLabel, m_Framerate.floatValue);
                m_Framerate.floatValue = TimelineAsset.GetValidFramerate(newFramerate);
            }
            else
            {
                m_customFramerate = false;
                m_Framerate.floatValue = TimelineProjectSettings.framerateValues[framerateIdx];
            }

            if (EditorGUI.EndChangeCheck())
            {
                m_SerializedObject.ApplyModifiedProperties();
                TimelineProjectSettings.instance.Save();
            }
        }
    }

    [SettingsProvider]
    public static SettingsProvider CreateTimelineProjectSettingProvider()
    {
        var provider = new TimelineProjectSettingsProvider("Project/Timeline", SettingsScope.Project, GetSearchKeywordsFromGUIContentProperties<Styles>());
        return provider;
    }
}

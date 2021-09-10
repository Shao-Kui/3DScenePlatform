using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading;
using UnityEditor;
using UnityEngine;

namespace Unity.VisualScripting
{
    [InitializeAfterPlugins]
    public static class BackgroundWorker
    {
        static BackgroundWorker()
        {
            if (useProgressApi)
            {
                try
                {
                    ProgressType = typeof(EditorWindow).Assembly.GetType(("UnityEditor.Progress"), true);
                    Progress_OptionsType = ProgressType.GetNestedType("Options");
                    Progress_Start = ProgressType.GetMethod("Start", BindingFlags.Public | BindingFlags.Static, null, new[] { typeof(string), typeof(string), Progress_OptionsType, typeof(int) }, null);
                    Progress_Report = ProgressType.GetMethod("Report", BindingFlags.Public | BindingFlags.Static, null, new[] { typeof(int), typeof(float), typeof(string) }, null);
                    Progress_Remove = ProgressType.GetMethod("Remove", BindingFlags.Public | BindingFlags.Static, null, new[] { typeof(int) }, null);

                    if (Progress_Start == null)
                    {
                        throw new MissingMemberException(ProgressType.FullName, "Start");
                    }

                    if (Progress_Report == null)
                    {
                        throw new MissingMemberException(ProgressType.FullName, "Report");
                    }

                    if (Progress_Remove == null)
                    {
                        throw new MissingMemberException(ProgressType.FullName, "Remove");
                    }
                }
                catch (Exception ex)
                {
                    throw new UnityEditorInternalException(ex);
                }
            }
            else
            {
                try
                {
                    AsyncProgressBarType = typeof(EditorWindow).Assembly.GetType("UnityEditor.AsyncProgressBar", true);
                    AsyncProgressBar_Display = AsyncProgressBarType.GetMethod("Display", BindingFlags.Static | BindingFlags.Public);
                    AsyncProgressBar_Clear = AsyncProgressBarType.GetMethod("Clear", BindingFlags.Static | BindingFlags.Public);

                    if (AsyncProgressBar_Display == null)
                    {
                        throw new MissingMemberException(AsyncProgressBarType.FullName, "Display");
                    }

                    if (AsyncProgressBar_Clear == null)
                    {
                        throw new MissingMemberException(AsyncProgressBarType.FullName, "Clear");
                    }
                }
                catch (Exception ex)
                {
                    throw new UnityEditorInternalException(ex);
                }
            }

            queue = new Queue<Action>();

            ClearProgress();

            foreach (var type in Codebase.ludiqEditorTypes.Where(type => type.HasAttribute<BackgroundWorkerAttribute>(false)))
            {
                foreach (var attribute in type.GetAttributes<BackgroundWorkerAttribute>().DistinctBy(bwa => bwa.methodName))
                {
                    var backgroundWorkMethod = type.GetMethod(attribute.methodName, BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic, null, Type.EmptyTypes, null);

                    if (backgroundWorkMethod != null)
                    {
                        tasks += () => backgroundWorkMethod.Invoke(null, new object[0]);
                    }
                    else
                    {
                        Debug.LogWarningFormat($"Missing '{attribute.methodName}' method for '{type}' background worker.");
                    }
                }
            }

            EditorApplication.update += DisplayProgress;

            EditorApplication.delayCall += delegate { new Thread(Work) { Name = "Background Worker" }.Start(); };
        }

        private static readonly object @lock = new object();
        private static bool clearProgress;

        private static readonly bool useProgressApi = EditorApplicationUtility.unityVersion >= "2020.1.0";

        private static readonly Type AsyncProgressBarType; // internal sealed class AsyncProgressBar
        private static readonly MethodInfo AsyncProgressBar_Display; // public static extern void AsyncStatusBar.Display(string progressInfo, float progress);
        private static readonly MethodInfo AsyncProgressBar_Clear; // public static extern void AsyncStatusBar.Clear();

        private static int progressId = -1;
        private static readonly Type ProgressType; // public static partial class Progress
        private static readonly Type Progress_OptionsType; // public enum Progress.Options
        private static readonly MethodInfo Progress_Start; // public static int Start(string name, string description = null, Options options = Options.None, int parentId = -1)
        private static readonly MethodInfo Progress_Report; // public static void Report(int id, float progress, string description)
        private static readonly MethodInfo Progress_Remove; // public static extern int Remove(int id);

        private static readonly Queue<Action> queue;

        public static event Action tasks
        {
            add
            {
                Schedule(value);
            }
            remove {}
        }

        public static string progressLabel { get; private set; }
        public static float progressProportion { get; private set; }
        public static bool hasProgress => progressLabel != null;

        public static void Schedule(Action action)
        {
            lock (queue)
            {
                queue.Enqueue(action);
            }
        }

        private static void Work()
        {
            while (true)
            {
                Action task = null;
                var remaining = 0;

                lock (queue)
                {
                    if (queue.Count > 0)
                    {
                        remaining = queue.Count;
                        task = queue.Dequeue();
                    }
                }

                if (task != null)
                {
                    ReportProgress($"{remaining} task{(queue.Count > 1 ? "s" : "")} remaining...", 0);

                    try
                    {
                        task();
                    }
                    catch (Exception ex)
                    {
                        EditorApplication.delayCall += () => Debug.LogException(ex);
                    }
                    finally
                    {
                        ClearProgress();
                    }
                }
                else
                {
                    Thread.Sleep(100);
                }
            }
        }

        public static void ReportProgress(string title, float progress)
        {
            lock (@lock)
            {
                progressLabel = title;
                progressProportion = progress;
            }
        }

        public static void ClearProgress()
        {
            lock (@lock)
            {
                clearProgress = true;
                progressLabel = null;
                progressProportion = 0;
            }
        }

        private static void DisplayProgress()
        {
            lock (@lock)
            {
                if (clearProgress)
                {
                    if (useProgressApi)
                    {
                        try
                        {
                            if (progressId != -1)
                            {
                                progressId = (int)Progress_Remove.InvokeOptimized(null, progressId);
                            }
                        }
                        catch (Exception ex)
                        {
                            throw new UnityEditorInternalException(ex);
                        }
                    }
                    else
                    {
                        try
                        {
                            AsyncProgressBar_Clear.InvokeOptimized(null);
                        }
                        catch (Exception ex)
                        {
                            throw new UnityEditorInternalException(ex);
                        }
                    }

                    clearProgress = false;
                }

                if (progressLabel != null)
                {
                    if (useProgressApi)
                    {
                        try
                        {
                            if (progressId == -1)
                            {
                                progressId = (int)Progress_Start.InvokeOptimized(null, "Ludiq Background Worker", progressLabel, Enum.ToObject(Progress_OptionsType, 0), -1);
                            }
                            else
                            {
                                Progress_Report.InvokeOptimized(null, progressId, progressProportion, progressLabel);
                            }
                        }
                        catch (Exception ex)
                        {
                            throw new UnityEditorInternalException(ex);
                        }
                    }
                    else
                    {
                        try
                        {
                            AsyncProgressBar_Display.InvokeOptimized(null, progressLabel, progressProportion);
                        }
                        catch (Exception ex)
                        {
                            throw new UnityEditorInternalException(ex);
                        }
                    }
                }
            }
        }
    }
}

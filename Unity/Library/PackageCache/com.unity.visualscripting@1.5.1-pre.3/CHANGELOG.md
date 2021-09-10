# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [1.5.1] - 2020-12-07
### Added
- Added Visual Scripting as built-in package as of Unity 2021.1
- Added New Input System Support. You can import the Input System package, activate the back-end and regenerate units to use.
- Added AOT Pre-Compile to automatically run when building AOT platforms
- Improved UI for deprecated built-in nodes
- Added automatic unit generation the first time the graph window is opened
### Changed
- Switched to delivering source instead of pre-built .NET 3/4 assemblies
- Updated Documentation
- Renamed assemblies to match Unity.VisualScripting naming scheme (Ex: Bolt.Core -> Unity.VisualScripting.Core)
- Merged Ludiq.Core and Ludiq.Graphs into Unity.VisualScripting.Core
- Moved Setup Wizard contents from pop-up on Editor startup to Player Settings. You can change the default settings from "Player Settings > Visual Scripting"
- Renamed "Assembly Options" to "Node Library"
- Renamed "Flow Graph" to "Script Graph"
- Renamed "Flow Machine" to "Script Machine"
- Renamed "Macro" graphs to "Graph" in machine source configuration and "GraphAsset" in Assets
- Renamed "Control Input/Output" to "Trigger Input/Output"
- Renamed "Value Input/Output" to "Data Input/Output"
- Updated built-in nodes. The Fuzzy Finder still accepts earlier version names of nodes.
- Renamed "Branch" node to "If"
- Renamed "Self" node to "This"
- Deprecated the previous Add unit. The Sum unit has been renamed to Add.
- Updated Window Naming   
- Changed "Variables" window to "Blackboard"
- Changed "Graph" window to "Script Graph" and "State Graph"
- Updated Bolt Preferences
- Renamed Bolt Preferences to "Visual Scripting"
- Removed BoltEx
- Moved settings previously accessed from "Window > Bolt" to preferences
- Renamed Control Schemes from "Unity/Unreal" to "Default/Alternate" (Neither control scheme currently matches their respective editors' controls and will be updated in a future release)
- Consolidated Graph editor, Blackboard and Graph Inspector into a single window
- Updated Third-Party Notices
### Fixed
- Corrected UGUI event management to trickle down correctly when the hierarchy contains a Unity Message Listener [BOLT-2](https://issuetracker.unity3d.com/issues/bolt-1-unity-message-listener-blocks-proper-trickling-of-ugui-events-in-hierarchies)
- Fixed backup failures with large projects [BOLT-10](https://issuetracker.unity3d.com/issues/bolt-1-backup-fails-to-complete)
- Fixed "Null Reference" when opening the Graph Window for the first time [BOLT-996](https://issuetracker.unity3d.com/issues/nullreferenceexception-when-graph-window-is-opened-on-a-new-project)
- Fixed IL2CPP build crash on startup [BOLT-1036](https://issuetracker.unity3d.com/issues/bolt-bolt-1-il2cpp-release-build-crashes-on-startup-when-there-is-at-least-1-node-present-in-a-graph)
- Fixed IL2CPP issue around converting certain managed types [BOLT-8](https://issuetracker.unity3d.com/issues/bolt-1-il2cpp-encountered-a-managed-type-which-it-cannot-convert-ahead-of-time)
- Fixed deserialization issues when undoing graphs with Wait nodes [BOLT-679](https://issuetracker.unity3d.com/issues/bolt-deserialization-error-and-nodes-missing-after-pressing-undo-when-update-coroutine-with-wait-node-is-present-in-graph)
- Fixed "SelectOnEnum" node behavior enums containing non-unique values e.g. "RuntimePlatform" [BOLT-688](https://issuetracker.unity3d.com/issues/select-on-enum-doesnt-work-with-the-runtimeplatform-enum)

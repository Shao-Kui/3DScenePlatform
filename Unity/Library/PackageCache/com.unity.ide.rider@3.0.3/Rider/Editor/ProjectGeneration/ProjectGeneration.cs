using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security;
using System.Text;
using System.Text.RegularExpressions;
using Packages.Rider.Editor.Util;
using UnityEditor;
using UnityEditor.Compilation;
using UnityEditorInternal;
using UnityEngine;

namespace Packages.Rider.Editor.ProjectGeneration
{
  internal class ProjectGeneration : IGenerator
  {
    private enum ScriptingLanguage
    {
      None,
      CSharp
    }

    public static readonly string MSBuildNamespaceUri = "http://schemas.microsoft.com/developer/msbuild/2003";

    /// <summary>
    /// Map source extensions to ScriptingLanguages
    /// </summary>
    private static readonly Dictionary<string, ScriptingLanguage> k_BuiltinSupportedExtensions =
      new Dictionary<string, ScriptingLanguage>
      {
        { "cs", ScriptingLanguage.CSharp },
        { "uxml", ScriptingLanguage.None },
        { "uss", ScriptingLanguage.None },
        { "shader", ScriptingLanguage.None },
        { "compute", ScriptingLanguage.None },
        { "cginc", ScriptingLanguage.None },
        { "hlsl", ScriptingLanguage.None },
        { "glslinc", ScriptingLanguage.None },
        { "template", ScriptingLanguage.None },
        { "raytrace", ScriptingLanguage.None }
      };

    private string m_SolutionProjectEntryTemplate = string.Join(Environment.NewLine,
      @"Project(""{{{0}}}"") = ""{1}"", ""{2}"", ""{{{3}}}""",
      @"EndProject").Replace("    ", "\t");

    private string m_SolutionProjectConfigurationTemplate = string.Join(Environment.NewLine,
      @"        {{{0}}}.Debug|Any CPU.ActiveCfg = Debug|Any CPU",
      @"        {{{0}}}.Debug|Any CPU.Build.0 = Debug|Any CPU").Replace("    ", "\t");

    private static readonly string[] k_ReimportSyncExtensions = { ".dll", ".asmdef" };

    /// <summary>
    /// Map ScriptingLanguages to project extensions
    /// </summary>
    /*static readonly Dictionary<ScriptingLanguage, string> k_ProjectExtensions = new Dictionary<ScriptingLanguage, string>
    {
        { ScriptingLanguage.CSharp, ".csproj" },
        { ScriptingLanguage.None, ".csproj" },
    };*/
    private static readonly Regex k_ScriptReferenceExpression = new Regex(
      @"^Library.ScriptAssemblies.(?<dllname>(?<project>.*)\.dll$)",
      RegexOptions.Compiled | RegexOptions.IgnoreCase);

    private string[] m_ProjectSupportedExtensions = new string[0];

    public string ProjectDirectory { get; }

    private readonly string m_ProjectName;
    private readonly IAssemblyNameProvider m_AssemblyNameProvider;
    private readonly IFileIO m_FileIOProvider;
    private readonly IGUIDGenerator m_GUIDGenerator;

    internal static bool isRiderProjectGeneration; // workaround to https://github.cds.internal.unity3d.com/unity/com.unity.ide.rider/issues/28

    private const string k_ToolsVersion = "4.0";
    private const string k_ProductVersion = "10.0.20506";
    private const string k_BaseDirectory = ".";
    private const string k_TargetFrameworkVersion = "v4.7.1";
    private const string k_TargetLanguageVersion = "latest";

    IAssemblyNameProvider IGenerator.AssemblyNameProvider => m_AssemblyNameProvider;

    public ProjectGeneration()
      : this(Directory.GetParent(Application.dataPath).FullName) { }

    public ProjectGeneration(string tempDirectory)
      : this(tempDirectory, new AssemblyNameProvider(), new FileIOProvider(), new GUIDProvider()) { }

    public ProjectGeneration(string tempDirectory, IAssemblyNameProvider assemblyNameProvider, IFileIO fileIoProvider, IGUIDGenerator guidGenerator)
    {
      ProjectDirectory = tempDirectory.Replace('\\', '/');
      m_ProjectName = Path.GetFileName(ProjectDirectory);
      m_AssemblyNameProvider = assemblyNameProvider;
      m_FileIOProvider = fileIoProvider;
      m_GUIDGenerator = guidGenerator;
    }

    /// <summary>
    /// Syncs the scripting solution if any affected files are relevant.
    /// </summary>
    /// <returns>
    /// Whether the solution was synced.
    /// </returns>
    /// <param name='affectedFiles'>
    /// A set of files whose status has changed
    /// </param>
    /// <param name="reimportedFiles">
    /// A set of files that got reimported
    /// </param>
    public bool SyncIfNeeded(IEnumerable<string> affectedFiles, IEnumerable<string> reimportedFiles)
    {
      SetupProjectSupportedExtensions();

      if (HasFilesBeenModified(affectedFiles, reimportedFiles) || RiderScriptEditorData.instance.hasChanges || RiderScriptEditorData.instance.HasChangesInCompilationDefines())
      {
        Sync();
        RiderScriptEditorData.instance.hasChanges = false;
        RiderScriptEditorData.instance.InvalidateSavedCompilationDefines();
        return true;
      }

      return false;
    }

    private bool HasFilesBeenModified(IEnumerable<string> affectedFiles, IEnumerable<string> reimportedFiles)
    {
      return affectedFiles.Any(ShouldFileBePartOfSolution) || reimportedFiles.Any(ShouldSyncOnReimportedAsset);
    }

    private static bool ShouldSyncOnReimportedAsset(string asset)
    {
      return k_ReimportSyncExtensions.Contains(Path.GetExtension(asset)) || Path.GetFileName(asset) == "csc.rsp";
    }

    public void Sync()
    {
      SetupProjectSupportedExtensions();
      var types = GetAssetPostprocessorTypes();
      isRiderProjectGeneration = true;
      var externalCodeAlreadyGeneratedProjects = OnPreGeneratingCSProjectFiles(types);
      isRiderProjectGeneration = false;
      if (!externalCodeAlreadyGeneratedProjects)
      {
        GenerateAndWriteSolutionAndProjects(types);
      }

      OnGeneratedCSProjectFiles(types);
    }

    public bool HasSolutionBeenGenerated()
    {
      return m_FileIOProvider.Exists(SolutionFile());
    }

    private void SetupProjectSupportedExtensions()
    {
      m_ProjectSupportedExtensions = m_AssemblyNameProvider.ProjectSupportedExtensions;
    }

    private bool ShouldFileBePartOfSolution(string file)
    {
      // Exclude files coming from packages except if they are internalized.
      if (m_AssemblyNameProvider.IsInternalizedPackagePath(file))
      {
          return false;
      }
      return HasValidExtension(file);
    }

    private bool HasValidExtension(string file)
    {
      var extension = Path.GetExtension(file);

      // Dll's are not scripts but still need to be included..
      if (extension.Equals(".dll", StringComparison.OrdinalIgnoreCase))
          return true;

      if (extension.Equals(".asmdef", StringComparison.OrdinalIgnoreCase))
        return true;

      return IsSupportedExtension(extension);
    }

    private bool IsSupportedExtension(string extension)
    {
      extension = extension.TrimStart('.');
      return k_BuiltinSupportedExtensions.ContainsKey(extension) || m_ProjectSupportedExtensions.Contains(extension);
    }

    public void GenerateAndWriteSolutionAndProjects(Type[] types)
    {
      // Only synchronize islands that have associated source files and ones that we actually want in the project.
      // This also filters out DLLs coming from .asmdef files in packages.
      var assemblies = m_AssemblyNameProvider.GetAssemblies(ShouldFileBePartOfSolution).ToArray();
      var assemblyNames = new HashSet<string>(assemblies.Select(a => a.name));
      var allAssetProjectParts = GenerateAllAssetProjectParts();

      var projectParts = new List<ProjectPart>();
      foreach (var assembly in assemblies)
      {
        allAssetProjectParts.TryGetValue(assembly.name, out var additionalAssetsForProject);
        projectParts.Add(new ProjectPart(assembly.name, assembly, additionalAssetsForProject));
      }

      var projectPartsWithoutAssembly = allAssetProjectParts.Where(a => !assemblyNames.Contains(a.Key));
      projectParts.AddRange(projectPartsWithoutAssembly.Select(allAssetProjectPart => new ProjectPart(allAssetProjectPart.Key, null, allAssetProjectPart.Value)));

      SyncSolution(projectParts.ToArray(), types);
      
      foreach (var projectPart in projectParts)
      {
        SyncProject(projectPart, types, GetAllRoslynAnalyzerPaths().ToArray());
      }
    }

    private IEnumerable<string> GetAllRoslynAnalyzerPaths()
    {
      return m_AssemblyNameProvider.GetRoslynAnalyzerPaths();
    }

    private Dictionary<string, string> GenerateAllAssetProjectParts()
    {
      var stringBuilders = new Dictionary<string, StringBuilder>();

      foreach (var asset in m_AssemblyNameProvider.GetAllAssetPaths())
      {
        // Exclude files coming from packages except if they are internalized.
        if (m_AssemblyNameProvider.IsInternalizedPackagePath(asset))
        {
          continue;
        }

        var extension = Path.GetExtension(asset);
        if (IsSupportedExtension(extension) && !extension.Equals(".cs", StringComparison.OrdinalIgnoreCase))
        {
          // Find assembly the asset belongs to by adding script extension and using compilation pipeline.
          var assemblyName = m_AssemblyNameProvider.GetAssemblyNameFromScriptPath(asset + ".cs");

          if (string.IsNullOrEmpty(assemblyName))
          {
            continue;
          }

          assemblyName = FileSystemUtil.FileNameWithoutExtension(assemblyName);

          if (!stringBuilders.TryGetValue(assemblyName, out var projectBuilder))
          {
            projectBuilder = new StringBuilder();
            stringBuilders[assemblyName] = projectBuilder;
          }

          projectBuilder.Append("     <None Include=\"").Append(EscapedRelativePathFor(asset)).Append("\" />")
            .Append(Environment.NewLine);
        }
      }

      var result = new Dictionary<string, string>();

      foreach (var entry in stringBuilders)
        result[entry.Key] = entry.Value.ToString();

      return result;
    }

    private void SyncProject(
      ProjectPart island,
      Type[] types,
      string[] roslynAnalyzerDllPaths)
    {
      SyncProjectFileIfNotChanged(
        ProjectFile(island),
        ProjectText(island, roslynAnalyzerDllPaths),
        types);
    }

    private void SyncProjectFileIfNotChanged(string path, string newContents, Type[] types)
    {
      if (Path.GetExtension(path) == ".csproj")
      {
        newContents = OnGeneratedCSProject(path, newContents, types);
      }

      SyncFileIfNotChanged(path, newContents);
    }

    private void SyncSolutionFileIfNotChanged(string path, string newContents, Type[] types)
    {
      newContents = OnGeneratedSlnSolution(path, newContents, types);

      SyncFileIfNotChanged(path, newContents);
    }

    private static void OnGeneratedCSProjectFiles(Type[] types)
    {
      foreach (var type in types)
      {
        var method = type.GetMethod("OnGeneratedCSProjectFiles",
          System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic |
          System.Reflection.BindingFlags.Static);
        if (method == null)
        {
          continue;
        }

        Debug.LogWarning("OnGeneratedCSProjectFiles is not supported.");
        // RIDER-51958
        //method.Invoke(null, args);
      }
    }

    public static Type[] GetAssetPostprocessorTypes()
    {
      return TypeCache.GetTypesDerivedFrom<AssetPostprocessor>().ToArray(); // doesn't find types from EditorPlugin, which is fine
    }

    private static bool OnPreGeneratingCSProjectFiles(Type[] types)
    {
      var result = false;
      foreach (var type in types)
      {
        var args = new object[0];
        var method = type.GetMethod("OnPreGeneratingCSProjectFiles",
          System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic |
          System.Reflection.BindingFlags.Static);
        if (method == null)
        {
          continue;
        }

        var returnValue = method.Invoke(null, args);
        if (method.ReturnType == typeof(bool))
        {
          result |= (bool)returnValue;
        }
      }

      return result;
    }

    private static string OnGeneratedCSProject(string path, string content, Type[] types)
    {
      foreach (var type in types)
      {
        var args = new[] { path, content };
        var method = type.GetMethod("OnGeneratedCSProject",
          System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic |
          System.Reflection.BindingFlags.Static);
        if (method == null)
        {
          continue;
        }

        var returnValue = method.Invoke(null, args);
        if (method.ReturnType == typeof(string))
        {
          content = (string)returnValue;
        }
      }

      return content;
    }

    private static string OnGeneratedSlnSolution(string path, string content, Type[] types)
    {
      foreach (var type in types)
      {
        var args = new[] { path, content };
        var method = type.GetMethod("OnGeneratedSlnSolution",
          System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic |
          System.Reflection.BindingFlags.Static);
        if (method == null)
        {
          continue;
        }

        var returnValue = method.Invoke(null, args);
        if (method.ReturnType == typeof(string))
        {
          content = (string)returnValue;
        }
      }

      return content;
    }

    private void SyncFileIfNotChanged(string filename, string newContents)
    {
      try
      {
        if (m_FileIOProvider.Exists(filename) && newContents == m_FileIOProvider.ReadAllText(filename))
        {
          return;
        }
      }
      catch (Exception exception)
      {
        Debug.LogException(exception);
      }

      m_FileIOProvider.WriteAllText(filename, newContents);
    }

    private string ProjectText(ProjectPart assembly,
      string[] roslynAnalyzerDllPaths)
    {
      var responseFilesData = assembly.ParseResponseFileData(m_AssemblyNameProvider, ProjectDirectory).ToList();
      var projectBuilder = new StringBuilder(ProjectHeader(assembly, responseFilesData, roslynAnalyzerDllPaths));
      
      foreach (var file in assembly.SourceFiles)
      {
        var fullFile = EscapedRelativePathFor(file);
        projectBuilder.Append("     <Compile Include=\"").Append(fullFile).Append("\" />").Append(Environment.NewLine);
      }

      projectBuilder.Append(assembly.AssetsProjectPart);

      var responseRefs = responseFilesData.SelectMany(x => x.FullPathReferences.Select(r => r));
      var internalAssemblyReferences = assembly.AssemblyReferences
        .Where(reference => !reference.sourceFiles.Any(ShouldFileBePartOfSolution)).Select(i => i.outputPath);
      var allReferences =
        assembly.CompiledAssemblyReferences
          .Union(responseRefs)
          .Union(internalAssemblyReferences).ToArray();

      foreach (var reference in allReferences)
      {
        var fullReference = Path.IsPathRooted(reference) ? reference : Path.Combine(ProjectDirectory, reference);
        AppendReference(fullReference, projectBuilder);
      }

      if (0 < assembly.AssemblyReferences.Length)
      {
        projectBuilder.Append("  </ItemGroup>").Append(Environment.NewLine);
        projectBuilder.Append("  <ItemGroup>").Append(Environment.NewLine);
        foreach (var reference in assembly.AssemblyReferences.Where(i => i.sourceFiles.Any(ShouldFileBePartOfSolution)))
        {
          projectBuilder.Append("    <ProjectReference Include=\"").Append(reference.name).Append(GetProjectExtension()).Append("\">").Append(Environment.NewLine);
          projectBuilder.Append("      <Project>{").Append(ProjectGuid(reference.name, reference.outputPath)).Append("}</Project>").Append(Environment.NewLine);
          projectBuilder.Append("      <Name>").Append(reference.name).Append("</Name>").Append(Environment.NewLine);
          projectBuilder.Append("    </ProjectReference>").Append(Environment.NewLine);
        }
      }

      projectBuilder.Append(ProjectFooter());
      return projectBuilder.ToString();
    }

    private static void AppendReference(string fullReference, StringBuilder projectBuilder)
    {
      //replace \ with / and \\ with /
      var escapedFullPath = SecurityElement.Escape(fullReference);
      escapedFullPath = escapedFullPath.Replace("\\\\", "/").Replace("\\", "/");
      projectBuilder.Append("     <Reference Include=\"").Append(FileSystemUtil.FileNameWithoutExtension(escapedFullPath))
        .Append("\">").Append(Environment.NewLine);
      projectBuilder.Append("     <HintPath>").Append(escapedFullPath).Append("</HintPath>").Append(Environment.NewLine);
      projectBuilder.Append("     </Reference>").Append(Environment.NewLine);
    }

    private string ProjectFile(ProjectPart projectPart)
    {
      return Path.Combine(ProjectDirectory, $"{m_AssemblyNameProvider.GetProjectName(projectPart.OutputPath, projectPart.Name)}.csproj");
    }

    public string SolutionFile()
    {
      return Path.Combine(ProjectDirectory, $"{m_ProjectName}.sln");
    }

    private string ProjectHeader(
      ProjectPart assembly,
      List<ResponseFileData> responseFilesData,
      string[] roslynAnalyzerDllPaths
    )
    {
      var otherResponseFilesData = GetOtherArgumentsFromResponseFilesData(responseFilesData);
      var arguments = new object[]
      {
        k_ToolsVersion,
        k_ProductVersion,
        ProjectGuid(assembly.Name, assembly.OutputPath),
        InternalEditorUtility.GetEngineAssemblyPath(),
        InternalEditorUtility.GetEditorAssemblyPath(),
        string.Join(";", assembly.Defines.Concat(responseFilesData.SelectMany(x => x.Defines)).Distinct().ToArray()),
        MSBuildNamespaceUri,
        assembly.Name,
        assembly.OutputPath,
        assembly.RootNamespace,
        k_TargetFrameworkVersion,
        GenerateLangVersion(otherResponseFilesData["langversion"]),
        k_BaseDirectory,
        assembly.CompilerOptions.AllowUnsafeCode | responseFilesData.Any(x => x.Unsafe),
        GenerateNoWarn(otherResponseFilesData["nowarn"].Distinct().ToArray()),
        GenerateAnalyserItemGroup(
          otherResponseFilesData["analyzer"].Concat(otherResponseFilesData["a"])
                                                  .SelectMany(x=>x.Split(';'))
                                                  .Concat(roslynAnalyzerDllPaths)
                                                  .Distinct()
                                                  .ToArray()),
        GenerateAnalyserAdditionalFiles(otherResponseFilesData["additionalfile"].SelectMany(x=>x.Split(';')).Distinct().ToArray()),
        #if UNITY_2020_2_OR_NEWER
        GenerateAnalyserRuleSet(otherResponseFilesData["ruleset"].Append(assembly.CompilerOptions.RoslynAnalyzerRulesetPath).Where(a=>!string.IsNullOrEmpty(a)).Distinct().ToArray()),
        #else
        GenerateAnalyserRuleSet(otherResponseFilesData["ruleset"].Distinct().ToArray()),
        #endif
        GenerateWarningLevel(otherResponseFilesData["warn"].Concat(otherResponseFilesData["w"]).Distinct()),
        GenerateWarningAsError(otherResponseFilesData["warnaserror"]),
        GenerateDocumentationFile(otherResponseFilesData["doc"].ToArray())
      };

      try
      {
        return string.Format(GetProjectHeaderTemplate(), arguments);
      }
      catch (Exception)
      {
        throw new NotSupportedException(
          "Failed creating c# project because the c# project header did not have the correct amount of arguments, which is " +
          arguments.Length);
      }
    }

    private static string GenerateDocumentationFile(string[] paths)
    {
      if (!paths.Any())
        return String.Empty;

      return $"{Environment.NewLine}{string.Join(Environment.NewLine, paths.Select(a => $"  <DocumentationFile>{a}</DocumentationFile>"))}";
    }

    private static string GenerateWarningAsError(IEnumerable<string> enumerable)
    {
      var returnValue = String.Empty;
      var allWarningsAsErrors = false;
      var warningIds = new List<string>();

      foreach (var s in enumerable)
      {
        if (s == "+") allWarningsAsErrors = true;
        else if (s == "-") allWarningsAsErrors = false;
        else
        {
          warningIds.Add(s);
        }
      }

      returnValue += $@"    <TreatWarningsAsErrors>{allWarningsAsErrors}</TreatWarningsAsErrors>";
      if (warningIds.Any())
      {
        returnValue += $"{Environment.NewLine}    <WarningsAsErrors>{string.Join(";", warningIds)}</WarningsAsErrors>";
      }

      return $"{Environment.NewLine}{returnValue}";
    }

    private static string GenerateWarningLevel(IEnumerable<string> warningLevel)
    {
      var level = warningLevel.FirstOrDefault();
      if (!string.IsNullOrWhiteSpace(level))
        return level;

      return 4.ToString();
    }

    private static string GetSolutionText()
    {
      return string.Join(Environment.NewLine,
        @"",
        @"Microsoft Visual Studio Solution File, Format Version {0}",
        @"# Visual Studio {1}",
        @"{2}",
        @"Global",
        @"    GlobalSection(SolutionConfigurationPlatforms) = preSolution",
        @"        Debug|Any CPU = Debug|Any CPU",
        @"    EndGlobalSection",
        @"    GlobalSection(ProjectConfigurationPlatforms) = postSolution",
        @"{3}",
        @"    EndGlobalSection",
        @"    GlobalSection(SolutionProperties) = preSolution",
        @"        HideSolutionNode = FALSE",
        @"    EndGlobalSection",
        @"EndGlobal",
        @"").Replace("    ", "\t");
    }

    private static string GetProjectFooterTemplate()
    {
      return string.Join(Environment.NewLine,
        @"  </ItemGroup>",
        @"  <Import Project=""$(MSBuildToolsPath)\Microsoft.CSharp.targets"" />",
        @"  <!-- To modify your build process, add your task inside one of the targets below and uncomment it.",
        @"       Other similar extension points exist, see Microsoft.Common.targets.",
        @"  <Target Name=""BeforeBuild"">",
        @"  </Target>",
        @"  <Target Name=""AfterBuild"">",
        @"  </Target>",
        @"  -->",
        @"</Project>",
        @"");
    }

    private static string GetProjectHeaderTemplate()
    {
      var header = new[]
      {
        @"<?xml version=""1.0"" encoding=""utf-8""?>",
        @"<Project ToolsVersion=""{0}"" DefaultTargets=""Build"" xmlns=""{6}"">",
        @"  <PropertyGroup>",
        @"    <LangVersion>{11}</LangVersion>",
        @"    <_TargetFrameworkDirectories>non_empty_path_generated_by_unity.rider.package</_TargetFrameworkDirectories>",
        @"    <_FullFrameworkReferenceAssemblyPaths>non_empty_path_generated_by_unity.rider.package</_FullFrameworkReferenceAssemblyPaths>",
        @"    <DisableHandlePackageFileConflicts>true</DisableHandlePackageFileConflicts>{17}",
        @"  </PropertyGroup>",
        @"  <PropertyGroup>",
        @"    <Configuration Condition="" '$(Configuration)' == '' "">Debug</Configuration>",
        @"    <Platform Condition="" '$(Platform)' == '' "">AnyCPU</Platform>",
        @"    <ProductVersion>{1}</ProductVersion>",
        @"    <SchemaVersion>2.0</SchemaVersion>",
        @"    <RootNamespace>{9}</RootNamespace>",
        @"    <ProjectGuid>{{{2}}}</ProjectGuid>",
        @"    <ProjectTypeGuids>{{E097FAD1-6243-4DAD-9C02-E9B9EFC3FFC1}};{{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}}</ProjectTypeGuids>",
        @"    <OutputType>Library</OutputType>",
        @"    <AppDesignerFolder>Properties</AppDesignerFolder>",
        @"    <AssemblyName>{7}</AssemblyName>",
        @"    <TargetFrameworkVersion>{10}</TargetFrameworkVersion>",
        @"    <FileAlignment>512</FileAlignment>",
        @"    <BaseDirectory>{12}</BaseDirectory>",
        @"  </PropertyGroup>",
        @"  <PropertyGroup Condition="" '$(Configuration)|$(Platform)' == 'Debug|AnyCPU' "">",
        @"    <DebugSymbols>true</DebugSymbols>",
        @"    <DebugType>full</DebugType>",
        @"    <Optimize>false</Optimize>",
        @"    <OutputPath>{8}</OutputPath>",
        @"    <DefineConstants>{5}</DefineConstants>",
        @"    <ErrorReport>prompt</ErrorReport>",
        @"    <WarningLevel>{18}</WarningLevel>",
        @"    <NoWarn>{14}</NoWarn>",
        @"    <AllowUnsafeBlocks>{13}</AllowUnsafeBlocks>{19}{20}",
        @"  </PropertyGroup>"
      };

      var forceExplicitReferences = new[]
      {
        @"  <PropertyGroup>",
        @"    <NoConfig>true</NoConfig>",
        @"    <NoStdLib>true</NoStdLib>",
        @"    <AddAdditionalExplicitAssemblyReferences>false</AddAdditionalExplicitAssemblyReferences>",
        @"    <ImplicitlyExpandNETStandardFacades>false</ImplicitlyExpandNETStandardFacades>",
        @"    <ImplicitlyExpandDesignTimeFacades>false</ImplicitlyExpandDesignTimeFacades>",
        @"  </PropertyGroup>"
      };

      var footer = new[]
      {
        @"{15}{16}  <ItemGroup>",
        @""
      };

      var pieces = header.Concat(forceExplicitReferences).Concat(footer).ToArray();
      return string.Join(Environment.NewLine, pieces);
    }

    private void SyncSolution(ProjectPart[] islands, Type[] types)
    {
      SyncSolutionFileIfNotChanged(SolutionFile(), SolutionText(islands), types);
    }

    private string SolutionText(ProjectPart[] islands)
    {
      var fileversion = "11.00";
      var vsversion = "2010";
      
      var projectEntries = GetProjectEntries(islands);
      var projectConfigurations = string.Join(Environment.NewLine,
        islands.Select(i => GetProjectActiveConfigurations(ProjectGuid(i.Name, i.OutputPath))).ToArray());
      return string.Format(GetSolutionText(), fileversion, vsversion, projectEntries, projectConfigurations);
    }

    private static string GenerateAnalyserItemGroup(string[] paths)
    {
      //   <ItemGroup>
      //      <Analyzer Include="..\packages\Comments_analyser.1.0.6626.21356\analyzers\dotnet\cs\Comments_analyser.dll" />
      //      <Analyzer Include="..\packages\UnityEngineAnalyzer.1.0.0.0\analyzers\dotnet\cs\UnityEngineAnalyzer.dll" />
      //  </ItemGroup>
      if (!paths.Any())
        return string.Empty;

      var analyserBuilder = new StringBuilder();
      analyserBuilder.AppendLine("  <ItemGroup>");
      foreach (var path in paths)
      {
        analyserBuilder.AppendLine($"    <Analyzer Include=\"{path}\" />");
      }

      analyserBuilder.AppendLine("  </ItemGroup>");
      return analyserBuilder.ToString();
    }

    private static ILookup<string, string> GetOtherArgumentsFromResponseFilesData(List<ResponseFileData> responseFilesData)
    {
      var paths = responseFilesData.SelectMany(x =>
        {
          return x.OtherArguments
            .Where(a => a.StartsWith("/") || a.StartsWith("-"))
            .Select(b =>
            {
              var index = b.IndexOf(":", StringComparison.Ordinal);
              if (index > 0 && b.Length > index)
              {
                var key = b.Substring(1, index - 1);
                return new KeyValuePair<string, string>(key, b.Substring(index + 1));
              }

              const string warnaserror = "warnaserror";
              if (b.Substring(1).StartsWith(warnaserror))
              {
                return new KeyValuePair<string, string>(warnaserror, b.Substring(warnaserror.Length + 1));
              }

              return default;
            });
        })
        .Distinct()
        .ToLookup(o => o.Key, pair => pair.Value);
      return paths;
    }

    private string GenerateLangVersion(IEnumerable<string> langVersionList)
    {
      var langVersion = langVersionList.FirstOrDefault();
      if (!string.IsNullOrWhiteSpace(langVersion))
        return langVersion;
      return k_TargetLanguageVersion;
    }

    private static string GenerateAnalyserRuleSet(string[] paths)
    {
      //<CodeAnalysisRuleSet>..\path\to\myrules.ruleset</CodeAnalysisRuleSet>
      if (!paths.Any())
        return string.Empty;

      return $"{Environment.NewLine}{string.Join(Environment.NewLine, paths.Select(a => $"    <CodeAnalysisRuleSet>{a}</CodeAnalysisRuleSet>"))}";
    }

    private static string GenerateAnalyserAdditionalFiles(string[] paths)
    {
      if (!paths.Any())
        return string.Empty;

      var analyserBuilder = new StringBuilder();
      analyserBuilder.AppendLine("  <ItemGroup>");
      foreach (var path in paths)
      {
        analyserBuilder.AppendLine($"    <AdditionalFiles Include=\"{path}\" />");
      }

      analyserBuilder.AppendLine("  </ItemGroup>");
      return analyserBuilder.ToString();
    }

    private static string GenerateNoWarn(string[] codes)
    {
      if (!codes.Any())
        return string.Empty;

      return $",{string.Join(",", codes)}";
    }
    
    private string GetProjectEntries(ProjectPart[] islands)
    {
      var projectEntries = islands.Select(i => string.Format(
        m_SolutionProjectEntryTemplate,
        SolutionGuidGenerator.GuidForSolution(),
        i.Name,
        Path.GetFileName(ProjectFile(i)),
        ProjectGuid(i.Name, i.OutputPath)
      ));

      return string.Join(Environment.NewLine, projectEntries.ToArray());
    }

    /// <summary>
    /// Generate the active configuration string for a given project guid
    /// </summary>
    private string GetProjectActiveConfigurations(string projectGuid)
    {
      return string.Format(
        m_SolutionProjectConfigurationTemplate,
        projectGuid);
    }

    private string EscapedRelativePathFor(string file)
    {
      var projectDir = ProjectDirectory.Replace('/', '\\');
      file = file.Replace('/', '\\');
      var path = SkipPathPrefix(file, projectDir);

      var packageInfo = m_AssemblyNameProvider.FindForAssetPath(path.Replace('\\', '/'));
      if (packageInfo != null)
      {
        // We have to normalize the path, because the PackageManagerRemapper assumes
        // dir seperators will be os specific.
        var absolutePath = Path.GetFullPath(NormalizePath(path)).Replace('/', '\\');
        path = SkipPathPrefix(absolutePath, projectDir);
      }

      return SecurityElement.Escape(path);
    }

    private static string SkipPathPrefix(string path, string prefix)
    {
      if (path.StartsWith($@"{prefix}\"))
        return path.Substring(prefix.Length + 1);
      return path;
    }

    private static string NormalizePath(string path)
    {
      if (Path.DirectorySeparatorChar == '\\')
        return path.Replace('/', Path.DirectorySeparatorChar);
      return path.Replace('\\', Path.DirectorySeparatorChar);
    }

    private static string ProjectFooter()
    {
      return GetProjectFooterTemplate();
    }

    private static string GetProjectExtension()
    {
      return ".csproj";
    }

    private string ProjectGuid(string name, string outputPath)
    {
      return m_GUIDGenerator.ProjectGuid(
        m_ProjectName,
        m_AssemblyNameProvider.GetProjectName(outputPath, name));
    }
  }
}

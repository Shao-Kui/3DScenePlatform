namespace Packages.Rider.Editor.ProjectGeneration {
  class GUIDProvider : IGUIDGenerator
  {
    public string ProjectGuid(string projectName, string assemblyName)
    {
      return SolutionGuidGenerator.GuidForProject(projectName + assemblyName);
    }
  }
}

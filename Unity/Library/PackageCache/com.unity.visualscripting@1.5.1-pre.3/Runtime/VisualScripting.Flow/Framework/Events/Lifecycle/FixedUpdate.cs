namespace Unity.VisualScripting
{
    /// <summary>
    /// Called every fixed framerate frame.
    /// </summary>
    [UnitCategory("Events/Lifecycle")]
    [UnitOrder(4)]
    public sealed class FixedUpdate : MachineEventUnit<EmptyEventArgs>
    {
        protected override string hookName => EventHooks.FixedUpdate;
    }
}

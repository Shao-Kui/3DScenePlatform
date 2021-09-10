namespace Unity.VisualScripting
{
    [Descriptor(typeof(FlowMachine))]
    public sealed class FlowMachineDescriptor : MachineDescriptor<FlowMachine, MachineDescription>
    {
        public FlowMachineDescriptor(FlowMachine target) : base(target) {}
    }
}

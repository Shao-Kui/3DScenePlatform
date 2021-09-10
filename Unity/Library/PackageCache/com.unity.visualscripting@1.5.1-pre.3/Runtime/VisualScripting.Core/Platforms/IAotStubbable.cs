using System.Collections.Generic;

namespace Unity.VisualScripting
{
    public interface IAotStubbable
    {
        IEnumerable<object> aotStubs { get; }
    }
}

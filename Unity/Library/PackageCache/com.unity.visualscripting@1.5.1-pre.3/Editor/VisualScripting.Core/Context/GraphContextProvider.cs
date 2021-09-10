using System;

namespace Unity.VisualScripting
{
    public class GraphContextProvider : SingleDecoratorProvider<GraphReference, IGraphContext, GraphContextAttribute>
    {
        static GraphContextProvider()
        {
            instance = new GraphContextProvider();
        }

        public static GraphContextProvider instance { get; }

        protected override bool cache => true;

        protected override Type GetDecoratedType(GraphReference reference)
        {
            return reference.graph.GetType();
        }

        public override bool IsValid(GraphReference reference)
        {
            return reference.isValid;
        }
    }

    public static class XGraphContextProvider
    {
        public static IGraphContext Context(this GraphReference reference)
        {
            return GraphContextProvider.instance.GetDecorator(reference);
        }

        public static T Context<T>(this GraphReference reference) where T : IGraphContext
        {
            return GraphContextProvider.instance.GetDecorator<T>(reference);
        }
    }
}

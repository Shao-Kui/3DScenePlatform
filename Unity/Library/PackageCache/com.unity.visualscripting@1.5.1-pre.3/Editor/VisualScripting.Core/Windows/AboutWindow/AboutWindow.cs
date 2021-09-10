using System;
using System.Collections.Generic;
using UnityEngine;

namespace Unity.VisualScripting
{
    public sealed class AboutWindow : SinglePageWindow<AboutPage>
    {
        public AboutWindow(IEnumerable<Plugin> plugins)
        {
            Ensure.That(nameof(plugins)).IsNotNull(plugins);

            this.plugins = plugins;
        }

        public AboutWindow(Product product)
        {
            Ensure.That(nameof(product)).IsNotNull(product);

            this.product = product;
        }

        private readonly Product product;
        private readonly IEnumerable<Plugin> plugins;

        public new void Show()
        {
            if (window == null)
            {
                ShowUtility();
                window.Center();
            }
            else
            {
                window.Focus();
            }
        }

        protected override AboutPage CreatePage()
        {
            if (product != null)
            {
                return new AboutPage(product);
            }
            else if (plugins != null)
            {
                return new AboutPage(plugins);
            }

            throw new NotSupportedException();
        }

        protected override void ConfigureWindow()
        {
            base.ConfigureWindow();
            window.minSize = window.maxSize = new Vector2(470, 370);
        }
    }
}

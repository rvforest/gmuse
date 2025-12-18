:::{grid}
:gutter: 3
:class-container: sd-text-center sd-mt-5

::::{grid-item}
:::{image} _static/logo/gmuse-logo-light.png
:align: center
:width: 300px
:class: sd-m-auto only-light
:::
:::{image} _static/logo/gmuse-logo-dark.png
:align: center
:width: 300px
:class: sd-m-auto only-dark
:::
::::

::::{grid-item}
:class: sd-fs-4 sd-text-center sd-d-flex sd-flex-column sd-justify-content-center

**AI-generated git commit messages in the shell.**

gmuse streamline your workflow by using LLMs to generate meaningful commit messages directly from your staged changes.

:::{div} sd-mt-3
{bdg-primary-line}`Open Source` {bdg-secondary-line}`Python` {bdg-info-line}`AI Powered`
:::

:::{button-link} tutorials/quickstart
:color: primary
:outline:
:shadow:
:class: sd-mt-4

{octicon}`rocket;1.2em` Quickstart
:::
::::
:::

:::{grid}
:gutter: 3
:class-container: sd-mt-5

::::{grid-item}
:::{card} {octicon}`book;1.2em;sd-text-primary` Tutorials
:link: tutorials/index
:link-type: doc
:shadow: md

Step-by-step lessons to help you get started with gmuse.
:::
::::

::::{grid-item}
:::{card} {octicon}`tools;1.2em;sd-text-primary` How-to Guides
:link: how_to/index
:link-type: doc
:shadow: md

Practical guides to solve specific problems and tasks.
:::
::::

::::{grid-item}
:::{card} {octicon}`info;1.2em;sd-text-primary` Explanation
:link: explanation/index
:link-type: doc
:shadow: md

Deep dives into the architecture, concepts, and design.
:::
::::

::::{grid-item}
:::{card} {octicon}`code-square;1.2em;sd-text-primary` Reference
:link: reference/index
:link-type: doc
:shadow: md

Technical reference for APIs, CLI, and configuration.
:::
::::
:::

```{toctree}
:maxdepth: 1
:hidden:

tutorials/index
how_to/index
reference/index
explanation/index
development/index
```

# AI commit messages

```{meta}
:description: AI-powered git commit messages in the shell. Streamline your workflow by using LLMs to generate meaningful commit messages directly from your staged changes.
:keywords: git, commit, messages, AI, LLM, developer tools, shell
```

:::::{grid} 1 1 2 2
:gutter: 3
:class-container: sd-text-center sd-mt-5

::::{grid-item}
:::{image} _static/logo/gmuse-hero-light.png
:align: center
:width: 250px
:class: sd-m-auto only-light
:::
:::{image} _static/logo/gmuse-hero-dark.png
:align: center
:width: 250px
:class: sd-m-auto only-dark
:::
::::

::::{grid-item}
:class: sd-d-flex sd-flex-column sd-justify-content-center sd-text-left-lg sd-text-center-sm

:::{div} sd-fs-2 sd-fw-bold
AI-powered git commit messages in the shell.
:::

:::{div} sd-fs-5 sd-mt-2 sd-text-muted
**gmuse** streamlines your workflow by using LLMs to generate meaningful commit messages directly from your staged changes.
:::

:::{div} sd-mt-3
{bdg-secondary-line}`MIT` {bdg-secondary-line}`Python` {bdg-info}`AI Powered`
:::

:::{container} terminal-window
```console
$ uv tool install gmuse
$ echo 'eval "$(gmuse git-completions zsh)"' >> ~/.zshrc
```
:::

:::{button-link} tutorials/quickstart
:color: info
:shadow: lg
:class: sd-mt-3 sd-rounded-pill

{octicon}`rocket;1.2em` Get Started
:::
::::
:::::

:::::{grid} 1 2 2 4
:gutter: 3
:class-container: sd-mt-5

:::{grid-item-card} {octicon}`book;1.2em;sd-text-info` Tutorials
:link: tutorials/index
:link-type: doc
:shadow: lg

Step-by-step lessons to help you get started with gmuse.
:::

:::{grid-item-card} {octicon}`tools;1.2em;sd-text-info` How-to Guides
:link: how_to/index
:link-type: doc
:shadow: lg

Practical guides to solve specific problems and tasks.
:::

:::{grid-item-card} {octicon}`info;1.2em;sd-text-info` Explanation
:link: explanation/index
:link-type: doc
:shadow: lg

Deep dives into the architecture, concepts, and design.
:::

:::{grid-item-card} {octicon}`code-square;1.2em;sd-text-info` Reference
:link: reference/index
:link-type: doc
:shadow: lg

Technical reference for APIs, CLI, and configuration.
:::
:::::

```{toctree}
:maxdepth: 1
:hidden:

tutorials/index
how_to/index
reference/index
explanation/index
development/index
```

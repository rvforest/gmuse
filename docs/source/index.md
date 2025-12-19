# AI commit messages

```{meta}
:description: AI-powered git commit messages in the shell. Streamline your workflow by using LLMs to generate meaningful commit messages directly from your staged changes.
:keywords: git, commit, messages, AI, LLM, developer tools, shell
```

:::::{grid} 1 1 2 2
:gutter: 5
:class-container: sd-text-center sd-mt-0

::::{grid-item}
:class: sd-text-left-lg sd-text-center-sm sd-pr-lg-5 sd-d-flex sd-flex-column

:::{div} sd-fs-2 sd-fw-bold
AI-powered git commit messages in the shell.
:::

:::{div} sd-fs-5 sd-mt-2 sd-text-muted
Streamline your workflow by using LLMs to generate meaningful commit messages from staged changes.
:::

:::{div} sd-mt-3
{bdg-secondary-line}`MIT` {bdg-secondary-line}`Python` {bdg-info}`AI Powered`
:::

:::{button-link} tutorials/quickstart
:color: info
:shadow: lg
:class: sd-mt-auto sd-rounded-pill sd-mt-5

{octicon}`rocket;1.2em` Get Started
:::
::::

::::{grid-item}
:class: sd-d-flex sd-flex-column sd-pl-lg-5

:::{container} terminal-window
```console
$ uv tool install gmuse
$ echo 'eval "$(gmuse git-completions zsh)"' >> ~/.zshrc
```
:::

:::{div} sd-mt-auto
```{asciinema} _static/gmuse-demo.cast
:preload: 1
:rows: 8
:speed: 2.5
:theme: monokai
:font_size: 12px
```
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

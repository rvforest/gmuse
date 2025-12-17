# Quickstart: zsh completions for gmuse

## Installation

1.  **Generate the completion script**:
    ```zsh
    mkdir -p "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions"
    gmuse completions zsh > "${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions/_gmuse"
    ```

2.  **Enable completions** (if not already enabled):
    Add the following to your `~/.zshrc`:
    ```zsh
    fpath=("${XDG_DATA_HOME:-$HOME/.local/share}/zsh/site-functions" $fpath)
    autoload -Uz compinit
    compinit
    ```

3.  **Restart zsh**:
    ```zsh
    exec zsh
    ```

## Usage

1.  Stage some changes:
    ```zsh
    git add .
    ```

2.  Type `git commit -m ` and press **TAB**.
    - `gmuse` will generate a commit message and insert it.

3.  **With a hint**:
    Type `git commit -m "fix auth` and press **TAB**.
    - `gmuse` will complete the message based on your hint.

## Configuration

| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `GMUSE_COMPLETIONS_ENABLED` | `true` | Enable/disable completions. |
| `GMUSE_COMPLETIONS_TIMEOUT` | `3.0` | Timeout in seconds. |
| `GMUSE_COMPLETIONS_CACHE_TTL` | `30` | Cache TTL in seconds. |

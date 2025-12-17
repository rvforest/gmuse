# Quickstart: zsh completions for gmuse

## Installation

1.  **Add to your `~/.zshrc`**:
    ```zsh
    eval "$(gmuse completions zsh)"
    ```

2.  **Restart zsh**:
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

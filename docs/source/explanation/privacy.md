# Privacy & Security

Security is a primary concern for any tool that interacts with your source code. `gmuse` is designed with a "Privacy-First" philosophy to ensure your data stays under your control and that your machine, not a gmuse server, controls what leaves the repository.

## Privacy‑first architecture

Unlike some AI tools, **`gmuse` has no backend servers.** gmuse is **privacy‑first**: we prioritize local control and do not operate gmuse-hosted servers. When configured with a remote LLM provider, gmuse transmits only the minimal required inputs (staged diff, recent commits, project context, and any hint) directly from your machine to that provider and does not store them.

*   **No Data Storage**: We do not store, log, or track your code, diffs, or commit messages.
*   **Direct Communication**: The tool communicates directly from your machine to the LLM provider (OpenAI, Anthropic, Google, etc.).
*   **Stateless**: Each generation is a stateless request.

When you call a remote provider, only the staged diff, recent commits, project context, and any user hint are sent straight to that provider for the purpose of generating a commit message. If you run an LLM locally through LiteLLM or another local backend, both the prompt and the resulting response remain on your machine.

## Data in Transit

To generate a commit message, the following data is sent to the configured LLM provider:

| Data Type | Description |
| :--- | :--- |
| **Staged Diff** | The literal code changes you have added to the git index. |
| **Commit History** | The text of the last ~5 commit messages (to match your style). |
| **Project Context** | Content from your `.gmuse` file (if present). |
| **User Hint** | Any text you provide via the `--hint` flag. |

Remote providers receive exactly those pieces of data. When LiteLLM or any other locally hosted backend is configured, the same inputs are prepared locally and never traverse the network outside your machine.

<a name="what-is-never-sent"></a>
### What is NEVER sent:
*   Unstaged changes in your working directory.
*   Your API keys outside of the provider authentication flow (keys are read locally to authenticate the request to the provider and are never logged or stored by gmuse).
*   Any files or data outside of the current Git repository.
*   Environment variables unrelated to the specific API keys required for the request.

## API Key Security

*   **Priority of $ENV**: `gmuse` prefers using environment variables (e.g., `OPENAI_API_KEY`) for authentication. This is the most secure method as it keeps keys out of configuration files.
*   **No Accidental Commits**: If you use a local `.env` file, ensure it is in your `.gitignore`. `gmuse` never automatically reads or uploads `.env` files.
*   **Local Usage**: Keys are read on your machine and used only to authenticate the request to the provider; gmuse never uploads them to a gmuse-operated service or stores them anywhere.

```{warning}
**Warning:** Enabling `GMUSE_DEBUG=1` or DEBUG-level logging can surface prompts, diffs, and hints in your logs. Avoid enabling debug logging in sensitive environments—logs may reveal the same data the provider sees even though API keys remain redacted.
```


## LLM Provider Policies

Since `gmuse` uses the **APIs** of these providers (rather than their consumer web interfaces like ChatGPT), your data is typically subject to stricter privacy terms.

Most major providers (OpenAI, Anthropic, Google Gemini) state in their API terms that:
1.  Data sent via the API is **not** used to train their global models.
2.  Data is typically deleted after a short retention period (e.g., 30 days) for abuse monitoring only.

Policies evolve, so check the current privacy documentation for your chosen provider (OpenAI, Anthropic, Google, etc.) before sending sensitive data.

## How to Minimize Exposure

*   Prefer running LiteLLM or another trusted local model backend so prompts and responses stay on your machine.
*   Keep API keys in environment variables, never commit them, and store them in secrets managers if available.
*   Use `gmuse --dry-run` to inspect the prompt that would be sent to the provider before actually calling it.
*   Reserve `GMUSE_DEBUG` or DEBUG-level logging for troubleshooting and disable it in classified or shared environments.

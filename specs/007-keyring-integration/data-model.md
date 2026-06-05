# Data Model: Secure API Key Management

## Entity: `CredentialRecord`

Represents one credential variable as seen by `gmuse`.

**Fields**:

- `variable_name: str`
  - Environment-variable-style identifier, for example `OPENAI_API_KEY`.
  - Validation: non-empty, uppercase snake case preferred, no embedded value content.
- `source: Literal["env", "keyring", "missing"]`
  - The source that resolved the credential.
- `raw_value: str | None`
  - Actual credential value when resolution succeeds.
  - Never logged or printed directly.
- `masked_value: str | None`
  - UI-safe representation derived from `raw_value`.
- `is_managed: bool`
  - `True` when the variable appears in gmuse's keyring index.

**Relationships**:

- A `CredentialRecord` may correspond to a keyring entry under service `gmuse` with `username == variable_name`.
- Records shown by default in `auth status` come from the managed index; explicit provider checks can synthesize additional records from env vars and keyring lookups.

## Entity: `ManagedCredentialIndex`

Represents the set of variables currently managed by gmuse in the OS keyring.

**Storage Form**:

- Stored in the keyring under:
  - `service_name = "gmuse"`
  - `username = "__gmuse_index__"`
- Serialized as a comma-separated list of variable names.

**Fields**:

- `variables: set[str]`
  - Unique managed variable names.
  - Validation: values must be sorted/canonicalized before persistence to keep writes deterministic.

**State Transitions**:

- Empty index → add variable: after successful `auth set`.
- Existing index → remove variable: after successful `auth remove`.
- Non-empty index → empty index: after last managed credential is removed.

## Entity: `BackendStatus`

Represents whether the active keyring backend can be used for secure storage.

**Fields**:

- `backend_name: str`
- `backend_module: str`
- `is_available: bool`
- `is_secure: bool`
- `failure_reason: str | None`

**Validation Rules**:

- `is_available = false` for `NoKeyringError` and equivalent unusable states.
- `is_secure = false` when backend class comes from `keyrings.alt.*` or is `keyring.backends.null.Keyring`.

**Usage**:

- `auth set` must require `is_available = true` and `is_secure = true` before prompting.
- `auth status` and runtime resolution may read from a secure backend; insecure/unavailable backends surface actionable status/errors instead of reading or writing secrets.

## Entity: `AuthRequest`

Represents a user-triggered auth operation.

**Fields**:

- `command: Literal["set", "status", "remove"]`
- `variables: list[str]`
- `provider: str | None`
- `force: bool`
- `interactive: bool`

**Rules**:

- `set` requires exactly one variable name and masked interactive input.
- `remove` requires one or more variable names.
- `status` accepts zero or one provider hint and otherwise reads from the managed index.

## Resolution Flow

1. Resolve explicit CLI-provided credential values first when a command path supports them.
2. Check the environment variable named by `variable_name`.
3. Treat empty or whitespace-only env values as unresolved.
4. If unresolved, read the keyring entry for `variable_name` from service `gmuse`.
5. If still unresolved, return `source = "missing"` and surface a user-facing error or offline completion result.

## Masking Rules

- If credential length is 8 or more, replace all but the last 4 characters with `*`.
- If credential length is shorter than 8, replace every character with `*`.
- `None` remains unset and should not be shown as a masked secret.

"""CLI commands for secure credential management."""

from __future__ import annotations

from typing import NoReturn

import typer

from gmuse.credentials import (
    credential_exists,
    delete_credential,
    ensure_secure_backend,
    get_managed_variables,
    get_provider_credential_variables,
    resolve_credential,
    store_credential,
)
from gmuse.exceptions import (
    CredentialError,
    InsecureKeyringError,
    KeyringUnavailableError,
    build_insecure_keyring_message,
    build_missing_credential_message,
    build_no_secure_keyring_message,
    build_overwrite_message,
    build_provider_validation_message,
)

auth_app = typer.Typer(
    help=(
        "Manage API credentials for gmuse.\n\n"
        "Store interactive credentials in the OS keyring. Environment variables remain\n"
        "the recommended path for CI/CD and always take precedence when set."
    ),
    no_args_is_help=True,
)


def _exit_with_error(message: str, *, hint: str | None = None) -> NoReturn:
    typer.echo(f"Error: {message}", err=True)
    if hint:
        typer.echo("", err=True)
        typer.echo(hint, err=True)
    raise typer.Exit(code=1)


def _print_table(title: str, rows: list[tuple[str, str, str]]) -> None:
    typer.echo(title)
    typer.echo("")
    if not rows:
        typer.echo("No stored credentials found.")
        return

    variable_width = max(len("Variable"), max(len(row[0]) for row in rows))
    source_width = max(len("Source"), max(len(row[1]) for row in rows))
    value_width = max(len("Value"), max(len(row[2]) for row in rows))

    typer.echo(
        f"{'Variable':<{variable_width}}  {'Source':<{source_width}}  {'Value':<{value_width}}"
    )
    typer.echo(f"{'-' * variable_width}  {'-' * source_width}  {'-' * value_width}")
    for variable, source, value in rows:
        typer.echo(
            f"{variable:<{variable_width}}  {source:<{source_width}}  {value:<{value_width}}"
        )


@auth_app.command("set")
def set_credential(
    variable_name: str = typer.Argument(
        ..., help="Environment variable name to store."
    ),
    force: bool = typer.Option(
        False, "--force", help="Replace an existing credential."
    ),
) -> None:
    """Store or replace a credential in the OS keyring."""
    normalized_name = variable_name.strip()
    if not normalized_name:
        _exit_with_error("Variable name cannot be empty.")

    try:
        ensure_secure_backend()
    except KeyringUnavailableError:
        _exit_with_error(build_no_secure_keyring_message())
    except InsecureKeyringError:
        _exit_with_error(build_insecure_keyring_message())

    if credential_exists(normalized_name) and not force:
        confirmed = False
        try:
            confirmed = typer.confirm(
                f"Overwrite existing credential for {normalized_name}?",
                default=False,
            )
        except (EOFError, typer.Abort):
            _exit_with_error(build_overwrite_message(normalized_name))

        if not confirmed:
            _exit_with_error(build_overwrite_message(normalized_name))

    secret = ""
    try:
        secret = typer.prompt(
            f"Enter value for {normalized_name}",
            hide_input=True,
            show_default=False,
        )
    except (EOFError, typer.Abort):
        _exit_with_error(build_missing_credential_message(normalized_name))

    if not secret.strip():
        _exit_with_error("Credential value cannot be empty.")

    try:
        store_credential(normalized_name, secret.strip())
    except CredentialError as exc:
        _exit_with_error(str(exc))

    typer.echo(f"Stored {normalized_name} in the system keyring for gmuse.")


@auth_app.command("status")
def status(provider: str | None = None) -> None:
    """Show credential availability and storage source."""
    rows: list[tuple[str, str, str]] = []
    candidate_variables: list[str] = []

    if provider:
        validation: dict[str, object] = {}
        try:
            import litellm

            validation = litellm.validate_environment(model=f"{provider}/dummy")
        except Exception:
            _exit_with_error(build_provider_validation_message(provider))

        candidate_variables = list(get_provider_credential_variables(provider))
        missing_keys = validation.get("missing_keys", [])
        if isinstance(missing_keys, list):
            for missing_variable in missing_keys:
                if not isinstance(missing_variable, str):
                    continue
                if missing_variable not in candidate_variables:
                    candidate_variables.append(missing_variable)
    else:
        candidate_variables = sorted(get_managed_variables())

    managed = get_managed_variables()
    for variable_name in candidate_variables:
        resolution = resolve_credential(variable_name, managed_index=managed)
        rows.append(
            (
                variable_name,
                resolution.source,
                resolution.masked_value or "",
            )
        )

    title = (
        f"Credential status for provider: {provider}"
        if provider
        else "Credential status for gmuse"
    )
    _print_table(title, rows)


@auth_app.command("remove")
def remove_credential(
    variable_names: list[str] = typer.Argument(
        ..., help="One or more environment variable names to delete."
    ),
) -> None:
    """Remove one or more stored credentials."""
    if not variable_names:
        _exit_with_error("Provide at least one variable name to remove.")

    try:
        ensure_secure_backend()
    except KeyringUnavailableError:
        _exit_with_error(build_no_secure_keyring_message())
    except InsecureKeyringError:
        _exit_with_error(build_insecure_keyring_message())

    removed = 0
    missing: list[str] = []

    for variable_name in variable_names:
        normalized_name = variable_name.strip()
        if not normalized_name:
            continue
        try:
            if delete_credential(normalized_name):
                removed += 1
            else:
                missing.append(normalized_name)
        except CredentialError as exc:
            _exit_with_error(str(exc))

    if removed:
        typer.echo(f"Removed {removed} credential(s) from the system keyring.")

    for variable_name in missing:
        typer.echo(f"No stored credential found for {variable_name}.")

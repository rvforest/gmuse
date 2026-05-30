"""LLM client for interacting with various LLM providers.

This module provides a unified interface for calling LLM APIs using LiteLLM,
which supports 100+ providers including OpenAI, Anthropic, Cohere, and more.

Public API:
    - detect_provider: Auto-detect LLM provider from environment
    - resolve_model: Resolve model name with auto-detection
    - is_llm_available: Check if LLM is configured
    - LLMClient: Client for generating text

Note:
    All providers are supported out of the box via LiteLLM.
"""

import contextlib
import io
import os
import sys
from dataclasses import dataclass, field
from typing import Callable, Final, Iterator, Optional

import litellm

from gmuse.exceptions import LLMError
from gmuse.logging import configure_litellm_logging, get_logger

logger = get_logger(__name__)

ModelCompatibilityRule = Callable[[str], bool]
"""Callable used to decide whether a model can be served by a backend."""

# -----------------------------------------------------------------------------
# Module Initialization
# -----------------------------------------------------------------------------

# Configure litellm logging on module import
configure_litellm_logging()

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BackendDefinition:
    """Static description of one supported backend."""

    name: str
    credential_signals: tuple[str, ...]
    default_model: str
    model_compatibility_rule: ModelCompatibilityRule
    kind: str = "direct"
    backend_settings_namespace: str = ""


@dataclass(frozen=True, slots=True)
class BackendSelection:
    """Current backend selection state for one resolution attempt."""

    value: str | None
    source: str
    status: str
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ModelSelection:
    """Current model selection state for one resolution attempt."""

    value: str | None
    source: str
    native_backend_hint: str | None = None


@dataclass(frozen=True, slots=True)
class ResolutionContext:
    """Resolved backend/model context used by generation and diagnostics."""

    backend: BackendSelection
    model: ModelSelection
    diagnostic_source: str
    backend_settings: dict[str, object] = field(default_factory=dict)


def _get_model_provider_hint(model: str) -> str | None:
    """Infer the provider/backend hint for a model name using LiteLLM."""
    try:
        with _suppress_litellm_output():
            _, provider, _, _ = litellm.get_llm_provider(model)
    except Exception:
        return None
    return provider


def _is_openai_compatible_model(model: str) -> bool:
    """Return True when a model looks compatible with OpenAI-style backends."""
    provider_hint = _get_model_provider_hint(model)
    if provider_hint == "openai":
        return True

    normalized_model = model.removeprefix("openai/").removeprefix("azure/")
    return normalized_model.startswith(
        ("gpt-", "chatgpt-", "o1", "o3", "o4", "text-embedding-")
    )


def _is_anthropic_compatible_model(model: str) -> bool:
    """Return True when a model looks compatible with Anthropic."""
    provider_hint = _get_model_provider_hint(model)
    return provider_hint == "anthropic" or model.startswith("claude")


def _is_cohere_compatible_model(model: str) -> bool:
    """Return True when a model looks compatible with Cohere."""
    provider_hint = _get_model_provider_hint(model)
    return provider_hint == "cohere" or model.startswith("command")


def _is_azure_compatible_model(model: str) -> bool:
    """Return True when a model looks compatible with Azure OpenAI."""
    provider_hint = _get_model_provider_hint(model)
    return provider_hint == "azure" or _is_openai_compatible_model(model)


def _is_gemini_compatible_model(model: str) -> bool:
    """Return True when a model looks compatible with Gemini."""
    provider_hint = _get_model_provider_hint(model)
    return provider_hint == "gemini" or model.startswith("gemini")


def _guess_native_backend_hint(model: str) -> str | None:
    """Infer a built-in backend from model naming conventions alone."""
    if model.startswith("azure/"):
        return "azure"
    if _is_anthropic_compatible_model(model):
        return "anthropic"
    if _is_cohere_compatible_model(model):
        return "cohere"
    if _is_gemini_compatible_model(model):
        return "gemini"
    if _is_openai_compatible_model(model):
        return "openai"
    return None


def _make_provider_compatibility_rule(provider_name: str) -> ModelCompatibilityRule:
    """Create a compatibility rule bound to one provider/backend name."""

    def _is_compatible(model: str) -> bool:
        return _get_model_provider_hint(model) == provider_name

    return _is_compatible


def _make_direct_backend(
    name: str,
    *,
    credential_signals: tuple[str, ...],
    default_model: str,
    compatibility_rule: ModelCompatibilityRule | None = None,
) -> BackendDefinition:
    """Create a direct-backend definition for the built-in backends."""
    return BackendDefinition(
        name=name,
        credential_signals=credential_signals,
        default_model=default_model,
        model_compatibility_rule=(
            compatibility_rule
            if compatibility_rule is not None
            else _make_provider_compatibility_rule(name)
        ),
    )


# Prefer low-cost 'mini/light/haiku' variants for short, high-throughput tasks
# (commit message generation). These defaults prioritize cost and latency while
# retaining reliable instruction-following for our use case.
_DIRECT_BACKENDS: Final[dict[str, BackendDefinition]] = {
    "openai": _make_direct_backend(
        "openai",
        credential_signals=("OPENAI_API_KEY",),
        default_model="gpt-4o-mini",
        compatibility_rule=_is_openai_compatible_model,
    ),
    "anthropic": _make_direct_backend(
        "anthropic",
        credential_signals=("ANTHROPIC_API_KEY",),
        default_model="claude-haiku-4-5",
        compatibility_rule=_is_anthropic_compatible_model,
    ),
    "cohere": _make_direct_backend(
        "cohere",
        credential_signals=("COHERE_API_KEY",),
        default_model="command-light",
        compatibility_rule=_is_cohere_compatible_model,
    ),
    "azure": _make_direct_backend(
        "azure",
        credential_signals=("AZURE_API_KEY",),
        default_model="gpt-4o-mini",
        compatibility_rule=_is_azure_compatible_model,
    ),
    "gemini": _make_direct_backend(
        "gemini",
        credential_signals=("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        default_model="gemini/gemini-flash-lite-latest",
        compatibility_rule=_is_gemini_compatible_model,
    ),
}


def get_backend_definition(name: str) -> BackendDefinition | None:
    """Return the static definition for a supported direct backend."""
    return _DIRECT_BACKENDS.get(name)


def get_direct_backend_names() -> tuple[str, ...]:
    """Return the supported built-in direct backend names in priority order."""
    return tuple(_DIRECT_BACKENDS.keys())


def get_configured_direct_backends() -> tuple[BackendDefinition, ...]:
    """Return built-in direct backends that appear configured in the environment."""
    return tuple(
        backend
        for backend in _DIRECT_BACKENDS.values()
        if any(os.getenv(signal) for signal in backend.credential_signals)
    )


def get_native_backend_hint(model: str | None) -> str | None:
    """Return the built-in backend hinted by a model name, if any."""
    if not model:
        return None

    provider = _get_model_provider_hint(model)
    if provider in _DIRECT_BACKENDS:
        return provider
    return _guess_native_backend_hint(model)


def get_compatible_direct_backends(model: str | None) -> tuple[BackendDefinition, ...]:
    """Return configured built-in backends that can serve the selected model."""
    configured_backends = get_configured_direct_backends()
    if model is None:
        return configured_backends

    return tuple(
        backend
        for backend in configured_backends
        if backend.model_compatibility_rule(model)
    )


def _is_backend_configured(backend: BackendDefinition) -> bool:
    """Return True when the backend's credential signals are present."""
    return any(os.getenv(signal) for signal in backend.credential_signals)


def _missing_credentials_error(backend_name: str) -> LLMError:
    """Build a backend-aware missing-credentials error."""
    return LLMError(
        f"Selected backend '{backend_name}' is missing credentials.\n\n"
        "Configure the backend credentials and try again.\n"
        "Examples:\n"
        "  export OPENAI_API_KEY='sk-...'\n"
        "  export ANTHROPIC_API_KEY='sk-ant-...'\n"
        "  export COHERE_API_KEY='...'\n"
        "  export AZURE_API_KEY='...'\n"
        "  export GEMINI_API_KEY='...'"
    )


def _backend_model_mismatch_error(backend_name: str, model: str) -> LLMError:
    """Build a backend/model compatibility error."""
    return LLMError(
        f"Backend '{backend_name}' cannot serve model '{model}'.\n\n"
        "Choose a compatible model, or select a backend that matches the model's native ecosystem."
    )


def _no_compatible_backend_error(model: str | None) -> LLMError:
    """Build an error for the no-compatible-backend case."""
    guidance = "Choose a model that matches a configured backend, or configure one of the supported backends."
    if model is None:
        guidance = "Configure exactly one supported backend, or set GMUSE_MODEL to a model with a clear native backend hint."

    return LLMError(
        "No compatible backend is configured.\n\n"
        f"{guidance}\n"
        "Examples:\n"
        "  export OPENAI_API_KEY='sk-...'\n"
        "  export ANTHROPIC_API_KEY='sk-ant-...'"
    )


def _ambiguous_backend_error(backends: tuple[BackendDefinition, ...]) -> LLMError:
    """Build an error for ambiguous configured backends."""
    backend_names = ", ".join(backend.name for backend in backends)
    return LLMError(
        "Multiple configured backends match the current request.\n\n"
        f"Configured backends: {backend_names}\n\n"
        "Select a backend explicitly, or choose a model with a clear native backend hint."
    )


def _select_backend_settings(
    backend_name: str,
    backend_settings: dict[str, object] | None,
) -> dict[str, object]:
    """Select the reserved settings namespace for the resolved backend."""
    if not isinstance(backend_settings, dict):
        return {}

    selected_settings = backend_settings.get(backend_name)
    if not isinstance(selected_settings, dict):
        return {}

    return dict(selected_settings)


def resolve_resolution_context(
    *,
    backend: str | None = None,
    model: str | None = None,
    backend_settings: dict[str, object] | None = None,
) -> ResolutionContext:
    """Resolve the backend/model pair for one generation request."""
    resolved_model = model or os.getenv("GMUSE_MODEL")
    model_source = "explicit_model" if model is not None else "environment"
    if resolved_model is None:
        model_source = "unresolved"

    native_backend_hint = get_native_backend_hint(resolved_model)

    def _build_context(
        backend_definition: BackendDefinition,
        *,
        backend_source: str,
        resolved_model_value: str,
        resolved_model_source: str,
    ) -> ResolutionContext:
        return ResolutionContext(
            backend=BackendSelection(
                value=backend_definition.name,
                source=backend_source,
                status="resolved",
            ),
            model=ModelSelection(
                value=resolved_model_value,
                source=resolved_model_source,
                native_backend_hint=native_backend_hint,
            ),
            diagnostic_source=backend_source,
            backend_settings=_select_backend_settings(
                backend_definition.name,
                backend_settings,
            ),
        )

    if backend is not None:
        backend_definition = get_backend_definition(backend)
        if backend_definition is None:
            raise LLMError(f"Unsupported backend '{backend}'.")
        if not _is_backend_configured(backend_definition):
            raise _missing_credentials_error(backend_definition.name)
        if resolved_model is None:
            resolved_model = backend_definition.default_model
            model_source = "backend_default"
        elif not backend_definition.model_compatibility_rule(resolved_model):
            raise _backend_model_mismatch_error(backend_definition.name, resolved_model)

        return _build_context(
            backend_definition,
            backend_source="explicit_backend",
            resolved_model_value=resolved_model,
            resolved_model_source=model_source,
        )

    if resolved_model is not None and native_backend_hint is not None:
        hinted_backend = get_backend_definition(native_backend_hint)
        if hinted_backend is not None and _is_backend_configured(hinted_backend):
            return _build_context(
                hinted_backend,
                backend_source="native_backend_hint",
                resolved_model_value=resolved_model,
                resolved_model_source=model_source,
            )

    compatible_backends = get_compatible_direct_backends(resolved_model)
    if len(compatible_backends) == 1:
        selected_backend = compatible_backends[0]
        if resolved_model is None:
            resolved_model = selected_backend.default_model
            model_source = "backend_default"

        return _build_context(
            selected_backend,
            backend_source="single_configured_backend",
            resolved_model_value=resolved_model,
            resolved_model_source=model_source,
        )

    if len(compatible_backends) > 1:
        raise _ambiguous_backend_error(compatible_backends)

    raise _no_compatible_backend_error(resolved_model)


# -----------------------------------------------------------------------------
# Internal Helpers
# -----------------------------------------------------------------------------


@contextlib.contextmanager
def _suppress_litellm_output() -> Iterator[None]:
    """Context manager to suppress litellm's noisy stdout/stderr output.

    LiteLLM prints debug info like "Provider List: ..." that clutters output.
    This context manager captures and discards that output unless debug mode
    is enabled.

    Yields:
        None
    """
    if os.getenv("GMUSE_DEBUG"):
        yield
        return

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    try:
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


# -----------------------------------------------------------------------------
# Provider Detection
# -----------------------------------------------------------------------------


def detect_provider() -> Optional[str]:
    """Detect LLM provider from environment variables.

    Checks for common API key environment variables in priority order:

    1. OPENAI_API_KEY -> "openai"
    2. ANTHROPIC_API_KEY -> "anthropic"
    3. COHERE_API_KEY -> "cohere"
    4. AZURE_API_KEY -> "azure"
    5. GEMINI_API_KEY or GOOGLE_API_KEY -> "gemini"
    6. GMUSE_MODEL containing "gemini" -> "gemini"

    Returns:
        Provider name if API key found, None otherwise

    Example:
        >>> os.environ["OPENAI_API_KEY"] = "sk-..."
        >>> detect_provider()
        'openai'
    """
    # Check for direct backend credentials in priority order.
    configured_backends = get_configured_direct_backends()
    if configured_backends:
        return configured_backends[0].name

    # Check if GMUSE_MODEL explicitly indicates a provider
    if model := os.getenv("GMUSE_MODEL"):
        return _get_model_provider_hint(model)

    raise LLMError(
        "No LLM provider API key configured.\n\n"
        "Set an environment variable for your provider:\n"
        "  export OPENAI_API_KEY='sk-...'\n"
        "  export ANTHROPIC_API_KEY='sk-ant-...'\n\n"
        "Or configure in config.toml:\n"
        "  model = 'gpt-4'\n\n"
        "Config location: ~/.config/gmuse/config.toml"
    )


def resolve_model(provider: str, model: Optional[str] = None) -> str:
    """Resolve model name, using provider auto-detection if needed.

    Resolution priority:

    1. Explicit model parameter
    2. GMUSE_MODEL environment variable
    3. Auto-detect from provider API keys

    Args:
        model: Explicit model name (e.g., "gpt-4", "claude-3-opus")
        provider: Explicit provider override

    Returns:
        Resolved model name

    Raises:
        LLMError: If no model can be resolved

    Example:
        >>> resolve_model("gpt-4")
        'gpt-4'
        >>> os.environ["OPENAI_API_KEY"] = "sk-..."
        >>> resolve_model()  # Auto-detects
        'gpt-4o-mini'
    """
    # 1. Explicit model parameter
    if model:
        logger.debug(f"Using explicit model: {model}")
        return model

    # 2. Environment variable
    if env_model := os.getenv("GMUSE_MODEL"):
        logger.debug(f"Using model from GMUSE_MODEL: {env_model}")
        return env_model

    # 3. Try to get default model for provider
    backend_definition = get_backend_definition(provider)
    if backend_definition is None:
        raise LLMError(
            f"No default model configured for provider '{provider}'.\n\n"
            "Please specify a model explicitly:\n"
            "  export GMUSE_MODEL='<model-name>'\n"
            "  gmuse msg --model '<model-name>'\n\n"
            "Or configure in config.toml:\n"
            "  model = '<model-name>'\n\n"
            "Config location: ~/.config/gmuse/config.toml"
        )

    default_model = backend_definition.default_model
    logger.debug(f"Auto-detected provider: {provider}, using model: {default_model}")
    return default_model


class LLMClient:
    """Client for generating text using LLM providers.

    This class wraps LiteLLM to provide a simple interface for generating
    commit messages using various LLM providers.

    Attributes:
        model: LLM model identifier
        timeout: Request timeout in seconds

    Example:
        >>> client = LLMClient(model="gpt-4", timeout=30)
        >>> response = client.generate(
        ...     system_prompt="You are a commit message generator.",
        ...     user_prompt="Generate a commit message for: Added tests"
        ... )
        >>> print(response)
        'Add unit tests for authentication module'
    """

    def __init__(
        self,
        model: Optional[str] = None,
        backend: Optional[str] = None,
        backend_settings: dict[str, object] | None = None,
        timeout: int = 30,
    ):
        """Initialize LLM client.

        Args:
            model: LLM model identifier (auto-detects if None)
            timeout: Request timeout in seconds (default: 30)

        Raises:
            LLMError: If no provider is configured
        """
        resolution_context = resolve_resolution_context(
            backend=backend,
            model=model,
            backend_settings=backend_settings,
        )
        resolved_backend = resolution_context.backend.value
        resolved_model = resolution_context.model.value

        assert resolved_backend is not None, "Backend must be resolved"
        assert resolved_model is not None, "Model must be resolved"

        self.backend = resolved_backend
        self.provider = resolved_backend
        self.model = resolved_model
        self.timeout = timeout
        self.resolution_context = resolution_context

        logger.debug(
            "Initialized LLMClient with backend=%s, model=%s, timeout=%ss",
            self.backend,
            self.model,
            timeout,
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """Generate text using the LLM.

        Args:
            system_prompt: System message defining role and constraints
            user_prompt: User message with context and task
            temperature: Sampling temperature (0.0-1.0, default: 0.7)
            max_tokens: Maximum tokens in response (default: 500)

        Returns:
            Generated text from LLM

        Raises:
            LLMError: If API call fails

        Example:
            >>> client = LLMClient(model="gpt-4")
            >>> message = client.generate(
            ...     system_prompt="You are a helpful assistant.",
            ...     user_prompt="Say hello"
            ... )
            >>> print(message)
            'Hello! How can I help you today?'
        """
        logger.debug(f"Generating with model={self.model}, temperature={temperature}")
        logger.debug(f"System prompt:\n{system_prompt}")
        logger.debug(f"User prompt:\n{user_prompt}")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            # Suppress litellm's debug output unless GMUSE_DEBUG is enabled
            with _suppress_litellm_output():
                response = litellm.completion(  # type: ignore[operator]
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=self.timeout,
                )

            # Extract generated text
            content: str | None = response.choices[0].message.content
            if not content:
                raise LLMError("LLM returned empty response")

            logger.debug(f"Generated text: {content.strip()}")
            return content.strip()

        except LLMError:
            # Re-raise our own errors without wrapping
            raise
        except Exception as e:
            raise _convert_to_llm_error(e, self.timeout) from e


def _convert_to_llm_error(error: Exception, timeout: int) -> LLMError:
    """Convert various exceptions to appropriate LLMError messages.

    Args:
        error: The original exception
        timeout: Request timeout value for error messages

    Returns:
        LLMError with user-friendly message
    """
    error_msg = str(error).lower()

    if "api key" in error_msg or "authentication" in error_msg:
        return LLMError(
            "Authentication failed. Check your API key:\n\n"
            "  export OPENAI_API_KEY='sk-...'\n"
            "  export ANTHROPIC_API_KEY='sk-ant-...'\n\n"
            f"Original error: {error}"
        )

    if "timeout" in error_msg or "timed out" in error_msg:
        return LLMError(
            f"Request timed out after {timeout} seconds.\n\n"
            "Try increasing timeout:\n"
            f"  export GMUSE_TIMEOUT={timeout * 2}\n\n"
            f"Original error: {error}"
        )

    if "rate limit" in error_msg:
        return LLMError(
            "Rate limit exceeded. Wait a moment and try again.\n\n"
            f"Original error: {error}"
        )

    if "network" in error_msg or "connection" in error_msg:
        return LLMError(
            f"Network error. Check your internet connection.\n\nOriginal error: {error}"
        )

    # Generic error
    return LLMError(
        f"Failed to generate commit message: {error}\n\n"
        "This might be a temporary issue. Try again or check:\n"
        "  - API key is valid\n"
        "  - Internet connection is working\n"
        "  - Provider status page for outages"
    )

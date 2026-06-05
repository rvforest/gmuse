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
from typing import Final, Generator, Optional

import litellm

from gmuse.credentials import (
    detect_provider_from_credentials,
    normalize_env_value,
    resolve_provider_credential,
)
from gmuse.exceptions import (
    CredentialLookupTimeout,
    LLMError,
    build_missing_credential_message,
)
from gmuse.logging import configure_litellm_logging, get_logger

logger = get_logger(__name__)

# -----------------------------------------------------------------------------
# Module Initialization
# -----------------------------------------------------------------------------

# Configure litellm logging on module import
configure_litellm_logging()

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# Prefer low-cost 'mini/light/haiku' variants for short, high-throughput tasks
# (commit message generation). These defaults prioritize cost and latency while
# retaining reliable instruction-following for our use case.
_DEFAULT_MODELS: Final[dict[str, str]] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5",
    "cohere": "command-light",
    "azure": "gpt-4o-mini",
    "gemini": "gemini/gemini-flash-lite-latest",
}


# -----------------------------------------------------------------------------
# Internal Helpers
# -----------------------------------------------------------------------------


@contextlib.contextmanager
def _suppress_litellm_output() -> Generator[None, None, None]:
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


def detect_provider(
    *, model: str | None = None, credential_lookup_timeout: float | None = None
) -> Optional[str]:
    """Detect LLM provider from environment variables or model.

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
    # If model is known, try provider lookup. Fall back to credential detection
    # if LiteLLM introspection is unavailable or returns an unexpected shape.
    if model is not None or (model := os.getenv("GMUSE_MODEL")):
        with contextlib.suppress(Exception):
            provider_info = litellm.get_llm_provider(model)
            if isinstance(provider_info, tuple) and len(provider_info) >= 2:
                provider = provider_info[1]
                if isinstance(provider, str) and provider:
                    return provider

    env_var_provider = resolve_provider_from_key_env_vars()
    if env_var_provider is not None:
        return env_var_provider

    keyring_provider: Optional[str] = detect_provider_from_credentials(
        completion_timeout=credential_lookup_timeout,
    )
    if keyring_provider is not None:
        return keyring_provider
    raise LLMError(build_missing_credential_message())


def resolve_provider_from_key_env_vars() -> Optional[str]:
    """Resolve provider by checking for known API key environment variables.

    Returns:
        Provider name if found, None otherwise
    """
    if normalize_env_value(os.getenv("OPENAI_API_KEY")):
        return "openai"
    if normalize_env_value(os.getenv("ANTHROPIC_API_KEY")):
        return "anthropic"
    if normalize_env_value(os.getenv("COHERE_API_KEY")):
        return "cohere"
    if normalize_env_value(os.getenv("AZURE_API_KEY")):
        return "azure"
    if normalize_env_value(os.getenv("GEMINI_API_KEY")) or normalize_env_value(
        os.getenv("GOOGLE_API_KEY")
    ):
        return "gemini"
    return None


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
    if provider not in _DEFAULT_MODELS:
        raise LLMError(
            f"No default model configured for provider '{provider}'.\n\n"
            "Please specify a model explicitly:\n"
            "  export GMUSE_MODEL='<model-name>'\n"
            "  gmuse msg --model '<model-name>'\n\n"
            "Or configure in config.toml:\n"
            "  model = '<model-name>'\n\n"
            "Config location: ~/.config/gmuse/config.toml"
        )

    default_model = _DEFAULT_MODELS[provider]
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
        timeout: int = 30,
        credential_lookup_timeout: float | None = None,
    ):
        """Initialize LLM client.

        Args:
            model: LLM model identifier (auto-detects if None)
            timeout: Request timeout in seconds (default: 30)

        Raises:
            LLMError: If no provider is configured
        """
        # Detect provider for model resolution
        provider = detect_provider(
            model=model,
            credential_lookup_timeout=credential_lookup_timeout,
        )

        assert provider is not None, "Provider must be detected"
        self.provider = provider

        self.model = resolve_model(provider, model)
        self.timeout = timeout
        self.api_key: str | None = None

        credential = resolve_provider_credential(
            provider,
            completion_timeout=credential_lookup_timeout,
        )
        if credential is not None:
            if credential.source == "timeout":
                raise CredentialLookupTimeout(
                    f"Credential lookup for provider '{provider}' timed out after {credential_lookup_timeout} seconds."
                )
            self.api_key = credential.raw_value

        logger.debug(
            f"Initialized LLMClient with model={self.model}, timeout={timeout}s"
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
                    api_key=self.api_key,
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
            "Authentication failed. Check your provider credentials.\n\n"
            "You can configure credentials using environment variables or gmuse auth commands.\n"
            "Run 'gmuse auth status' to inspect credential detection.\n\n"
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

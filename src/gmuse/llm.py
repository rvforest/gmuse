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
from typing import Final, Iterator, Optional

import litellm

from gmuse.exceptions import LLMError
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
    # Check for API keys in priority order
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("COHERE_API_KEY"):
        return "cohere"
    if os.getenv("AZURE_API_KEY"):
        return "azure"
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        return "gemini"

    # Check if GMUSE_MODEL explicitly indicates gemini
    if model := os.getenv("GMUSE_MODEL"):
        if model.lower().startswith("gemini/") or "gemini" in model.lower():
            return "gemini"

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
    if provider not in _DEFAULT_MODELS:
        raise LLMError(
            f"No default model configured for provider '{provider}'.\n\n"
            "Please specify a model explicitly:\n"
            f"  export GMUSE_MODEL='<model-name>'\n"
            f"  gmuse msg --model '<model-name>'\n\n"
            "Or configure in config.toml:\n"
            f"  model = '<model-name>'\n\n"
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
        provider: Optional[str] = None,
    ):
        """Initialize LLM client.

        Args:
            model: LLM model identifier (auto-detects if None)
            timeout: Request timeout in seconds (default: 30)

        Raises:
            LLMError: If no provider is configured
        """
        # Detect provider once and reuse for both model resolution and storage
        if provider is None:
            provider = detect_provider()

        assert provider is not None, "Provider must be specified or detected"
        self.provider = provider

        self.model = resolve_model(provider, model)
        self.timeout = timeout

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

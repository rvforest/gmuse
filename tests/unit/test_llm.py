"""Unit tests for gmuse.llm module."""

import os
from unittest import mock

import pytest

from gmuse.exceptions import LLMError
from gmuse.llm import (
    LLMClient,
    detect_provider,
    resolve_model,
)


class TestDetectProvider:
    """Tests for detect_provider function."""

    def test_detect_openai(self) -> None:
        """Test detecting OpenAI provider."""
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            assert detect_provider() == "openai"

    def test_detect_anthropic(self) -> None:
        """Test detecting Anthropic provider."""
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            assert detect_provider() == "anthropic"

    def test_detect_cohere(self) -> None:
        """Test detecting Cohere provider."""
        with mock.patch.dict(os.environ, {"COHERE_API_KEY": "test"}):
            assert detect_provider() == "cohere"

    def test_detect_gemini_from_model_env(self) -> None:
        """Detect gemini provider when GMUSE_MODEL indicates a gemini model."""
        with mock.patch.dict(
            os.environ, {"GMUSE_MODEL": "gemini/gemini-flash-lite-latest"}, clear=True
        ):
            assert detect_provider() == "gemini"

    def test_detect_no_provider_raises_error(self) -> None:
        """Test error when no provider API key is set."""
        with mock.patch.dict(os.environ, {}, clear=True):
            with pytest.raises(LLMError, match="No LLM provider API key configured"):
                detect_provider()

    def test_detect_openai_priority(self) -> None:
        """Test OpenAI takes priority when multiple keys present."""
        with mock.patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "sk-test", "ANTHROPIC_API_KEY": "sk-ant-test"},
        ):
            assert detect_provider() == "openai"


class TestResolveModel:
    """Tests for resolve_model function."""

    def test_resolve_explicit_model(self) -> None:
        """Test resolving with explicit model parameter."""
        assert resolve_model("openai", "gpt-4") == "gpt-4"
        assert resolve_model("anthropic", "claude-3-opus") == "claude-3-opus"

    def test_resolve_from_env_var(self) -> None:
        """Test resolving model from GMUSE_MODEL env var."""
        with mock.patch.dict(os.environ, {"GMUSE_MODEL": "gpt-3.5-turbo"}):
            assert resolve_model("openai") == "gpt-3.5-turbo"

    def test_resolve_auto_detect_openai(self) -> None:
        """Test auto-detecting OpenAI model."""
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
            model = resolve_model("openai")
            assert model == "gpt-4o-mini"

    def test_resolve_auto_detect_anthropic(self) -> None:
        """Test auto-detecting Anthropic model."""
        with mock.patch.dict(
            os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}, clear=True
        ):
            model = resolve_model("anthropic")
            assert model == "claude-haiku-4-5"

    def test_resolve_explicit_overrides_env(self) -> None:
        """Test explicit model parameter overrides environment."""
        with mock.patch.dict(os.environ, {"GMUSE_MODEL": "gpt-3.5-turbo"}):
            assert resolve_model("anthropic", "claude-3-opus") == "claude-3-opus"

    def test_resolve_auto_detect_cohere(self) -> None:
        """Test auto-detecting Cohere model."""
        with mock.patch.dict(os.environ, {"COHERE_API_KEY": "test"}, clear=True):
            model = resolve_model("cohere")
            assert model == "command-light"

    def test_resolve_from_provider(self) -> None:
        """Test resolving model from explicit provider."""
        with mock.patch.dict(os.environ, {}, clear=True):
            assert resolve_model("gemini") == "gemini/gemini-flash-lite-latest"

    def test_resolve_unmapped_provider_raises_error(self) -> None:
        """Test that providers without default models raise an error."""
        with mock.patch.dict(os.environ, {}, clear=True):
            # bedrock is a valid provider but not in _DEFAULT_MODELS
            with pytest.raises(
                LLMError, match="No default model configured for provider 'bedrock'"
            ):
                resolve_model("bedrock")

            # huggingface is a valid provider but not in _DEFAULT_MODELS
            with pytest.raises(
                LLMError,
                match="No default model configured for provider 'huggingface'",
            ):
                resolve_model("huggingface")

    def test_resolve_unmapped_provider_with_explicit_model(self) -> None:
        """Test that unmapped providers work with explicit model."""
        with mock.patch.dict(os.environ, {}, clear=True):
            # Should work when model is explicitly provided
            assert (
                resolve_model("bedrock", "anthropic.claude-v2") == "anthropic.claude-v2"
            )
            assert (
                resolve_model("huggingface", "meta-llama/Llama-2-7b-hf")
                == "meta-llama/Llama-2-7b-hf"
            )

    def test_resolve_unmapped_provider_with_env_model(self) -> None:
        """Test that unmapped providers work with GMUSE_MODEL env var."""
        with mock.patch.dict(
            os.environ, {"GMUSE_MODEL": "my-custom-model"}, clear=True
        ):
            # Should work when GMUSE_MODEL is set
            assert resolve_model("bedrock") == "my-custom-model"
            assert resolve_model("huggingface") == "my-custom-model"


class TestLLMClient:
    """Tests for LLMClient class."""

    def test_init_with_explicit_model(self) -> None:
        """Test initializing client with explicit model and provider."""
        with mock.patch.dict(os.environ, {}, clear=True):
            client = LLMClient(model="gpt-4", timeout=60, provider="openai")
        assert client.model == "gpt-4"
        assert client.timeout == 60
        assert client.provider == "openai"

    def test_init_with_provider_override(self) -> None:
        """Test initializing client with explicit provider override."""
        with mock.patch.dict(os.environ, {}, clear=True):
            client = LLMClient(model=None, provider="gemini")
            # model should be auto-resolved to gemini default
            assert client.model == "gemini/gemini-flash-lite-latest"
            assert client.provider == "gemini"

    def test_init_auto_detects_model(self) -> None:
        """Test initializing client auto-detects model from environment."""
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
            client = LLMClient()
            assert client.model == "gpt-4o-mini"
            assert client.timeout == 30
            assert client.provider == "openai"

    @mock.patch("gmuse.llm.litellm")
    def test_generate_success(self, mock_litellm: mock.Mock) -> None:
        """Test successful message generation."""
        mock_response = mock.Mock()
        mock_response.choices = [
            mock.Mock(message=mock.Mock(content="Generated commit message"))
        ]
        mock_litellm.completion.return_value = mock_response

        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
            client = LLMClient(model="gpt-4", provider="openai")
            result = client.generate(
                system_prompt="You are a commit message generator.",
                user_prompt="Generate a message",
            )

            assert result == "Generated commit message"
            mock_litellm.completion.assert_called_once()

    @mock.patch("gmuse.llm.litellm")
    def test_generate_empty_response_raises_error(
        self, mock_litellm: mock.Mock
    ) -> None:
        """Test error when LLM returns empty response."""
        mock_response = mock.Mock()
        mock_response.choices = [mock.Mock(message=mock.Mock(content=""))]
        mock_litellm.completion.return_value = mock_response

        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
            client = LLMClient(model="gpt-4", provider="openai")
            with pytest.raises(LLMError, match="LLM returned empty response"):
                client.generate(
                    system_prompt="You are a commit message generator.",
                    user_prompt="Generate a message",
                )

    @mock.patch("gmuse.llm.litellm")
    def test_generate_auth_error(self, mock_litellm: mock.Mock) -> None:
        """Test handling authentication errors."""
        mock_litellm.completion.side_effect = Exception("API key invalid")

        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
            client = LLMClient(model="gpt-4", provider="openai")
            with pytest.raises(LLMError, match="Authentication failed"):
                client.generate(
                    system_prompt="System",
                    user_prompt="User",
                )

    @mock.patch("gmuse.llm.litellm")
    def test_generate_timeout_error(self, mock_litellm: mock.Mock) -> None:
        """Test handling timeout errors."""
        mock_litellm.completion.side_effect = Exception("Request timed out")

        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
            client = LLMClient(model="gpt-4", timeout=30, provider="openai")
            with pytest.raises(LLMError, match="Request timed out after 30 seconds"):
                client.generate(
                    system_prompt="System",
                    user_prompt="User",
                )

    @mock.patch("gmuse.llm.litellm")
    def test_generate_rate_limit_error(self, mock_litellm: mock.Mock) -> None:
        """Test handling rate limit errors."""
        mock_litellm.completion.side_effect = Exception("Rate limit exceeded")

        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
            client = LLMClient(model="gpt-4", provider="openai")
            with pytest.raises(LLMError, match="Rate limit exceeded"):
                client.generate(
                    system_prompt="System",
                    user_prompt="User",
                )

    @mock.patch("gmuse.llm.litellm")
    def test_generate_network_error(self, mock_litellm: mock.Mock) -> None:
        """Test handling network errors."""
        mock_litellm.completion.side_effect = Exception("Network error occurred")

        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
            client = LLMClient(model="gpt-4", provider="openai")
            with pytest.raises(LLMError, match="Network error"):
                client.generate(
                    system_prompt="System",
                    user_prompt="User",
                )

    @mock.patch("gmuse.llm.litellm")
    def test_generate_generic_error(self, mock_litellm: mock.Mock) -> None:
        """Test handling generic errors."""
        mock_litellm.completion.side_effect = Exception("Unknown error")

        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
            client = LLMClient(model="gpt-4", provider="openai")
            with pytest.raises(LLMError, match="Failed to generate commit message"):
                client.generate(
                    system_prompt="System",
                    user_prompt="User",
                )

        @mock.patch("gmuse.llm.litellm")
        def test_generate_suppresses_provider_list_prints(
            self, mock_litellm: mock.Mock, capsys
        ) -> None:
            """Ensure we suppress litellm 'Provider List' prints during generation unless GMUSE_DEBUG=true."""

            # Create a side effect that prints the provider list and then returns a success response
            def fake_completion(*args, **kwargs):
                print("Provider List: https://docs.litellm.ai/docs/providers")

                class R:
                    class Choice:
                        class Message:
                            content = "Generated commit message"

                        message = Message()

                    choices = [Choice()]

                return R()

            mock_litellm.completion.side_effect = fake_completion

            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=True):
                client = LLMClient(model="gpt-4")
                # Ensure GMUSE_DEBUG not set -> the provider list should be suppressed
                os.environ.pop("GMUSE_DEBUG", None)
                result = client.generate(
                    system_prompt="You are a commit message generator.",
                    user_prompt="Generate a message",
                )
                assert result == "Generated commit message"
                captured = capsys.readouterr()
                assert "Provider List" not in captured.out

                # Now set GMUSE_DEBUG: provider list should appear
                os.environ["GMUSE_DEBUG"] = "1"
                result = client.generate(
                    system_prompt="You are a commit message generator.",
                    user_prompt="Generate a message",
                )
                captured = capsys.readouterr()
                assert "Provider List" in captured.out

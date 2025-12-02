"""
Tests for LLM Configuration Module.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from src.multi_agent_mobile_ui_assistant.llm_config import LLMConfig, create_llm, get_default_llm

class TestLLMConfig:
    """Tests for LLMConfig class."""

    def test_init_defaults(self):
        """Test initialization with default values."""
        with patch.dict(os.environ, {}, clear=True):
            config = LLMConfig(provider="ollama")
            assert config.provider == "ollama"
            assert config.model == "llama3.2"
            assert config.temperature == 0.7
            assert config.base_url == "http://localhost:11434"

    def test_init_openai_defaults(self):
        """Test initialization for OpenAI with defaults."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            config = LLMConfig(provider="openai")
            assert config.provider == "openai"
            assert config.model == "gpt-4o-mini"
            assert config.api_key == "test-key"

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            temperature=0.5,
            api_key="custom-key"
        )
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.api_key == "custom-key"

    def test_openai_missing_key(self):
        """Test error when OpenAI API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key required"):
                LLMConfig(provider="openai")

    @patch("src.multi_agent_mobile_ui_assistant.llm_config.ChatOllama")
    def test_get_llm_ollama(self, mock_chat_ollama):
        """Test getting Ollama LLM instance."""
        config = LLMConfig(provider="ollama", model="llama2", temperature=0.8)
        llm = config.get_llm()
        
        mock_chat_ollama.assert_called_once_with(
            model="llama2",
            temperature=0.8,
            base_url="http://localhost:11434"
        )
        assert llm == mock_chat_ollama.return_value

    @patch("src.multi_agent_mobile_ui_assistant.llm_config.ChatOpenAI")
    def test_get_llm_openai(self, mock_chat_openai):
        """Test getting OpenAI LLM instance."""
        config = LLMConfig(provider="openai", api_key="sk-test")
        llm = config.get_llm()
        
        mock_chat_openai.assert_called_once_with(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key="sk-test"
        )
        assert llm == mock_chat_openai.return_value

    def test_invalid_provider(self):
        """Test error with invalid provider."""
        config = LLMConfig(provider="ollama")
        config.provider = "invalid"
        with pytest.raises(ValueError, match="Unsupported provider"):
            config.get_llm()

class TestCreateLLM:
    """Tests for create_llm factory function."""

    @patch("src.multi_agent_mobile_ui_assistant.llm_config.LLMConfig")
    def test_create_llm_from_env(self, mock_config_cls):
        """Test creating LLM from environment variables."""
        env_vars = {
            "LLM_PROVIDER": "openai",
            "LLM_MODEL": "gpt-4",
            "LLM_TEMPERATURE": "0.2",
            "OPENAI_API_KEY": "env-key"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            create_llm()
            
            mock_config_cls.assert_called_once_with(
                provider="openai",
                model="gpt-4",
                temperature=0.2
            )
            mock_config_cls.return_value.get_llm.assert_called_once()

    @patch("src.multi_agent_mobile_ui_assistant.llm_config.LLMConfig")
    def test_create_llm_args_override(self, mock_config_cls):
        """Test arguments override environment variables."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=True):
            create_llm(provider="openai", model="gpt-3.5", temperature=0.9)
            
            mock_config_cls.assert_called_once_with(
                provider="openai",
                model="gpt-3.5",
                temperature=0.9
            )

class TestGetDefaultLLM:
    """Tests for get_default_llm singleton."""

    def setup_method(self):
        """Reset singleton before each test."""
        import src.multi_agent_mobile_ui_assistant.llm_config as module
        module._default_llm = None

    @patch("src.multi_agent_mobile_ui_assistant.llm_config.create_llm")
    def test_singleton_behavior(self, mock_create):
        """Test that create_llm is called only once."""
        mock_llm = MagicMock()
        mock_create.return_value = mock_llm
        
        # First call creates instance
        llm1 = get_default_llm()
        assert llm1 == mock_llm
        mock_create.assert_called_once()
        
        # Second call returns same instance
        llm2 = get_default_llm()
        assert llm2 == mock_llm
        mock_create.assert_called_once()

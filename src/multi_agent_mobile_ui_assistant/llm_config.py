"""
LLM Configuration Module

This module handles LLM provider selection and initialization.
Supports both OpenAI and Ollama providers.
"""

import os
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


LLMProvider = Literal["openai", "ollama"]


class LLMConfig:
    """Configuration for LLM providers."""
    
    def __init__(
        self,
        provider: LLMProvider = "ollama",
        model: str | None = None,
        temperature: float = 0.7,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize LLM configuration.
        
        Args:
            provider: LLM provider to use ("openai" or "ollama")
            model: Model name (defaults based on provider)
            temperature: Temperature for generation (0.0 to 1.0)
            api_key: API key for OpenAI (optional, reads from env)
            base_url: Base URL for Ollama (optional, defaults to localhost)
        """
        self.provider = provider
        self.temperature = temperature
        
        # Set default models based on provider
        if model is None:
            self.model = "gpt-4o-mini" if provider == "openai" else "llama3.2"
        else:
            self.model = model
        
        # Set API key for OpenAI
        if provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                    "or pass api_key parameter."
                )
        
        # Set base URL for Ollama
        if provider == "ollama":
            self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    def get_llm(self) -> BaseChatModel:
        """
        Get configured LLM instance.
        
        Returns:
            Configured LangChain chat model
        """
        if self.provider == "openai":
            return ChatOpenAI(
                model=self.model,
                temperature=self.temperature,
                api_key=self.api_key,
            )
        elif self.provider == "ollama":
            return ChatOllama(
                model=self.model,
                temperature=self.temperature,
                base_url=self.base_url,
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")


def create_llm(
    provider: LLMProvider | None = None,
    model: str | None = None,
    temperature: float = 0.7,
) -> BaseChatModel:
    """
    Create and return an LLM instance.
    
    This is a convenience function that reads configuration from
    environment variables if not provided.
    
    Args:
        provider: LLM provider ("openai" or "ollama")
        model: Model name
        temperature: Generation temperature
        
    Returns:
        Configured LangChain chat model
        
    Environment Variables:
        LLM_PROVIDER: Default provider (default: "ollama")
        LLM_MODEL: Default model name
        LLM_TEMPERATURE: Default temperature
        OPENAI_API_KEY: OpenAI API key (required for OpenAI)
        OLLAMA_BASE_URL: Ollama server URL (default: http://localhost:11434)
    """
    # Read from environment if not provided
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "ollama")  # type: ignore
    
    if model is None:
        model = os.getenv("LLM_MODEL")
    
    temperature_env = os.getenv("LLM_TEMPERATURE")
    if temperature_env is not None:
        temperature = float(temperature_env)
    
    # Create and return LLM
    config = LLMConfig(
        provider=provider,
        model=model,
        temperature=temperature,
    )
    
    return config.get_llm()


# Default LLM instance (lazy loaded)
_default_llm: BaseChatModel | None = None


def get_default_llm() -> BaseChatModel:
    """
    Get the default LLM instance.
    
    This creates a singleton LLM instance based on environment configuration.
    
    Returns:
        Default LangChain chat model
    """
    global _default_llm
    
    if _default_llm is None:
        _default_llm = create_llm()
    
    return _default_llm

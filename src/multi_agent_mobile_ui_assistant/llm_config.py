"""
LLM Configuration Module

This module handles LLM provider selection and initialization.
Supports OpenAI, Ollama, Google, and Anthropic providers.
"""

import os
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


LLMProvider = Literal["openai", "ollama", "google", "anthropic", "custom"]


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
            provider: LLM provider to use ("openai", "ollama", "google", "anthropic")
            model: Model name (defaults based on provider)
            temperature: Temperature for generation (0.0 to 1.0)
            api_key: API key for OpenAI/Google/Anthropic (optional, reads from env)
            base_url: Base URL for Ollama (optional, defaults to localhost)
        """
        self.provider = provider
        self.temperature = temperature
        
        # Set default models based on provider
        if model is None:
            if provider == "openai":
                self.model = "gpt-4o-mini"
            elif provider == "google":
                self.model = "gemini-1.5-pro"
            elif provider == "anthropic":
                self.model = "claude-3-5-sonnet-20240620"
            else:
                self.model = "llama3.2"
        else:
            self.model = model
        
        # Set API key based on provider
        if provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI API key required.")
        elif provider == "google":
            self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
            if not self.api_key:
                raise ValueError("Google API key required.")
        elif provider == "anthropic":
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise ValueError("Anthropic API key required.")
        
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
        elif self.provider == "google":
            return ChatGoogleGenerativeAI(
                model=self.model,
                temperature=self.temperature,
                google_api_key=self.api_key,
            )
        elif self.provider == "anthropic":
            return ChatAnthropic(
                model_name=self.model,
                temperature=self.temperature,
                api_key=self.api_key,
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")


def create_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.7,
) -> BaseChatModel:
    """
    Create and return an LLM instance.
    
    This is a convenience function that reads configuration from
    environment variables if not provided.
    
    Args:
        provider: LLM provider
        model: Model name
        temperature: Generation temperature
        
    Returns:
        Configured LangChain chat model
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
        provider=provider, # type: ignore
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

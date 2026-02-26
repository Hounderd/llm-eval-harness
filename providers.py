from abc import ABC, abstractmethod
import os
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from google import genai

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, model_name: str, prompt: str) -> str:
        """Generate a response from the LLM given a prompt."""
        pass

class AsyncOpenAIProvider(LLMProvider):
    def __init__(self):
        # Relies on OPENAI_API_KEY environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is missing")
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(self, model_name: str, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

class AsyncAnthropicProvider(LLMProvider):
    def __init__(self):
        # Relies on ANTHROPIC_API_KEY environment variable
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is missing")
        self.client = AsyncAnthropic(api_key=api_key)

    async def generate(self, model_name: str, prompt: str) -> str:
        response = await self.client.messages.create(
            model=model_name,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

class GroqProvider(LLMProvider):
    """Groq Cloud — OpenAI-compatible API with free tier.
    Supports: llama-3.3-70b-versatile, llama-3.1-8b-instant, gemma2-9b-it, mixtral-8x7b-32768
    Sign up and get a free key at: https://console.groq.com
    """
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is missing")
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )

    async def generate(self, model_name: str, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

class GeminiProvider(LLMProvider):
    """Google Gemini — generous free tier via Google AI Studio.
    Supports: gemini-2.0-flash, gemini-1.5-flash, gemini-1.5-pro
    Get a free key at: https://aistudio.google.com/apikey
    """
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is missing")
        self.client = genai.Client(api_key=api_key)

    async def generate(self, model_name: str, prompt: str) -> str:
        response = await self.client.aio.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text

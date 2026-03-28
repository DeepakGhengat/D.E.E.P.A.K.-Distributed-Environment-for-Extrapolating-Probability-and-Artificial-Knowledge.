"""
LLM Client - Claude via Anthropic API or OpenRouter
Supports two providers:
  1. Anthropic (direct) - native SDK, best performance
  2. OpenRouter - OpenAI-compatible API, access Claude + other models
"""

import json
import re
from typing import Optional, Dict, Any, List

from ..config import Config


class LLMClient:
    """Claude LLM Client - auto-selects Anthropic or OpenRouter based on config"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.model = model or Config.LLM_MODEL_NAME
        self.provider = provider or Config.LLM_PROVIDER

        if not self.api_key:
            raise ValueError(
                "No LLM API key configured. "
                "Set ANTHROPIC_API_KEY or OPENROUTER_API_KEY in your .env file"
            )

        if self.provider == 'anthropic':
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        elif self.provider == 'openrouter':
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=Config.OPENROUTER_BASE_URL
            )
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        Send a chat request to Claude (via Anthropic or OpenRouter).

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                      Supports 'system', 'user', and 'assistant' roles.
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens in the response
            response_format: If {"type": "json_object"}, instructs Claude to return JSON

        Returns:
            Model response text
        """
        if self.provider == 'anthropic':
            return self._chat_anthropic(messages, temperature, max_tokens, response_format)
        else:
            return self._chat_openrouter(messages, temperature, max_tokens, response_format)

    def _chat_anthropic(self, messages, temperature, max_tokens, response_format):
        """Send request via native Anthropic SDK"""
        system_text = None
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            else:
                chat_messages.append(msg)

        if response_format and response_format.get("type") == "json_object":
            json_instruction = "You must respond with valid JSON only. No markdown, no explanation, just the JSON object."
            system_text = f"{system_text}\n\n{json_instruction}" if system_text else json_instruction

        kwargs = {
            "model": self.model,
            "messages": chat_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_text:
            kwargs["system"] = system_text

        response = self.client.messages.create(**kwargs)
        content = response.content[0].text
        content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
        return content

    def _chat_openrouter(self, messages, temperature, max_tokens, response_format):
        """Send request via OpenRouter (OpenAI-compatible API)"""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        content = re.sub(r'<think>[\s\S]*?</think>', '', content).strip()
        return content

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Send a chat request and return parsed JSON.

        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens in the response

        Returns:
            Parsed JSON object
        """
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise ValueError(f"LLM returned invalid JSON: {cleaned_response}")

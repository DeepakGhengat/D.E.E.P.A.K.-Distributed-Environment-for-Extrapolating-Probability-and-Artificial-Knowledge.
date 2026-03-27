"""
LLM Client - Anthropic Claude Integration
Unified client for Claude model interactions via the Anthropic SDK.
"""

import json
import re
from typing import Optional, Dict, Any, List

import anthropic

from ..config import Config


class LLMClient:
    """Claude LLM Client powered by Anthropic API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.model = model or Config.LLM_MODEL_NAME

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured")

        self.client = anthropic.Anthropic(api_key=self.api_key)

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        Send a chat request to Claude.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                      Supports 'system', 'user', and 'assistant' roles.
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens in the response
            response_format: If {"type": "json_object"}, instructs Claude to return JSON

        Returns:
            Model response text
        """
        # Extract system message if present
        system_text = None
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            else:
                chat_messages.append(msg)

        # If JSON format requested, add instruction to system prompt
        if response_format and response_format.get("type") == "json_object":
            json_instruction = "You must respond with valid JSON only. No markdown, no explanation, just the JSON object."
            if system_text:
                system_text = f"{system_text}\n\n{json_instruction}"
            else:
                system_text = json_instruction

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
        # Clean up any thinking tags from extended thinking models
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
        # Clean markdown code block markers
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_response, flags=re.IGNORECASE)
        cleaned_response = re.sub(r'\n?```\s*$', '', cleaned_response)
        cleaned_response = cleaned_response.strip()

        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            raise ValueError(f"Claude returned invalid JSON: {cleaned_response}")

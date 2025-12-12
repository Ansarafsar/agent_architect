"""
Base agent class and utilities for Cerina Protocol Foundry.
"""
import os
import json
from typing import Optional, Dict, Any
import httpx
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for OpenRouter API calls."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize the LLM client.
        
        Args:
            api_key: OpenRouter API key. If None, uses OPENROUTER_API_KEY from env
            model: Model name. If None, uses OPENROUTER_MODEL from env
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = model or os.getenv("OPENROUTER_MODEL", "google/gemini-2.0-flash-exp:free")
        self.base_url = "https://openrouter.ai/api/v1"
        
        if not self.api_key:
            logger.warning("No OpenRouter API key found. Set OPENROUTER_API_KEY environment variable.")
    
    async def chat(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        json_mode: bool = False
    ) -> str:
        """
        Send a chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            json_mode: If True, requests JSON output
            
        Returns:
            Generated text response
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://cerina-foundry.local",
            "X-Title": "Cerina Protocol Foundry"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                return result["choices"][0]["message"]["content"]
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during LLM call: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during LLM call: {e}")
            raise
    
    async def chat_json(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Send a chat completion request expecting JSON response.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Parsed JSON response
        """
        response = await self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response}")
            # Try to extract JSON from markdown code blocks
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            raise


class BaseAgent:
    """Base class for all agents in the system."""
    
    def __init__(self, name: str, llm_client: Optional[LLMClient] = None):
        """
        Initialize the agent.
        
        Args:
            name: Agent name for logging
            llm_client: LLM client instance. If None, creates a new one
        """
        self.name = name
        self.llm = llm_client or LLMClient()
        self.logger = logging.getLogger(f"agent.{name}")
    
    def log(self, message: str, level: str = "info"):
        """Log a message."""
        log_func = getattr(self.logger, level, self.logger.info)
        log_func(f"[{self.name}] {message}")
    
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the agent. Must be implemented by subclasses.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state
        """
        raise NotImplementedError("Subclasses must implement run()")

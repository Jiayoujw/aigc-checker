import json
from typing import Literal
from openai import AsyncOpenAI
from ..config import config


class LLMClient:
    def __init__(self, provider: Literal["deepseek", "openai", "auto"] = "auto"):
        self.provider = config.DEFAULT_PROVIDER if provider == "auto" else provider

        if self.provider == "deepseek":
            self.client = AsyncOpenAI(
                base_url=config.DEEPSEEK_BASE_URL,
                api_key=config.DEEPSEEK_API_KEY,
            )
            self.model = config.DEEPSEEK_MODEL
        else:
            self.client = AsyncOpenAI(
                api_key=config.OPENAI_API_KEY,
            )
            self.model = config.OPENAI_MODEL

    async def chat_json(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
    ) -> dict:
        """Send a chat request and parse the response as JSON."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if content is None:
            raise ValueError("LLM returned empty response")
        return json.loads(content)

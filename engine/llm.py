import logging

from api.config import get_settings

# Import clients conditionally to avoid hard crashes if packages aren't installed yet
try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None  # type: ignore[assignment, misc]

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None  # type: ignore[assignment, misc]

settings = get_settings()
logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self):
        self.openai = None
        self.anthropic = None

        if settings.openai_api_key and AsyncOpenAI is not None:
            self.openai = AsyncOpenAI(api_key=settings.openai_api_key)

        if settings.anthropic_api_key and AsyncAnthropic is not None:
            self.anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def ask(self, prompt: str, system_role: str = "You are a helpful assistant.") -> str:
        """
        Send a prompt to the configured AI model.
        Prioritizes Anthropic (Claude 3 Opus) if available.
        Fallbacks to OpenAI (GPT-4o).
        """
        # 1. Try Anthropic (Opus)
        if self.anthropic:
            try:
                message = await self.anthropic.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=4000,
                    system=system_role,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text  # type: ignore[no-any-return]
            except Exception as e:
                logger.error(f"Anthropic error: {e}")
                # Fallthrough to OpenAI if available

        # 2. Try OpenAI (GPT-4o)
        if self.openai:
            try:
                response = await self.openai.chat.completions.create(
                    model=settings.ai_model, # e.g. gpt-4o
                    messages=[
                        {"role": "system", "content": system_role},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content  # type: ignore[no-any-return]
            except Exception as e:
                logger.error(f"OpenAI error: {e}")
                raise e

        raise ValueError("No viable AI client configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY.")

# Global instance
ai_client = AIClient()

async def ask_ai(prompt: str, system_role: str = "You are a helpful assistant.") -> str:
    return await ai_client.ask(prompt, system_role)

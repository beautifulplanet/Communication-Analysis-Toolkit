import asyncio

import pytest

from api.config import get_settings
from engine.llm import ask_ai


@pytest.mark.asyncio
async def test_ai():
    settings = get_settings()

    if not (settings.openai_api_key or settings.anthropic_api_key):
        pytest.skip("No API keys configured — add OPENAI_API_KEY or ANTHROPIC_API_KEY to .env")

    response = await ask_ai("Say 'AI Connected' if you are working.")
    assert response
    assert len(response) > 0


if __name__ == "__main__":
    asyncio.run(test_ai())

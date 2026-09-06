import asyncio

from app.services.providers.openai_provider import OpenAIProvider
from app.services.providers.gemini_provider import GeminiProvider
from app.services.providers.groq_provider import GroqProvider


async def main():
    # provider = OpenAIProvider()
    # provider = GeminiProvider()  
    provider = GroqProvider()  

    response = await provider.generate(
        message="Say hello in one sentence."
        # message="Read https://groq.com and summarize what Groq does."
    )

    print("Response:")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
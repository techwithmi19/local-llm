import asyncio

from app.services.providers.openai_provider import OpenAIProvider
from app.services.providers.gemini_provider import GeminiProvider
from app.services.providers.groq_provider import GroqProvider


async def main():
    # provider = OpenAIProvider()
    # provider = GeminiProvider()  
    provider = GroqProvider()  

    messages = [
        {"role": "user", "content": "Say hello in one sentence."}
        # {"role": "user", "content": "Read https://groq.com and summarize what Groq does."}
    ]

    response = await provider.generate(messages=messages)

    print("Response:")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
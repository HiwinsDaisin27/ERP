import asyncio

import httpx

from app.core.config import settings


async def main() -> None:
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/getWebhookInfo"
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url)
        response.raise_for_status()
        print(response.json())


if __name__ == "__main__":
    asyncio.run(main())

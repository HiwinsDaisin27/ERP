import asyncio

from app.core.config import settings
from app.services.telegram_client import TelegramClient


async def main() -> None:
    client = TelegramClient()
    result = await client.set_webhook(
        url=settings.telegram_webhook_url,
        secret_token=settings.telegram_webhook_secret,
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())


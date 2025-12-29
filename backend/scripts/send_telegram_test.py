import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bot.telegram_client import telegram_notifier


async def main():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["trading_bot"]
    cfg = await db.configs.find_one({"type": "bot_config"}) or {}
    token = cfg.get("telegram_bot_token", "")
    chat = cfg.get("telegram_chat_id", "")
    verify = cfg.get("telegram_verify_ssl", True)

    telegram_notifier.initialize(bot_token=token, chat_id=chat, verify_ssl=verify)
    ok = telegram_notifier.send_message("Teste: bot ativo")
    print({"telegram_sent": ok})
    client.close()


if __name__ == "__main__":
    asyncio.run(main())

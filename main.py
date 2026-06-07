import logging
from telegram.ext import Application
from config import TELEGRAM_BOT_TOKEN
from bot.handlers import build_handlers

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)


def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    for handler in build_handlers():
        app.add_handler(handler)
    app.run_polling()


if __name__ == "__main__":
    main()

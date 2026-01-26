import logging

from platformdirs import user_data_dir
APP_NAME = 'daily-language-bot'

from .bot import Bot

logger = logging.getLogger(__name__)


def main():
    LOG_FORMAT = (
        "%(asctime)s | "
        "%(levelname)-8s | "
        "%(name)s | "
        "%(message)s"
    )

    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)

    logger.info("Starting German Number Telegram Bot")
    bot = Bot(user_data_dir(APP_NAME))
    bot.run()


if __name__ == "__main__":
    main()
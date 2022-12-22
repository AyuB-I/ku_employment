import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from tgbot.handlers.admin import admin_router
from tgbot.handlers.basics import basics_router
from tgbot.handlers.form_filling import form_filling_router
from tgbot.handlers.feedback import feedback_router
from tgbot.middlewares.config import ConfigMiddleware
from tgbot.middlewares.database import DbSessionMiddleware
from tgbot.config import load_config, Config
from tgbot.middlewares.throttling import ThrottlingMiddleware
from tgbot.misc import broadcaster
from tgbot.misc.default_commands import setup_default_commands
from tgbot.database.functions.setup import create_session_pool


logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, config: Config):
    await setup_default_commands(bot)
    await broadcaster.broadcast(bot, config.tgbot.admins, "Bot Started!")


async def on_shutdown(bot: Bot, config: Config):
    await broadcaster.broadcast(bot, config.tgbot.admins, "Bot Stopped!!")


def register_global_middlewares(dp: Dispatcher, config, session_pool):
    dp.message.middleware(ThrottlingMiddleware())
    dp.message.outer_middleware(ConfigMiddleware(config))
    dp.callback_query.outer_middleware(ConfigMiddleware(config))
    dp.message.middleware(DbSessionMiddleware(session_pool=session_pool))
    dp.callback_query.middleware(DbSessionMiddleware(session_pool=session_pool))


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info("Starting bot!")
    config = load_config(".env")

    storage = RedisStorage.from_url(
            url=config.tgbot.redis_url,
            connection_kwargs={"decode_responses": True}
        ) if config.tgbot.use_redis else MemoryStorage()
    bot = Bot(token=config.tgbot.bot_token, parse_mode="HTML")
    dp = Dispatcher(storage=storage)
    dp.message.filter(F.chat.type == "private")
    session_pool = await create_session_pool(db=config.db)

    for router in [
        admin_router,
        basics_router,
        form_filling_router,
        feedback_router
    ]:
        dp.include_router(router)

    register_global_middlewares(dp, config, session_pool)

    try:
        await on_startup(bot, config)
        await dp.start_polling(bot)
    finally:
        await on_shutdown(bot, config)
        await dp.storage.close()
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("The bot has been disabled!")

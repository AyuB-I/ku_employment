from aiogram.filters import BaseFilter
from aiogram.types import Message

from tgbot.config import Config


class AdminFilter(BaseFilter):
    async def __call__(self, message: Message, config: Config) -> bool:
        return message.from_user.id in config.tgbot.admins


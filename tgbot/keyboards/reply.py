from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession

from tgbot.config import Config
from tgbot.database.models.models import Users


async def make_menu_keyboard(session: AsyncSession, current_user_id: int, config: Config):
    form_id = await session.scalar(select(Users.form_id).where(Users.telegram_id == current_user_id))
    keyboard = ReplyKeyboardBuilder()
    admin_ids = config.tgbot.admins

    if form_id:
        keyboard.row(KeyboardButton(text="\U0001f4dd Anketamni yangilash"))  # Emoji "memo"
        keyboard.row(
            KeyboardButton(text="\U0001F4CB Mening anketam"),  # Emoji "clipboard"
            KeyboardButton(text="\U0001f3e2 Biz haqimizda")  # Emoji "office_building"
        )
        keyboard.row(
            KeyboardButton(text="\U0001F4AC Qayta aloqa"),  # Emoji "speech_balloon"
            KeyboardButton(text="\U0000260E Kontaktlar")  # Emoji "office_building"
        )
        if current_user_id in admin_ids:
            keyboard.row(KeyboardButton(text="\U000026A1"))  # Emoji "Zap"
    else:
        keyboard.row(KeyboardButton(text="\U0001f4dd Anketa to'ldirish"))  # Emoji "memo"
        keyboard.row(
            KeyboardButton(text="\U0001F4AC Qayta aloqa")  # Emoji "speech_balloon"
        )
        keyboard.row(
            KeyboardButton(text="\U0001f3e2 Biz haqimizda"),  # Emoji "office_building"
            KeyboardButton(text="\U0000260E Kontaktlar")  # Emoji "office_building"
        )
        if current_user_id in admin_ids:
            keyboard.row(KeyboardButton(text="\U000026A1"))  # Emoji "Zap"

    return keyboard.as_markup(resize_keyboard=True)


home_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="\U0001F3E0")]],  # Emoji "home"
    input_field_placeholder="Tushunarli qilib yozing :)",
    resize_keyboard=True
)

contact_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="\U0001F4DE Raqamni jo'natish", request_contact=True)],
        [KeyboardButton(text="\U0001F3E0")]  # Emoji "home"
    ],
    input_field_placeholder="Yozma ravishda jo'natmang!!!",
    resize_keyboard=True
)

confirming_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="\U00002714"),  # Emoji "heavy_check_mark"
            KeyboardButton(text="\U0000274C")  # Emoji "x"
        ]
    ],
    input_field_placeholder="Tugmalar orqali tasdiqlang!!!",
    resize_keyboard=True
)



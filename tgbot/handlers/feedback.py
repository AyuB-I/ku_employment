from asyncio import sleep as asleep
from contextlib import suppress

from aiogram import Router, Bot, F, html
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.config import Config
from tgbot.keyboards.reply import contact_keyboard, home_keyboard, confirming_keyboard, make_menu_keyboard
from tgbot.misc.states import FeedbackStates

flags = {"throttling_key": "default"}
feedback_router = Router()


@feedback_router.message(F.text == "\U0001F3E0", FeedbackStates(), flags=flags)  # Emoji "home"
@feedback_router.message(F.text == "\U0000274C", FeedbackStates.waiting_for_confirmation, flags=flags)  # Emoji "X"
async def cancel_feedback(message: Message, state: FSMContext, session: AsyncSession, config: Config):
    """  Cancel sending the feedback  """
    await state.clear()
    menu_keyboard = await make_menu_keyboard(session, message.from_user.id, config)
    await message.answer("<b>Asosiy Menyu\U0001F3E0</b>", reply_markup=menu_keyboard)


@feedback_router.message(F.text == "\U0001F4AC Qayta aloqa", flags=flags)
async def ask_feedback_text(message: Message, state: FSMContext):
    """  Ask a feedback message when user starts to send a feedback  """
    await state.set_state(FeedbackStates.asking_text)
    await message.answer(
        text="<b>Bu yerga xabar, taklif yoki shikoyatingizni jo'nating.\nUlar albatta ko'rib chiqiladi!</b>",
        reply_markup=home_keyboard)


@feedback_router.message(F.text, FeedbackStates.asking_text, flags=flags)
async def ask_phonenum(message: Message, state: FSMContext):
    """  Ask users phone number  """
    await state.set_state(FeedbackStates.asking_contact)
    feedback_text = html.quote(message.text)
    await message.answer("<b>Siz bilan bog'lanishimiz uchun quyidagi tugma orqali raqamingizni jo'nating.</b>",
                         reply_markup=contact_keyboard)
    await state.update_data(feedback_text=feedback_text)


@feedback_router.message(F.content_type == "contact", FeedbackStates.asking_contact, flags=flags)
async def ask_to_confirm(message: Message, state: FSMContext):
    """  Ask the user to confirm sending the feedback  """
    await state.set_state(FeedbackStates.waiting_for_confirmation)
    state_data = await state.get_data()
    phonenum = message.contact.phone_number
    await message.answer(text=f"{state_data['feedback_text']}\n\n<b>Ushbu xabarni jo'natishni tasdiqlaysizmi?</b>",
                         reply_markup=confirming_keyboard)
    await state.update_data(phonenum=phonenum)


@feedback_router.message(F.text == "\U00002714", FeedbackStates.waiting_for_confirmation, flags=flags)
async def send_feedback(message: Message, bot: Bot, state: FSMContext, session: AsyncSession, config: Config):
    """  Send the feedback to the Feedbacks Group  """
    state_data = await state.get_data()
    feedback_text = f"<b>Jo'natuvchi:</b>\n" \
                    f"    <b>ID:</b> {message.from_user.id}\n" \
                    f"    <b>Ismi:</b> {message.from_user.full_name}\n" \
                    f"    <b>Nomi:</b> @{message.from_user.username}\n" \
                    f"    <b>Raqami:</b> +{state_data['phonenum']}\n\n" \
                    f"<b>Xabar matni:</b>\n" \
                    f"{state_data['feedback_text']}"

    # Sending feedback to feedbacks group, but if it is not possible, send it to admin
    try:
        await bot.send_message(text=feedback_text, chat_id=config.tgbot.feedbacks_group)

    except Exception as error:
        for admin_id in config.tgbot.admins:
            with suppress(TelegramBadRequest):
                await bot.send_message(chat_id=admin_id, text=f"Guruhga xabar jo'natish jarayonida xatolik!\n"
                                                              f"<code>{error}</code>")
                await bot.send_message(text=feedback_text, chat_id=admin_id)
    menu_keyboard = await make_menu_keyboard(session, message.from_user.id, config)
    await message.answer(text="<b>Xabaringiz muvaffaqiyatli jo'natildi</b>\U0001F389",  # Emoji "tada"
                         reply_markup=menu_keyboard)
    await state.clear()


@feedback_router.message(FeedbackStates())
async def incorrect_message_alert(message: Message, bot: Bot):
    await message.delete()
    alert_message = await message.answer(text="<b>Iltimos ko'rsatmalarga amal qiling!</b>")
    await asleep(5)
    await bot.delete_message(chat_id=message.chat.id, message_id=alert_message.message_id)

from datetime import datetime
from contextlib import suppress
from asyncio import sleep as asleep

from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.config import Config
from tgbot.database.functions.functions import (add_profession, get_professions, get_profession, delete_profession,
                                                get_directions, delete_direction, add_direction, get_direction,
                                                get_form, get_user_ids_by_filter, get_stats)
from tgbot.database.models.models import NationsEnum, GendersEnum, WorkingStylesEnum, Users, Forms, UniversityDirections
from tgbot.keyboards.inline import (cancel_keyboard, raw_true_false_keyboard, make_directions_keyboard,
                                    make_professions_keyboard_for_admin, admin_functions, make_forms_keyboard,
                                    filter_categories_keyboard, menu_navigation_keyboard, genders_keyboard,
                                    university_grades_keyboard, working_style_keyboard)
from tgbot.keyboards.reply import make_menu_keyboard
from tgbot.misc.cbdata import MainCallbackFactory
from tgbot.misc.filters import AdminFilter
from tgbot.misc.states import ProfessionStates, DirectionStates, AdminStates

flags = {"throttling_key": "default"}
admin_router = Router()


# -----------------------------------------Working with Professions--------------------------------------------------- #

# Add a new profession to database
@admin_router.message(Command("add_profession"), flags=flags)
async def ask_profession_title(message: Message, state: FSMContext, session: AsyncSession):
    """  Ask the user for input the title of the profession  """
    await state.clear()
    await state.set_state(ProfessionStates.asking_title)
    all_professions = await get_professions(session)
    if len(all_professions) >= 20:
        await message.answer(
            "<code>XATO: Maksimal sohalar soni - 20</code>\n\n"
            "<b>Sohalar ma'lumotlar bazasida saqlanishi mumkin bo'lgan maksimal songa yetgan. Yangi "
            "soha qo'shish uchun /get_professions oraqli biron bir mavjud sohani o'chiring!</b>")
        await state.clear()
        return
    await message.answer("<b>Siz anketa savollaridagi sohalar orasiga yangi soha qo'shmoqchisiz!</b>\n",
                         reply_markup=ReplyKeyboardRemove())
    first_message = await message.answer("Yangi sohaning nomini kiriting:", reply_markup=cancel_keyboard)
    await state.update_data(first_message_id=first_message.message_id)


@admin_router.message(F.text.regexp(r"^[A-Za-z\s'-/.]{2,32}$"), ProfessionStates.asking_title, flags=flags)
async def ask_for_confirmation(message: Message, state: FSMContext, bot: Bot):
    """  Ask the user is he really going to add this profession  """
    await state.set_state(ProfessionStates.waiting_for_confirmation)
    await message.delete()
    state_data = await state.get_data()
    await bot.edit_message_text(text=f"<b>Soha nomi:</b> {message.text.capitalize()}", chat_id=message.chat.id,
                                message_id=state_data["first_message_id"])
    second_message = await message.answer("Yangi soha qo'shishni tasdiqlaysizmi?",
                                          reply_markup=raw_true_false_keyboard)
    await state.update_data(second_message_id=second_message.message_id, profession_title=message.text.lower())


@admin_router.message(ProfessionStates.asking_title)
async def incorrect_title_alert(message: Message, bot: Bot):
    """  Send an alert message about incorrect answer  """
    await message.delete()
    alert_message = await message.answer("<b>Sohaning nomi quyidagilarga mos shakilda bo'lishi kerak:</b>\n"
                                         "1. Lotincha xarflardan iborat bo'lishi\n"
                                         "2. 1ta belgidan ko'p bo'lishi va 32ta belgidan kam bo'lishi\n"
                                         "3. Mumkin bo'lgan simvollar:  <code>. / - '</code>")
    await asleep(10)
    await bot.delete_message(chat_id=message.chat.id, message_id=alert_message.message_id)


@admin_router.callback_query(MainCallbackFactory.filter(F.data == 1), ProfessionStates.waiting_for_confirmation)
async def add_new_profession(call: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession, config: Config):
    """  Add the new profession to database  """
    state_data = await state.get_data()
    menu_keyboard = await make_menu_keyboard(session, call.from_user.id, config)
    await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["second_message_id"])
    try:
        await add_profession(session, title=state_data["profession_title"])
    except IntegrityError:
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["first_message_id"])
        await call.message.answer(f"<b><u>Bunday soha mavjud!</u></b>", reply_markup=menu_keyboard)
        await state.clear()
        return
    await call.message.answer("Yangi soha qo'shildi\U0001F389", reply_markup=menu_keyboard)
    await state.clear()


@admin_router.callback_query(MainCallbackFactory.filter(F.data == 0), ProfessionStates.waiting_for_confirmation)
@admin_router.callback_query(MainCallbackFactory.filter(F.action == "home"), ProfessionStates.asking_title)
async def cancel_adding_profession(call: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession,
                                   config: Config):
    """  Cancel adding a new profession and go home  """
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    # I did two suppress block because I need to delete the second message firstly cause of making a pretty animation
    # of deleting message
    with suppress(KeyError):
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["second_message_id"])
    with suppress(KeyError):
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["first_message_id"])
    menu_keyboard = await make_menu_keyboard(session, call.from_user.id, config)
    await call.message.answer("<b><u>Yangi soha qo'shish bekor qilindi!</u></b>",
                              reply_markup=menu_keyboard)
    await state.clear()


@admin_router.message(Command("get_professions"), flags=flags)
async def show_professions(message: Message, state: FSMContext, session: AsyncSession, config: Config):
    """  Send the list of professions from database to user  """
    await state.set_state(ProfessionStates.showing_professions_list)
    all_professions = await get_professions(session)  # Get all existing professions from database
    keyboard = await make_professions_keyboard_for_admin(session)
    if not all_professions:
        menu_keyboard = await make_menu_keyboard(session, message.from_user.id, config)
        await message.answer("<u><b>Soha mavjud emas!</b></u>", reply_markup=menu_keyboard)
        await state.clear()
        return
    function_message = await message.answer(
        "<b>Sohalarni ko'rish va o'chirish.</b>", reply_markup=ReplyKeyboardRemove()
    )
    professions_message = await message.answer("Mavjud sohalar:", reply_markup=keyboard)
    await state.update_data(professions_message_id=professions_message.message_id,
                            function_message_id=function_message.message_id)


@admin_router.callback_query(MainCallbackFactory.filter(F.action == "delete"),
                             ProfessionStates.showing_professions_list)
async def ask_confirm_deleting_profession(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession,
                                          callback_data: MainCallbackFactory):
    """  Ask user for confirm deleting selected profession  """
    await call.answer(cache_time=1)
    await state.set_state(ProfessionStates.deleting_profession)
    await call.message.edit_reply_markup()
    state_data = await state.get_data()
    profession_title = (await get_profession(session, profession_id=callback_data.data))[0]
    text = f"Siz rosdan ham \"{profession_title.capitalize()}\" sohasini ma'lumotlar bazasidan " \
           f"<u>o'chirmoqchimisiz</u>?"
    with suppress(TelegramBadRequest):  # Skip if message is not exists
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["function_message_id"])
    professions_message = await bot.edit_message_text(text=text, chat_id=call.message.chat.id,
                                                      message_id=state_data["professions_message_id"],
                                                      reply_markup=raw_true_false_keyboard, )
    await state.update_data(profession_id=callback_data.data, profession_title=profession_title,
                            professionss_message_id=professions_message.message_id)


# Works when user cancels to delete the profession
@admin_router.callback_query(MainCallbackFactory.filter(F.data == 0), ProfessionStates.deleting_profession)
async def cancel_deleting_profession(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession):
    await call.answer(cache_time=1)
    await state.set_state(ProfessionStates.showing_professions_list)
    state_data = await state.get_data()
    keyboard = await make_professions_keyboard_for_admin(session)
    professions_message = await bot.edit_message_text(text="<b>Sohalar ro'yxati:</b>", reply_markup=keyboard,
                                                      chat_id=call.message.chat.id,
                                                      message_id=state_data["professions_message_id"])
    await state.update_data(professions_message_id=professions_message.message_id)


# Works when user confirms to delete the profession
@admin_router.callback_query(MainCallbackFactory.filter(F.data == 1), ProfessionStates.deleting_profession)
async def complete_deleting_profession(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession,
                                       config: Config):
    """  Delete selected profession from database  """
    await call.answer(cache_time=1)
    await state.set_state(ProfessionStates.showing_professions_list)
    state_data = await state.get_data()
    profession_title = state_data["profession_title"]
    text = f"<u><b>\"{profession_title.capitalize()}\" yo'nalishini ma'lumotlar bazasidan o'chirildi!</b></u>"
    await delete_profession(session, profession_id=state_data["profession_id"])  # Delete profession from db
    await bot.edit_message_text(text, message_id=state_data["professions_message_id"],
                                chat_id=call.message.chat.id)
    all_professions = await get_professions(session)
    if not all_professions:
        menu_keyboard = await make_menu_keyboard(session, call.from_user.id, config)
        await call.message.answer("<b><u>Boshqa sohalar mavjud emas!</u></b>", reply_markup=menu_keyboard)
        await state.clear()
        return

    keyboard = await make_professions_keyboard_for_admin(session)
    professions_message = await call.message.answer("<b>Sohalar ro'yxati:</b>", reply_markup=keyboard)
    await state.update_data(professions_message_id=professions_message.message_id)


@admin_router.callback_query(MainCallbackFactory.filter(F.action == "home"), ProfessionStates())
async def cancel_all_profession_actions(call: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession,
                                        config: Config):
    """  Cancel all actions and go home  """
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    with suppress(KeyError, TelegramBadRequest):
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["professions_message_id"])
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["professions_list_message_id"])
    menu_keyboard = await make_menu_keyboard(session, call.from_user.id, config)
    await call.message.answer("<b>Asosiy menyu\U0001F3E0</b>", reply_markup=menu_keyboard)
    await state.clear()


# =================================================Professions======================================================== #


# -------------------------------------Working with University Directions--------------------------------------------- #

# Add a new direction to database
@admin_router.message(Command("add_direction"), flags=flags)
async def ask_direction_title(message: Message, state: FSMContext, session: AsyncSession):
    """  Ask the user for input the title of the university direction  """
    await state.clear()
    await state.set_state(DirectionStates.asking_title)
    all_directions = await get_directions(session)
    if len(all_directions) >= 20:
        await message.answer(
            "<code>XATO: Maksimal yo'nalishlar soni - 20</code>\n\n"
            "<b>Ta'lim yo'nalishlari ma'lumotlar bazasida saqlanishi mumkin bo'lgan maksimal songa yetgan. Yangi "
            "yo'nalish qo'shish uchun /get_directions oraqli biron bir mavjud yo'nalishni o'chiring!</b>")
        await state.clear()
        return
    await message.answer(
        "<b>Siz anketa savollaridagi ta'lim yo'nalishlari orasiga yangi yo'nalish qo'shmoqchisiz!</b>\n",
        reply_markup=ReplyKeyboardRemove()
    )
    first_message = await message.answer("Yangi ta'lim yo'nalishining nomini kiriting:", reply_markup=cancel_keyboard)
    await state.update_data(first_message_id=first_message.message_id)


@admin_router.message(F.text.regexp(r"^[A-Za-z\s'-/.]{2,32}$"), DirectionStates.asking_title, flags=flags)
async def ask_for_confirmation(message: Message, state: FSMContext, bot: Bot):
    """  Ask the user is he really going to add this direction  """
    await state.set_state(DirectionStates.waiting_for_confirmation)
    await message.delete()
    state_data = await state.get_data()
    await bot.edit_message_text(text=f"<b>Yo'nalish nomi:</b> {message.text.capitalize()}", chat_id=message.chat.id,
                                message_id=state_data["first_message_id"])
    second_message = await message.answer("Yangi ta'lim yo'nalishi qo'shishni tasdiqlaysizmi?",
                                          reply_markup=raw_true_false_keyboard)
    await state.update_data(second_message_id=second_message.message_id, direction_title=message.text.lower())


@admin_router.message(DirectionStates.asking_title)
async def incorrect_title_alert(message: Message, bot: Bot):
    """  Send an alert message about incorrect answer  """
    await message.delete()
    alert_message = await message.answer(
        "<b>Ta'lim yo'nalishining nomi quyidagilarga mos shakilda bo'lishi kerak:</b>\n"
        "1. Lotincha xarflardan iborat bo'lishi\n"
        "2. 1ta belgidan ko'p bo'lishi va 32ta belgidan kam bo'lishi\n"
        "3. Mumkin bo'lgan simvollar:  <code>. / - '</code>")
    await asleep(10)
    await bot.delete_message(chat_id=message.chat.id, message_id=alert_message.message_id)


@admin_router.callback_query(MainCallbackFactory.filter(F.data == 1), DirectionStates.waiting_for_confirmation)
async def add_new_direction(call: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession, config: Config):
    """  Add the new direction to database  """
    state_data = await state.get_data()
    await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["second_message_id"])
    menu_keyboard = await make_menu_keyboard(session, call.from_user.id, config)
    try:
        await add_direction(session, title=state_data["direction_title"])
    except IntegrityError:
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["first_message_id"])
        await call.message.answer("<b><u>Bunday ta'lim yo'nalishi mavjud!</u></b>", reply_markup=menu_keyboard)
        await state.clear()
        return
    await call.message.answer("Yangi ta'lim yo'nalishi qo'shildi\U0001F389", reply_markup=menu_keyboard)  # Emoji "tada"
    await state.clear()


@admin_router.callback_query(MainCallbackFactory.filter(F.data == 0), DirectionStates.waiting_for_confirmation)
@admin_router.callback_query(MainCallbackFactory.filter(F.action == "home"), DirectionStates.asking_title)
async def cancel_adding_direction(call: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession,
                                  config: Config):
    """  Cancel adding a new direction and go home  """
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    # I did two suppress block because I need to delete the second message firstly cause of making a pretty animation
    # of deleting message
    with suppress(KeyError):
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["second_message_id"])
    with suppress(KeyError):
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["first_message_id"])
    menu_keyboard = await make_menu_keyboard(session, call.from_user.id, config)
    await call.message.answer("<b><u>Yangi o'quv yonalishi qo'shish bekor qilindi!</u></b>",
                              reply_markup=menu_keyboard)
    await state.clear()


@admin_router.message(Command("get_directions"), flags=flags)
async def show_directions(message: Message, state: FSMContext, session: AsyncSession, config: Config):
    """  Send the list of directions from database to user  """
    await state.set_state(DirectionStates.showing_directions_list)
    all_directions = await get_directions(session)  # Get all directions from database
    keyboard = await make_directions_keyboard(session, with_cross=True)
    if not all_directions:
        menu_keyboard = await make_menu_keyboard(session, message.from_user.id, config)
        await message.answer("<u><b>Ta'lim yo'nalishlari mavjud emas!</b></u>", reply_markup=menu_keyboard)
        await state.clear()
        return
    function_message = await message.answer(
        "<b>Yo'nalishlarni ko'rish va o'chirish.</b>", reply_markup=ReplyKeyboardRemove()
    )
    directions_message = await message.answer("Mavjud ta'lim yo'nalishlari:", reply_markup=keyboard)
    await state.update_data(directions_message_id=directions_message.message_id,
                            function_message_id=function_message.message_id)


@admin_router.callback_query(MainCallbackFactory.filter(F.action == "delete"), DirectionStates.showing_directions_list)
async def ask_confirm_deleting_direction(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession,
                                         callback_data: MainCallbackFactory):
    """  Ask user for confirm deleting selected direction  """
    await call.answer(cache_time=1)
    await state.set_state(DirectionStates.deleting_direction)
    await call.message.edit_reply_markup()
    state_data = await state.get_data()
    direction_title = (await get_direction(session, direction_id=callback_data.data))[0]  # Get direction title from db
    text = f"Siz rosdan ham \"{direction_title.capitalize()}\" yo'nalishini ma'lumotlar bazasidan " \
           f"<u>o'chirmoqchimisiz</u>?"
    with suppress(TelegramBadRequest):  # Skip if message is not exists
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["function_message_id"])
    directions_message = await bot.edit_message_text(text=text, chat_id=call.message.chat.id,
                                                     message_id=state_data["directions_message_id"],
                                                     reply_markup=raw_true_false_keyboard, )
    await state.update_data(direction_id=callback_data.data, direction_title=direction_title,
                            directions_message_id=directions_message.message_id)


# Works when user cancels to delete the direction
@admin_router.callback_query(MainCallbackFactory.filter(F.data == 0), DirectionStates.deleting_direction)
async def cancel_deleting_direction(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession):
    await call.answer(cache_time=1)
    await state.set_state(DirectionStates.showing_directions_list)
    state_data = await state.get_data()
    keyboard = await make_directions_keyboard(session, with_cross=True)
    directions_message = await bot.edit_message_text(text="<b>Ta'lim yo'nalishlari ro'yxati:</b>",
                                                     reply_markup=keyboard, chat_id=call.message.chat.id,
                                                     message_id=state_data["directions_message_id"])
    await state.update_data(directions_message_id=directions_message.message_id)


# Works when user confirms to delete the direction
@admin_router.callback_query(MainCallbackFactory.filter(F.data == 1), DirectionStates.deleting_direction)
async def complete_deleting_direction(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession,
                                      config: Config):
    """  Delete selected direction from database  """
    await call.answer(cache_time=1)
    await state.set_state(DirectionStates.showing_directions_list)
    state_data = await state.get_data()
    direction_title = state_data["direction_title"]
    text = f"<u><b>\"{direction_title.capitalize()}\" yo'nalishini ma'lumotlar bazasidan o'chirildi!</b></u>"
    await delete_direction(session, direction_id=state_data["direction_id"])  # Delete direction from db
    await bot.edit_message_text(text, message_id=state_data["directions_message_id"],
                                chat_id=call.message.chat.id)
    all_directions = await get_directions(session)
    if not all_directions:
        menu_keyboard = await make_menu_keyboard(session, call.from_user.id, config)
        await call.message.answer("<b><u>Boshqa ta'lim yo'nalishlari mavjud emas!</u></b>", reply_markup=menu_keyboard)
        await state.clear()
        return

    keyboard = await make_directions_keyboard(session, with_cross=True)
    directions_message = await call.message.answer("<b>Sohalar ro'yxati:</b>", reply_markup=keyboard)
    await state.update_data(directions_message_id=directions_message.message_id)


@admin_router.callback_query(MainCallbackFactory.filter(F.action == "home"), DirectionStates())
async def cancel_all_direction_actions(call: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession,
                                       config: Config):
    """  Cancel all actions and go home  """
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    with suppress(KeyError, TelegramBadRequest):
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["directions_message_id"])
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["function_message_id"])
    menu_keyboard = await make_menu_keyboard(session, call.from_user.id, config)
    await call.message.answer("<b>Asosiy menyu\U0001F3E0</b>",
                              reply_markup=menu_keyboard)
    await state.clear()

# ===============================================University Directions================================================ #


# ---------------------------------------------Working with Admin Mode------------------------------------------------ #

@admin_router.message(F.text == "\U000026A1", AdminFilter(), flags=flags)
async def show_admin_functions(message: Message, state: FSMContext):
    """  Handle the 'zap' button and direct the admin to the admin mode  """
    await state.set_state(AdminStates.admin_mode)
    await message.answer("Admin Rejimi!", reply_markup=ReplyKeyboardRemove())
    function_message = await message.answer("Mavjud funktsiyalar:", reply_markup=admin_functions)
    await state.update_data(function_message_id=function_message.message_id)


@admin_router.callback_query(MainCallbackFactory.filter(F.action == "home"), AdminStates())
async def go_home(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession, config: Config):
    """  Return to main menu  """
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    current_state = await state.get_state()
    menu_keyboard = await make_menu_keyboard(session, call.from_user.id, config)
    if current_state == "AdminStates:forms":
        sent_forms = state_data["sent_forms"]
        for form_id, photo_id in sent_forms:
            await bot.delete_message(chat_id=call.message.chat.id, message_id=form_id)
            await bot.delete_message(chat_id=call.message.chat.id, message_id=photo_id)
    try:
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["function_message_id"])
    except TelegramBadRequest:
        await bot.edit_message_text(text="<i>(O'chirilgan xabar)</i>", chat_id=call.message.chat.id,
                                         message_id=state_data["function_message_id"])
    await call.message.answer("Asosiy menyu\U0001F3E0", reply_markup=menu_keyboard)
    await state.clear()


# -------------------------------------------------Function Show Forms------------------------------------------------ #

@admin_router.callback_query(MainCallbackFactory.filter(F.action == "back"), AdminStates.forms)
async def go_back_from_forms(call: CallbackQuery, bot: Bot, state: FSMContext):
    """  Return to admin functions from state "AdminStates:forms" and delete sent forms  """
    await call.answer(cache_time=1)
    await state.set_state(AdminStates.admin_mode)
    state_data = await state.get_data()
    sent_forms = state_data["sent_forms"]
    for form_id, photo_id in sent_forms:
        await bot.delete_message(chat_id=call.message.chat.id, message_id=form_id)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=photo_id)
    await bot.edit_message_text(text="Mavjud funktsiyalar:", chat_id=call.message.chat.id,
                                message_id=state_data["function_message_id"], reply_markup=admin_functions)


@admin_router.callback_query(MainCallbackFactory.filter(F.action == "show_forms"), AdminStates.admin_mode)
async def send_form_list(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession):
    """  Send a list of forms and names of its owners to admin
    with inline keyboard of each form id from db  """
    await call.answer(cache_time=1)
    await state.set_state(AdminStates.forms)
    state_data = await state.get_data()
    keyboard_data = await make_forms_keyboard(session)
    # Converting from JSON to InlineKeyboardMarkup
    forms_keyboard = InlineKeyboardMarkup.parse_raw(keyboard_data["keyboard"])
    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=state_data["function_message_id"],
                                text=keyboard_data["text"], reply_markup=forms_keyboard)
    # We will use empty list "sent_forms" soon to save ids of sent forms messages
    # to delete them when we are leaving from state "AdminStates:forms"
    await state.update_data(sent_forms=[], keyboard_data=keyboard_data, filter_type=None)


@admin_router.callback_query(MainCallbackFactory.filter(F.action == "filter"), AdminStates.forms)
async def filter_sent_forms(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory,
                            session: AsyncSession):
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    next_filter = None
    if callback_data.data is None:
        next_filter = "male"
    elif callback_data.data == "male":
        next_filter = "female"
    elif callback_data.data == "female":
        next_filter = "working"
    elif callback_data.data == "working":
        next_filter = "not_working"
    elif callback_data.data == "not_working":
        next_filter = 1
    elif callback_data.data == 1:
        next_filter = 2
    elif callback_data.data == 2:
        next_filter = 3
    elif callback_data.data == 3:
        next_filter = 4
    elif callback_data.data == 4:
        next_filter = 5
    keyboard_data = await make_forms_keyboard(session, filter_type=next_filter)
    forms_keyboard = InlineKeyboardMarkup.parse_raw(keyboard_data["keyboard"])
    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=state_data["function_message_id"],
                                text=keyboard_data["text"], reply_markup=forms_keyboard)
    await state.update_data(keyboard_data=keyboard_data, filter_type=next_filter)


@admin_router.callback_query(MainCallbackFactory.filter(F.action == "next"), AdminStates.forms)
async def send_next_form_list(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession,
                              callback_data: MainCallbackFactory):
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    old_keyboard_data = state_data["keyboard_data"]
    begin = datetime.fromtimestamp(old_keyboard_data["smallest_date"])
    keyboard_data = await make_forms_keyboard(session, begin=begin, action="next", counter=callback_data.counter,
                                              filter_type=state_data["filter_type"])
    forms_keyboard = InlineKeyboardMarkup.parse_raw(keyboard_data["keyboard"])
    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=state_data["function_message_id"],
                                text=keyboard_data["text"], reply_markup=forms_keyboard)
    await state.update_data(keyboard_data=keyboard_data)


@admin_router.callback_query(MainCallbackFactory.filter(F.action == "previous"), AdminStates.forms)
async def send_previous_form_list(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession,
                                  callback_data: MainCallbackFactory):
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    old_keyboard_data = state_data["keyboard_data"]
    begin = datetime.fromtimestamp(old_keyboard_data["biggest_date"])
    # Cause of this condition is to make a correct counter when user goes back to previous list of forms
    counter = ((callback_data.counter - 1) // 10 - 1) * 10 if callback_data.counter >= 20 else 0
    keyboard_data = await make_forms_keyboard(session, begin=begin, action="previous", counter=counter,
                                              filter_type=state_data["filter_type"])
    forms_keyboard = InlineKeyboardMarkup.parse_raw(keyboard_data["keyboard"])
    await bot.edit_message_text(chat_id=call.message.chat.id, message_id=state_data["function_message_id"],
                                text=keyboard_data["text"], reply_markup=forms_keyboard)
    await state.update_data(keyboard_data=keyboard_data)


@admin_router.callback_query(MainCallbackFactory.filter(F.action == "select"), AdminStates.forms)
async def show_form(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession,
                    callback_data: MainCallbackFactory):
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    form = await get_form(session, callback_data.data)
    gender = 'Erkak' if form.gender == GendersEnum.MALE else 'Ayol'
    professions = "Mavjud emas!" if not form.professions else ', '.join(form.professions)
    nation = "O'zbek"
    if form.nation == NationsEnum.RUSSIAN:
        nation = "Rus"
    elif form.nation == NationsEnum.OTHER:
        nation = "Boshqa"

    university_grade = 'Magistr' if form.university_grade == 5 else form.university_grade
    university_direction = form.direction.capitalize() if form.direction is not None else "Ma'lumotlar bazasidan o'chirilgan!"
    working_company = "Mavjud emas!" if not form.working_company else f"\n    <b>Nomi:</b> {form.working_company[0]}" \
                                                                      f"\n    <b>Lavozimi:</b> {form.working_company[1]}"
    driver_license = "Bor" if form.driver_license else "Yo'q"
    languages = ""
    for i in form.languages:
        languages += f"    <b>{i[0]}:</b> {i[1]}%\n"

    apps = ""
    for i in form.apps:
        apps += f"    <b>{i[0]}:</b> {i[1]}%\n"

    working_style = 'Jamoada' if form.working_style == WorkingStylesEnum.COLLECTIVE else 'Individual'
    salary = "1 - 2 milion so'm"
    if form.wanted_salary == 2:
        salary = "3 - 4 million so'm"
    elif form.wanted_salary == 3:
        salary = "5 million so'm va undan yuqori"

    username = "Mavjud emas!" if form.username is None else f"@{form.username}"
    registered_at = f"{form.registered_at.day}.{form.registered_at.month}.{form.registered_at.year} " \
        f"{form.registered_at.hour}:{form.registered_at.minute}:{form.registered_at.second}"
    updated_at = "\n" if not form.updated_at else \
        f"\n<b>Yangilangan vaqt:</b> " \
        f"{form.updated_at.day}.{form.updated_at.month}.{form.updated_at.year} " \
        f"{form.updated_at.hour}:{form.updated_at.minute}:{form.updated_at.second}"

    form_text = f"<b>Ism va Familiya:</b> {form.full_name}\n" \
                f"<b>Tug'ilgan sana:</b> {form.birth_date.day}.{form.birth_date.month}.{form.birth_date.year}\n" \
                f"<b>Jins:</b> {gender}\n" \
                f"<b>Telefon raqam:</b> {form.phonenum}\n" \
                f"<b>Qiziqtirgan sohalar:</b> {professions}\n" \
                f"<b>Yashash manzil:</b> {form.address}\n" \
                f"<b>Millat:</b> {nation}\n" \
                f"<b>Kurs:</b> {university_grade}\n" \
                f"<b>Ta'lim yo'nalishi:</b> {university_direction}\n" \
                f"<b>Ish o'rni:</b> {working_company}\n" \
                f"<b>Oilaviy ahvol:</b> {'Turmush qurgan' if form.marital_status else 'Turmush qurmagan'}\n" \
                f"<b>Haydovchilik guvohnomasi:</b> {driver_license}\n" \
                f"<b>Tillar:</b>\n" \
                f"{languages}" \
                f"<b>Dasturlar:</b>\n" \
                f"{apps}" \
                f"<b>Ishlash uslubi:</b> {working_style}\n" \
                f"<b>Oylik maoshi:</b> {salary}\n" \
                f"<b>Ijobiy ta'rif:</b> {form.positive_assessment}\n" \
                f"<b>Salbiy ta'rif:</b> {form.negative_assessment}\n" \
                f"<b>Telegramdagi ismi:</b> {form.telegram_name}\n" \
                f"<b>Telegramdagi nomi:</b> {username}\n" \
                f"<b>Telegram ID:</b> {form.telegram_id}\n" \
                f"<b>Tuzilgan vaqt:</b> {registered_at}" \
                f"{updated_at}"
    old_keyboard_data = state_data["keyboard_data"]
    old_forms_keyboard = InlineKeyboardMarkup.parse_raw(old_keyboard_data["keyboard"])
    await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["function_message_id"])
    form_photo_message = await call.message.answer_photo(photo=form.photo_id)
    form_message = await bot.send_message(text=form_text, chat_id=call.message.chat.id,
                                          reply_to_message_id=form_photo_message.message_id)
    function_message = await call.message.answer(text=old_keyboard_data["text"],
                                                 reply_markup=old_forms_keyboard)
    sent_forms = state_data["sent_forms"]
    sent_forms.append((form_message.message_id, form_photo_message.message_id))
    await state.update_data(sent_forms=sent_forms, function_message_id=function_message.message_id)

# ================================================Function Show Forms================================================= #


# ------------------------------------------------Function Mailing---------------------------------------------------- #

@admin_router.callback_query(MainCallbackFactory.filter(F.action == "mailing"), AdminStates.admin_mode)
async def ask_mailing_filter_category(call: CallbackQuery, bot: Bot, state: FSMContext):
    """  Ask the target of mailing  """
    await call.answer(cache_time=1)
    await state.set_state(AdminStates.mailing_target_categories)
    state_data = await state.get_data()
    function_title_message = await bot.edit_message_text(
        text="<b>E'lon berish yoki xabar jo'natish!</b>",
        chat_id=call.message.chat.id, message_id=state_data["function_message_id"])
    function_message = await call.message.answer(
        text="<b>Keling mo'ljalimizni tanlab olamiz, aynan qaysi kategoriyadagilarga xabar jo'natmoqchisiz?</b>",
        reply_markup=filter_categories_keyboard)
    await state.update_data(function_message_id=function_message.message_id,
                            function_title_message_id=function_title_message.message_id)


@admin_router.callback_query(MainCallbackFactory.filter(F.action == "filter"), AdminStates.mailing_target_categories)
async def ask_mailing_filter(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession,
                             callback_data: MainCallbackFactory):
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    if callback_data.data == "everyone":
        await state.set_state(AdminStates.mailing_text)
        filter_text = f"<b>Mo'ljal:</b> Barcha"
        filter_message = await bot.edit_message_text(
            text=filter_text, chat_id=call.message.chat.id, message_id=state_data["function_message_id"],)
        function_message = await call.message.answer(
            text="<b>Barchaga jo'natmoqchi bo'lgan e'lon yoki xabaringizni yuboring.</b>",
            reply_markup=menu_navigation_keyboard)
        await state.update_data(filter_text=filter_text, filter_category=callback_data.data, target=None,
                                filter_message_id=filter_message.message_id,
                                function_message_id=function_message.message_id)

    elif callback_data.data == "one_user":
        await state.set_state(AdminStates.mailing_user_id)
        filter_text = f"<b>Mo'ljal:</b>\n    <b>Bitta foydalanuvchi:</b>\n"
        filter_message = await bot.edit_message_text(
            text=filter_text, chat_id=call.message.chat.id, message_id=state_data["function_message_id"])
        function_message = await call.message.answer(
            text="<b>Siz xabar jo'natmoqchi bo'lgan foyalanuvchining Telegram ID raqamini jo'nating.\n</b>"
                 "ID raqamni foydalanuvchining anketasidan olishingiz mumkin.",
            reply_markup=menu_navigation_keyboard)
        await state.update_data(filter_text=filter_text, filter_category=callback_data.data, target=None,
                                filter_message_id=filter_message.message_id,
                                function_message_id=function_message.message_id)

    elif callback_data.data == "gender":
        await state.set_state(AdminStates.mailing_target)
        filter_text = f"<b>Mo'ljal:</b> Jins - "
        filter_message = await bot.edit_message_text(
            text=filter_text, chat_id=call.message.chat.id, message_id=state_data["function_message_id"])
        function_message = await call.message.answer(
            text="<b>Aynan qaysi jins vakillari?</b>",
            reply_markup=genders_keyboard)
        await state.update_data(filter_text=filter_text, filter_category=callback_data.data,
                                filter_message_id=filter_message.message_id,
                                function_message_id=function_message.message_id)

    elif callback_data.data == "university_grade":
        await state.set_state(AdminStates.mailing_target)
        filter_text = f"<b>Mo'ljal:</b> Kurs - "
        filter_message = await bot.edit_message_text(
            text=filter_text, chat_id=call.message.chat.id, message_id=state_data["function_message_id"])
        function_message = await call.message.answer(
            text="<b>Aynan qaysi kurs a'zolari?</b>",
            reply_markup=university_grades_keyboard)
        await state.update_data(filter_text=filter_text, filter_category=callback_data.data,
                                filter_message_id=filter_message.message_id,
                                function_message_id=function_message.message_id)

    elif callback_data.data == "university_direction":
        await state.set_state(AdminStates.mailing_target)
        filter_text = f"<b>Mo'ljal:</b> Ta'lim yo'nalishi - "
        keyboard = await make_directions_keyboard(session, with_cross=False)
        filter_message = await bot.edit_message_text(
            text=filter_text, chat_id=call.message.chat.id, message_id=state_data["function_message_id"])
        function_message = await call.message.answer(
            text="<b>Aynan qaysi ta'lim yo'nalishi a'zolari?</b>",
            reply_markup=keyboard)
        await state.update_data(filter_text=filter_text, filter_category=callback_data.data,
                                filter_message_id=filter_message.message_id,
                                function_message_id=function_message.message_id)

    elif callback_data.data == "working_style":
        await state.set_state(AdminStates.mailing_target)
        filter_text = f"<b>Mo'ljal:</b> Ishlash uslubi - "
        filter_message = await bot.edit_message_text(
            text=filter_text, chat_id=call.message.chat.id, message_id=state_data["function_message_id"])
        function_message = await call.message.answer(
            text="<b>Aynan qaysi uslubda ishlashni hush ko'ruvchi foydalanuvchilar?</b>",
            reply_markup=working_style_keyboard)
        await state.update_data(filter_text=filter_text, filter_category=callback_data.data,
                                filter_message_id=filter_message.message_id,
                                function_message_id=function_message.message_id)


@admin_router.message(F.text.regexp(r"^\d{4,11}$"), AdminStates.mailing_user_id, flags=flags)
async def ask_mailing_text_for_user(message: Message, bot: Bot, state: FSMContext, session: AsyncSession):
    state_data = await state.get_data()
    await message.delete()
    user_id = int(message.text)
    filter_text = state_data["filter_text"]
    query = await session.execute(
        select(Users.telegram_id, Users.telegram_name, Users.username, Users.form_id).where(
            Users.telegram_id == user_id)
    )
    # Send an alert message if the user with given id not found
    try:
        user_data = query.all()[0]
    except IndexError:
        alert_message = await message.answer("<b>Bunday ID raqamli foydalanuvchi ma'lumotlar bazasida yo'q!</b>")
        await asleep(5)
        await bot.delete_message(chat_id=message.chat.id, message_id=alert_message.message_id)
        return
    await state.set_state(AdminStates.mailing_text)
    full_name = await session.scalar(select(Forms.full_name).where(Forms.form_id == user_data[3]))
    username = "Mavjud emas!" if not user_data[2] else f"@{user_data[2]}"
    filter_text += f"        <b>Telegram ID:</b> {user_data[0]}\n" \
                   f"        <b>Telegramdagi ismi:</b> {user_data[1]}\n" \
                   f"        <b>Telegramdagi nomi:</b> {username}\n" \
                   f"        <b>Anketadagi ismi:</b> {full_name}"
    await bot.edit_message_text(text=filter_text, chat_id=message.chat.id, message_id=state_data["filter_message_id"])
    await bot.edit_message_text(text="<b>Jo'natmoqchi bo'lgan e'lon yoki xabaringizni yuboring.</b>",
                                chat_id=message.chat.id, message_id=state_data["function_message_id"],
                                reply_markup=menu_navigation_keyboard)
    await state.update_data(filter_text=filter_text, target_user_id=user_data[0])


@admin_router.callback_query(MainCallbackFactory.filter(F.data), AdminStates.mailing_target)
async def ask_mailing_text(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory,
                           session: AsyncSession):
    await call.answer(cache_time=1)
    await state.set_state(AdminStates.mailing_text)
    state_data = await state.get_data()
    filter_text = state_data["filter_text"]
    if callback_data.data == "MALE":
        filter_text += "Erkak"
    elif callback_data.data == "FEMALE":
        filter_text += "Ayol"
    # We need second condition because callback data from university directions will return direction_id
    # that can be similar with digits in lists below
    elif callback_data.data in [1, 2, 3, 4] and state_data["filter_category"] == "university_grade":
        filter_text += f"{callback_data.data}"
    elif callback_data.data == 5 and state_data["filter_category"] == "university_grade":
        filter_text += "Magistr"
    elif callback_data.data == "COLLECTIVE":
        filter_text += "Jamoada"
    elif callback_data.data == "INDIVIDUAL":
        filter_text += "Individual"
    else:
        # There is only direction's id in callback data so getting direction title from database using direction id
        direction_id = callback_data.data
        direction_title = await session.scalar(select(UniversityDirections.title).where(
            UniversityDirections.direction_id == direction_id))
        filter_text += direction_title.capitalize()

    await bot.edit_message_text(text=filter_text, chat_id=call.message.chat.id,
                                message_id=state_data["filter_message_id"])
    await bot.edit_message_text(text="<b>Jo'natmoqchi bo'lgan e'lon yoki xabaringizni yuboring.</b>",
                                chat_id=call.message.chat.id, message_id=state_data["function_message_id"],
                                reply_markup=menu_navigation_keyboard)
    await state.update_data(filter_text=filter_text, target=callback_data.data)


@admin_router.message(AdminStates.mailing_text, flags=flags)
async def ask_to_confirm(message: Message, bot: Bot, state: FSMContext):
    await state.set_state(AdminStates.mailing_confirm)
    state_data = await state.get_data()
    await message.delete()
    await bot.delete_message(chat_id=message.chat.id, message_id=state_data["function_message_id"])
    copied_message = await message.send_copy(chat_id=message.chat.id)
    function_message = await message.answer(text="<b>Ushbu xabarni barchaga jo'natishga rozimisiz?</b>",
                                            reply_markup=raw_true_false_keyboard)
    await state.update_data(copied_message_id=copied_message.message_id,
                            function_message_id=function_message.message_id)


@admin_router.callback_query(MainCallbackFactory.filter(F.data == 0), AdminStates.mailing_confirm)
async def cancel_mailing(call: CallbackQuery, bot: Bot, state: FSMContext):
    """  Cancel mailing and return to admin mode  """
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["copied_message_id"])
    await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["filter_message_id"])
    await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["function_title_message_id"])
    await state.clear()
    await state.set_state(AdminStates.admin_mode)
    function_message = await call.message.edit_text("Mavjud funktsiyalar:", reply_markup=admin_functions)
    await state.update_data(function_message_id=function_message.message_id)


@admin_router.callback_query(MainCallbackFactory.filter(F.data == 1), AdminStates.mailing_confirm)
async def complete_mailing(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession):
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    target_category = state_data["filter_category"]
    target = state_data["target"]
    if target_category == "one_user":
        user_ids = [state_data["target_user_id"]]
    else:
        user_ids = await get_user_ids_by_filter(session, target_category, target)
    counter = 0
    try:
        for user_id in user_ids:
            if user_id == call.from_user.id:
                continue
            with suppress(TelegramBadRequest, TelegramForbiddenError):
                await bot.copy_message(chat_id=user_id, from_chat_id=call.message.chat.id,
                                       message_id=state_data["copied_message_id"])
                counter += 1
    except Exception as error:
        await call.message.answer(text=f"Xato! Dasturchiga murojat qiling!\n{error}")
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["copied_message_id"])
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["filter_message_id"])
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["function_title_message_id"])
        await state.clear()
        function_message = await call.message.edit_text("Mavjud funktsiyalar:", reply_markup=admin_functions)
        await state.set_state(AdminStates.admin_mode)
        await state.update_data(function_message_id=function_message.message_id)
    else:
        await call.message.edit_reply_markup()
        await call.message.answer(f"E'lon {counter} kishiga muvaffaqiyatli jo'natildi\U0001F389")
        function_message = await call.message.answer("Mavjud funktsiyalar:", reply_markup=admin_functions)
        await state.clear()
        await state.set_state(AdminStates.admin_mode)
        await state.update_data(function_message_id=function_message.message_id)


@admin_router.callback_query(MainCallbackFactory.filter(F.action == "back"), AdminStates.mailing_target_categories)
@admin_router.callback_query(MainCallbackFactory.filter(F.action == "back"), AdminStates.mailing_target)
@admin_router.callback_query(MainCallbackFactory.filter(F.action == "back"), AdminStates.mailing_user_id)
@admin_router.callback_query(MainCallbackFactory.filter(F.action == "back"), AdminStates.mailing_text)
async def go_back_from_mailing(call: CallbackQuery, bot: Bot, state: FSMContext):
    """  Return to admin functions from state "AdminStates:stats"  """
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    current_state = await state.get_state()
    if current_state == "AdminStates:mailing_target_categories":
        await state.set_state(AdminStates.admin_mode)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["function_title_message_id"])
        await bot.edit_message_text(text="Mavjud funktsiyalar:", chat_id=call.message.chat.id,
                                    message_id=state_data["function_message_id"], reply_markup=admin_functions)
    else:
        await state.set_state(AdminStates.mailing_target_categories)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["filter_message_id"])
        await bot.edit_message_text(
            text="<b>Keling mo'ljalimizni tanlab olamiz, aynan qaysi kategoriyadagilarga xabar jo'natmoqchisiz?</b>",
            chat_id=call.message.chat.id, message_id=state_data["function_message_id"],
            reply_markup=filter_categories_keyboard)

# ==================================================Function Mailing================================================== #


# ------------------------------------------------Function Statistics------------------------------------------------- #

@admin_router.callback_query(MainCallbackFactory.filter(F.action == "show_stats"), AdminStates.admin_mode)
async def send_stats(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession):
    """  Send statistics of users and forms received from database using function 'get_stats'  """
    await call.answer(cache_time=1)
    await state.set_state(AdminStates.stats)
    state_data = await state.get_data()
    stats = await get_stats(session)
    # Do not remove the whitespaces!!!
    await bot.edit_message_text(text=f"""<b>Statistika:</b>\n
    <b><i>Foydalanuvchilar:</i></b>\n
    <i>Oxirgi bir kun:</i>      <code>{stats['users_one_day']}</code>
    <i>Oxirgi bir xafta:</i>   <code>{stats['users_one_week']}</code>
    <i>Oxirgi bir oy:</i>        <code>{stats['users_one_month']}</code>
    <i>Oxirgi yarim yil:</i>   <code>{stats['users_half_year']}</code>
    <i>Oxirgi bir yil:</i>        <code>{stats['users_one_year']}</code>
    <u><i>Umumiy:</i></u>              <code>{stats['users_all_time']}</code>\n
    <b><i>Anketalar:</i></b>\n
    <i>Oxirgi bir kun:</i>      <code>{stats['forms_one_day']}</code>
    <i>Oxirgi bir xafta:</i>   <code>{stats['forms_one_week']}</code>
    <i>Oxirgi bir oy:</i>        <code>{stats['forms_one_month']}</code>
    <i>Oxirgi yarim yil:</i>   <code>{stats['forms_half_year']}</code>
    <i>Oxirgi bir yil:</i>        <code>{stats['forms_one_year']}</code>
    <u><i>Umumiy:</i></u>              <code>{stats['forms_all_time']}</code>\n
    <b><i>Yangilangan Anketalar:</i></b>\n
    <i>Oxirgi bir kun:</i>      <code>{stats['updated_forms_one_day']}</code>
    <i>Oxirgi bir xafta:</i>   <code>{stats['updated_forms_one_week']}</code>
    <i>Oxirgi bir oy:</i>        <code>{stats['updated_forms_one_month']}</code>
    <i>Oxirgi yarim yil:</i>   <code>{stats['updated_forms_half_year']}</code>
    <i>Oxirgi bir yil:</i>        <code>{stats['updated_forms_one_year']}</code>
    <u><i>Umumiy:</i></u>              <code>{stats['updated_forms_all_time']}</code>\n
    """,
                                chat_id=call.message.chat.id, message_id=state_data["function_message_id"],
                                reply_markup=menu_navigation_keyboard)


@admin_router.callback_query(MainCallbackFactory.filter(F.action == "back"), AdminStates.stats)
async def go_back_from_stats(call: CallbackQuery, bot: Bot, state: FSMContext):
    """  Return to admin functions from state "AdminStates:stats"  """
    await call.answer(cache_time=1)
    await state.set_state(AdminStates.admin_mode)
    state_data = await state.get_data()
    await bot.edit_message_text(text="Mavjud funktsiyalar:", chat_id=call.message.chat.id,
                                message_id=state_data["function_message_id"], reply_markup=admin_functions)

# ================================================Function Statistics================================================= #

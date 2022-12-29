from re import findall as regexp_findall
from contextlib import suppress
from datetime import datetime
from asyncio import sleep as asleep

from aiogram import Router, Bot, F, html
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.config import Config
from tgbot.database.functions.functions import get_profession, get_direction, get_users_form_id, add_form, update_form
from tgbot.keyboards.inline import home_keyboard, menu_navigation_keyboard, raw_true_false_keyboard, \
    genders_keyboard, make_professions_keyboard, nations_keyboard, university_grades_keyboard, confirming_keyboard, \
    make_directions_keyboard, marital_status_keyboard, level_keyboard, working_style_keyboard, \
    salary_keyboard, sending_keyboard
from tgbot.keyboards.reply import make_menu_keyboard
from tgbot.misc.states import FormFillingStates
from tgbot.misc.cbdata import MainCallbackFactory

flags = {"throttling_key": "default"}
form_filling_router = Router()

# --------------------------------------------------Form Filling------------------------------------------------------ #


@form_filling_router.callback_query(MainCallbackFactory.filter(F.action == "home"), FormFillingStates())
async def cancel_form(call: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession, config: Config):
    """  Cancel form filling and back to home menu  """
    await call.answer(cache_time=2)  # It's a simple anti-flood
    current_state = await state.get_state()
    state_data = await state.get_data()
    menu_keyboard = await make_menu_keyboard(session, call.from_user.id, config)
    if current_state != "FormFillingStates:q1_name" and current_state != "FormFillingStates:ready_form":
        await bot.delete_message(call.message.chat.id, state_data["question_message_id"])

    await bot.delete_message(call.message.chat.id, state_data["form_message_id"])
    with suppress(KeyError, TelegramBadRequest, TelegramBadRequest):
        await bot.delete_message(call.message.chat.id, state_data["form_photo_message_id"])
    await bot.delete_message(call.message.chat.id, state_data["anketa_text_message_id"])
    await call.message.answer("<b>Anketa to'ldirish bekor qilindi!</b>",
                              reply_markup=menu_keyboard)
    await state.clear()
    

@form_filling_router.message(F.text == "\U0001f4dd Anketa to'ldirish", flags=flags)
@form_filling_router.message(F.text == "\U0001f4dd Anketamni yangilash", flags=flags)
async def ask_q1(message: Message, state: FSMContext):
    """  Start form filling and ask for user's name  """
    await state.set_state(FormFillingStates.q1_name)
    anketa_text_message = await message.answer("Anketa:", reply_markup=ReplyKeyboardRemove())
    form_message = await message.answer("<b>F.I.Sh.</b>\nMisol: <i>Ikramov Akrom Murodjon o'g'li</i>)",
                                        reply_markup=home_keyboard)
    await state.update_data(form_message_id=form_message.message_id,
                            anketa_text_message_id=anketa_text_message.message_id)


@form_filling_router.message(F.text.regexp(r"^[A-Za-z\s']{4,64}$"), FormFillingStates.q1_name, flags=flags)
async def ask_q2(message: Message, state: FSMContext, bot: Bot):
    """  Ask for the user's date of birth  """
    await state.set_state(FormFillingStates.q2_birth_date)
    full_name = message.text.title()
    form_text = f"<b>F.I.Sh.:</b> {full_name}\n"
    state_data = await state.get_data()
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id,
                                message_id=state_data["form_message_id"])
    question_message = await message.answer("<b>Tug'ilgan sanangizni kiriting.</b>\n(11.09.1988)",
                                            reply_markup=menu_navigation_keyboard)
    await message.delete()
    await state.update_data(full_name=full_name, form_text=form_text, question_message_id=question_message.message_id)


@form_filling_router.message(
    F.text.regexp(r"(?:0?[1-9]|[12][0-9]|3[01])[.](?:0?[1-9]|1[012])[.](?:19[6-9]\d|20[01][0-9])$"),
    FormFillingStates.q2_birth_date, flags=flags)
async def ask_q3(message: Message, state: FSMContext, bot: Bot):
    """  Ask for the user's gender  """
    await state.set_state(FormFillingStates.q3_gender)
    state_data = await state.get_data()
    date_list = message.text.split(".")
    birth_date = f"{date_list[2]}-{date_list[1]}-{date_list[0]}"
    form_text = state_data["form_text"] + f"<b>Tug'ilgan sana:</b> {message.text}\n"
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Jinsingiz:</b>", chat_id=message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=genders_keyboard)
    await message.delete()
    await state.update_data(birth_date=birth_date, form_text=form_text)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data), FormFillingStates.q3_gender)
async def ask_q4(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory):
    """  Ask for the user's phone number  """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q4_phonenum)
    state_data = await state.get_data()
    gender_uz = "Erkak" if callback_data.data == "MALE" else "Ayol"  # Gender in Uzbek language
    form_text = state_data["form_text"] + f"<b>Jins:</b> {gender_uz}\n"
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(
        text="<b>Siz bilan bog'lanishimiz mumkin bo'lgan telefon raqamni kiriting.</b>\n(+998735455555)",
        chat_id=call.message.chat.id, message_id=state_data["question_message_id"],
        reply_markup=menu_navigation_keyboard)
    await state.update_data(gender=callback_data.data, form_text=form_text)


@form_filling_router.message(F.text.regexp(r"\+998[0-9]{9}$"), FormFillingStates.q4_phonenum, flags=flags)
@form_filling_router.message(F.contentype == "contact", FormFillingStates.q4_phonenum, flags=flags)
async def confirm_q3(message: Message, state: FSMContext, bot: Bot):
    """  Ask the user to confirm that the phone number is correct  """
    await message.delete()
    phonenum = message.text
    state_data = await state.get_data()
    await bot.edit_message_text(text=f"<b>Raqamni to'g'ri terdingizmi?</b>\n{phonenum}", chat_id=message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=raw_true_false_keyboard)
    await state.update_data(phonenum=phonenum)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data == 0), FormFillingStates.q4_phonenum)
async def ask_q4_again(call: CallbackQuery, bot: Bot, state: FSMContext):
    """  Ask for user's phone number again if last was incorrect  """
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    await bot.edit_message_text(
        text="<b>Siz bilan bog'lanishimiz mumkin bo'lgan telefon raqamni kiriting.</b>\n(+998735455555)",
        chat_id=call.message.chat.id, message_id=state_data["question_message_id"],
        reply_markup=menu_navigation_keyboard)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data == 1), FormFillingStates.q4_phonenum)
async def ask_q5(call: CallbackQuery, state: FSMContext, bot: Bot, session: AsyncSession, config: Config):
    """  Ask user which profession he is interested in  """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q5_professions)
    state_data = await state.get_data()
    keyboard = await make_professions_keyboard(session)
    if not keyboard:
        menu_keyboard = await make_menu_keyboard(session, call.from_user.id, config)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["question_message_id"])
        await call.message.answer(text="<u><b>Xozircha ishga olish uchun mavjud sohalar yo'q!</b></u>",
                                  reply_markup=menu_keyboard)
        await state.clear()
        return
    form_text = state_data["form_text"] + f"<b>Telefon raqam:</b> {state_data['phonenum']}\n"
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id,
                                message_id=state_data["form_message_id"])
    await call.message.edit_text("<b>Sizni qiziqtirgan sohalarni tanlang:</b>",
                                 reply_markup=keyboard)
    await state.update_data(form_text=form_text)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.action == "select"), FormFillingStates.q5_professions)
async def confirm_selected_professions(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession,
                                       callback_data: MainCallbackFactory):
    """  Wait for selecting or confirming selected professions  """
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    try:
        checked_professions = state_data["checked_professions"]
    except KeyError:
        checked_professions = []
    selected_profession_id = callback_data.data
    if selected_profession_id in checked_professions:
        keyboard = await make_professions_keyboard(session, checked_professions=checked_professions, is_check=False,
                                                   last_selected_profession=selected_profession_id)
        checked_professions.remove(selected_profession_id)
    else:
        checked_professions.append(selected_profession_id)
        keyboard = await make_professions_keyboard(session, checked_professions=checked_professions,
                                                   last_selected_profession=selected_profession_id)
    await bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=state_data["question_message_id"],
                                        reply_markup=keyboard)
    await state.update_data(checked_professions=checked_professions)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.action == "confirm"), FormFillingStates.q5_professions)
async def ask_q6(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession):
    """  Ask for the user's living address   """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q6_address)
    state_data = await state.get_data()
    profession_titles = []
    if not state_data["checked_professions"]:
        form_text = state_data["form_text"] + "<b>Qiziqtirgan sohalar:</b> Mavjud emas!\n"
    else:
        for profession_id in state_data["checked_professions"]:
            # Getting profession title from database and adding it to the list above
            profession_title = (await get_profession(session, profession_id))[0]
            profession_titles.append(profession_title.capitalize())
        form_text = state_data["form_text"] + f"<b>Qiziqtirgan sohalar:</b> {', '.join(profession_titles)}\n"
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(
        text="<b>Doimiy yashash manzilingizni kiriting.</b>\nMusol: <i>Qoʻqon shahri, Turkiston koʻchasi, 28-A uy</i>)",
        chat_id=call.message.chat.id, message_id=state_data["question_message_id"],
        reply_markup=menu_navigation_keyboard
    )
    await state.update_data(form_text=form_text, profession_titles=profession_titles)


@form_filling_router.message(F.text.regexp(r"^[A-Za-z\d\s'ʻ-/.,]{3,150}$"), FormFillingStates.q6_address, flags=flags)
async def ask_q7(message: Message, state: FSMContext, bot: Bot):
    """  Ask for the user's nation  """
    await state.set_state(FormFillingStates.q7_nation)
    state_data = await state.get_data()
    address = html.quote(message.text)
    form_text = state_data["form_text"] + f"<b>Yashash manzil:</b> {address}\n"
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Millatingiz:</b>", chat_id=message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=nations_keyboard)
    await message.delete()
    await state.update_data(form_text=form_text, address=address)


@form_filling_router.message(FormFillingStates.q6_address)
async def incorrect_address_alert(message: Message, bot: Bot):
    """  Send an alert message about incorrect answer  """
    await message.delete()
    alert_message = await message.answer("<b>Yashah manzilingiz quyidagilarga mos shakilda bo'lishi kerak:</b>\n"
                                         "1. Lotincha xarflar yoki raqamlardan iborat bo'lishi\n"
                                         "2. 3ta belgidan ko'p bo'lishi va 150 belgidan kam bo'lishi\n"
                                         "3. Mumkin bo'lgan simvollar:  <code>. , / - '</code>")
    await asleep(10)
    await bot.delete_message(chat_id=message.chat.id, message_id=alert_message.message_id)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data), FormFillingStates.q7_nation)
async def ask_q8(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory):
    """  Ask for the user's university grade   """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q8_university_grade)
    state_data = await state.get_data()
    nation = "O'zbek"
    if callback_data.data == "RUSSIAN":
        nation = "Rus"
    elif callback_data.data == "OTHER":
        nation = "Boshqa"
    form_text = state_data["form_text"] + f"<b>Millat:</b> {nation}\n"
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(
        text="<b>Nechanchi kurs talabasisiz?</b>",
        chat_id=call.message.chat.id, message_id=state_data["question_message_id"],
        reply_markup=university_grades_keyboard
    )
    await state.update_data(form_text=form_text, nation=callback_data.data)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data), FormFillingStates.q8_university_grade)
async def ask_q9(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession,
                 callback_data: MainCallbackFactory):
    """  Ask for the user's university direction  """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q9_university_direction)
    state_data = await state.get_data()
    university_grade_uz = "Magistr" if callback_data.data == 5 else callback_data.data
    form_text = state_data["form_text"] + f"<b>Kurs:</b> {university_grade_uz}\n"
    keyboard = await make_directions_keyboard(session)
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(
        text="<b>Ta'lim yo'nalishingiz:</b>",
        chat_id=call.message.chat.id, message_id=state_data["question_message_id"],
        reply_markup=keyboard
    )
    await state.update_data(form_text=form_text, university_grade=callback_data.data)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data), FormFillingStates.q9_university_direction)
async def ask_q10(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession,
                  callback_data: MainCallbackFactory):
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q10_working_company)
    state_data = await state.get_data()
    direction_title = (await get_direction(session, callback_data.data))[0]
    form_text = state_data["form_text"] + f"<b>Ta'lim yo'nalishi: </b> {direction_title.capitalize()}\n"
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id,
                                message_id=state_data["form_message_id"])
    await state.update_data(direction_id=callback_data.data, form_text=form_text)
    await call.message.edit_text("<b>Hozirda ish bilan bandmisiz?</b>",
                                 reply_markup=confirming_keyboard)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data == 1), FormFillingStates.q10_working_company)
async def ask_company_name(call: CallbackQuery, bot: Bot, state: FSMContext):
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.company_name)
    state_data = await state.get_data()
    form_text = state_data["form_text"] + f"<b>Ish o'rni: </b>"
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id,
                                message_id=state_data["form_message_id"])
    question_message = await call.message.edit_text(
        "<b>Ishlayotgan korxonangizning nomi nima?</b>\n(Kokand University)",
        reply_markup=menu_navigation_keyboard)
    await state.update_data(question_message_id=question_message.message_id, form_text=form_text)


@form_filling_router.message(F.text.regexp(r"^[A-Za-z\d\s'-/.]{2,150}$"), FormFillingStates.company_name, flags=flags)
async def ask_company_position(message: Message, bot: Bot, state: FSMContext):
    await state.set_state(FormFillingStates.company_position)
    state_data = await state.get_data()
    company_name = message.text.strip()
    form_text = state_data["form_text"] + f"\n    <b>Nomi:</b> {company_name}\n"
    await message.delete()
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Qaysi lavozimda ishlaysiz?</b>\n(Buxgalter)", chat_id=message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=menu_navigation_keyboard)
    await state.update_data(form_text=form_text, company_name=company_name)


@form_filling_router.message(F.text.regexp(r"^[A-Za-z\d\s'-/.]{2,150}$"), FormFillingStates.company_position,
                             flags=flags)
async def ask_q11(message: Message, bot: Bot, state: FSMContext):
    await state.set_state(FormFillingStates.q11_marital_status)
    state_data = await state.get_data()
    company_position = message.text.strip()
    form_text = state_data["form_text"] + f"    <b>Lavozimi:</b> {company_position}\n"
    await message.delete()
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Oilaviy ahvolingiz:</b>", reply_markup=marital_status_keyboard,
                                chat_id=message.chat.id, message_id=state_data["question_message_id"])
    await state.update_data(form_text=form_text, company=[state_data["company_name"], company_position])


@form_filling_router.message(FormFillingStates.company_name)
@form_filling_router.message(FormFillingStates.company_position)
async def incorrect_company_data_alert(message: Message, bot: Bot):
    """  Send an alert message about incorrect answer  """
    await message.delete()
    alert_message = await message.answer("<b>Matn quyidagilarga mos shakilda bo'lishi kerak:</b>\n"
                                         "1. Lotincha xarflar yoki raqamlardan iborat bo'lishi\n"
                                         "2. 1ta belgidan ko'p bo'lishi va 150 belgidan kam bo'lishi\n"
                                         "3. Mumkin bo'lgan simvollar:  <code>. / - '</code>")
    await asleep(10)
    await bot.delete_message(chat_id=message.chat.id, message_id=alert_message.message_id)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data == 0), FormFillingStates.q10_working_company)
async def ask_q11_callback(call: CallbackQuery, bot: Bot, state: FSMContext):
    """  Ask marital status if didn't add working company  """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q11_marital_status)
    state_data = await state.get_data()
    form_text = state_data["form_text"] + "<b>Ish o'rni: </b>\U00002796\n"  # Emoji 'heavy_minus_sign'
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Oilaviy ahvolingiz:</b>", reply_markup=marital_status_keyboard,
                                chat_id=call.message.chat.id, message_id=state_data["question_message_id"])
    await state.update_data(company=None, form_text=form_text)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data == 1), FormFillingStates.q11_marital_status)
@form_filling_router.callback_query(MainCallbackFactory.filter(F.data == 0), FormFillingStates.q11_marital_status)
async def ask_q12(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory):
    """  Ask for user's driver license  """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q12_driver_license)
    state_data = await state.get_data()
    marital_status_uz = "Turmush qurgan" if callback_data.data else "Turmush qurmagan"
    form_text = state_data["form_text"] + f"<b>Oilaviy ahvol:</b> {marital_status_uz}\n"
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Haydovchilik guvohnomangiz bormi?</b>",
                                chat_id=call.message.chat.id, message_id=state_data["question_message_id"],
                                reply_markup=confirming_keyboard)
    # We need an empty list 'languages' in next handlers
    await state.update_data(form_text=form_text, marital_status=callback_data.data, languages=[])


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data == 1), FormFillingStates.q12_driver_license)
@form_filling_router.callback_query(MainCallbackFactory.filter(F.data == 0), FormFillingStates.q12_driver_license)
async def ask_q13(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory):
    """  Ask for user how well he speaks russian  """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q13_ru_lang)
    state_data = await state.get_data()
    driver_license_uz = "Bor" if callback_data.data else "Yo'q"
    form_text = state_data["form_text"] + f"<b>Haydovchilik guvohnomasi:</b> {driver_license_uz}\n" \
                                          f"<b>Tillar:</b>\n"
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Rus tilida suhbatlashish darajangiz:</b>", chat_id=call.message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=level_keyboard)
    await state.update_data(form_text=form_text, driver_license=callback_data.data)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data.in_([0, 25, 50, 75, 100])),
                                    FormFillingStates.q13_ru_lang)
async def ask_q14(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory):
    """  Ask for user how well he speaks english  """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q14_eng_lang)
    state_data = await state.get_data()
    form_text = state_data["form_text"] + f"Rus tili: {callback_data.data}%\n"
    languages = state_data["languages"]
    languages.append({"name": "rus", "level": callback_data.data})
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Ingiliz tilida suhbatlashish darajangiz:</b>", chat_id=call.message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=level_keyboard)
    await state.update_data(form_text=form_text, languages=languages)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data.in_([0, 25, 50, 75, 100])),
                                    FormFillingStates.q14_eng_lang)
async def ask_q15(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory):
    """  Ask for user which other languages he speaks  """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q15_other_lang)
    state_data = await state.get_data()
    form_text = state_data["form_text"] + f"Ingiliz tili: {callback_data.data}%\n"
    languages = state_data["languages"]
    languages.append({"name": "ingiliz", "level": callback_data.data})
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Yana boshqa bir tilni bilasizmi?</b>", chat_id=call.message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=confirming_keyboard)
    await state.update_data(form_text=form_text, languages=languages)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data == 1), FormFillingStates.q15_other_lang)
async def ask_lang_name(call: CallbackQuery, state: FSMContext):
    """  Ask for the name of the language that user speaks or ask for how well he knows word app  """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.lang_name)
    question_message = await call.message.edit_text(
        "<b>Tilning nomini kiriting</b>\n(Arab)",
        reply_markup=menu_navigation_keyboard)
    await state.update_data(question_message_id=question_message.message_id)


@form_filling_router.message(F.text.regexp(r"^[^\s\d\n]{2,32}$"), FormFillingStates.lang_name, flags=flags)
async def ask_lang_level(message: Message, bot: Bot, state: FSMContext):
    """  Ask user how well he speaks that language  """
    await state.set_state(FormFillingStates.lang_level)
    state_data = await state.get_data()
    form_text = state_data["form_text"] + f"{message.text.capitalize()}: "
    await message.delete()
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Bu tilda qay darajada suhbatlasha olasiz?</b>", chat_id=message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=level_keyboard)
    await state.update_data(form_text=form_text, lang_name=message.text.lower())


@form_filling_router.message(FormFillingStates.lang_name)
async def incorrect_lang_name_alert(message: Message, bot: Bot):
    """  Send an alert message about incorrect answer  """
    await message.delete()
    alert_message = await message.answer("<b>Lotincha harflardan foydalangan holda faqatgina tilning nomini kiriting, "
                                         "32ta harfdan oshmasin!</b>\n"
                                         "Misol: <code>Xitoy</code>")
    await asleep(10)
    await bot.delete_message(chat_id=message.chat.id, message_id=alert_message.message_id)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data.in_([0, 25, 50, 75, 100])),
                                    FormFillingStates.lang_level)
async def ask_again_q16(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory):
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q15_other_lang)
    state_data = await state.get_data()
    languages = state_data["languages"]
    languages.append({"name": state_data["lang_name"], "level": callback_data.data})
    form_text = state_data["form_text"] + f"{callback_data.data}%\n"
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await state.update_data(form_text=form_text, languages=languages)
    if len(languages) >= 7:
        await state.set_state(FormFillingStates.q16_word_app)
        form_text = form_text + f"<b>Dasturlar:</b>\n"
        await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id,
                                    message_id=state_data["form_message_id"])
        await bot.edit_message_text(text="<b>Word dasturidan foydalana olish darajangiz:</b>",
                                    chat_id=call.message.chat.id, message_id=state_data["question_message_id"],
                                    reply_markup=level_keyboard)
        await state.update_data(applications=[], form_text=form_text)
        return
    await bot.edit_message_text(text="<b>Yana boshqa bir tilni bilasizmi?</b>", chat_id=call.message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=confirming_keyboard)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data == 0), FormFillingStates.q15_other_lang)
async def ask_q16(call: CallbackQuery, bot: Bot, state: FSMContext):
    """  Ask user how well he knows word app  """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q16_word_app)
    state_data = await state.get_data()
    form_text = state_data["form_text"] + f"<b>Dasturlar:</b>\n"
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id,
                                message_id=state_data["form_message_id"])
    await call.message.edit_text("<b>Word dasturidan foydalana olish darajangiz:</b>",
                                 reply_markup=level_keyboard)
    await state.update_data(applications=[], form_text=form_text)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data.in_([0, 25, 50, 75, 100])),
                                    FormFillingStates.q16_word_app)
async def ask_q17(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory):
    """  Ask for user how well he knows excel app  """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q17_excel_app)
    state_data = await state.get_data()
    form_text = state_data["form_text"] + f"Word: {callback_data.data}%\n"
    applications = state_data["applications"]
    applications.append({"name": "word", "level": callback_data.data})
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Excel dasturidan foydalana olish darajangiz:</b>", reply_markup=level_keyboard,
                                chat_id=call.message.chat.id, message_id=state_data["question_message_id"])
    await state.update_data(form_text=form_text, applications=applications)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data.in_([0, 25, 50, 75, 100])),
                                    FormFillingStates.q17_excel_app)
async def ask_q18(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory):
    """  Ask for user how well he knows 1C app  """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q18_1c_app)
    state_data = await state.get_data()
    form_text = state_data["form_text"] + f"Excel: {callback_data.data}%\n"
    applications = state_data["applications"]
    applications.append({"name": "excel", "level": callback_data.data})
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>1C dasturidan foydalana olish darajangiz:</b>", reply_markup=level_keyboard,
                                chat_id=call.message.chat.id, message_id=state_data["question_message_id"])
    await state.update_data(form_text=form_text, applications=applications)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data.in_([0, 25, 50, 75, 100])),
                                    FormFillingStates.q18_1c_app)
async def ask_q19(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory):
    """  Ask user for which other applications he knows  """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q19_other_app)
    state_data = await state.get_data()
    form_text = state_data["form_text"] + f"1C: {callback_data.data}%\n"
    applications = state_data["applications"]
    applications.append({"name": "1c", "level": callback_data.data})
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Yana boshqa bir dasturni bilasizmi?</b>", chat_id=call.message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=confirming_keyboard)
    await state.update_data(form_text=form_text, applications=applications)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data == 1), FormFillingStates.q19_other_app)
async def ask_app_name(call: CallbackQuery, state: FSMContext):
    """  Ask for the name of the application that user knows  """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.app_name)
    question_message = await call.message.edit_text(
        "<b>Dasturning nomini kiriting</b>\n(Adobe Photoshop)",
        reply_markup=menu_navigation_keyboard)
    await state.update_data(question_message_id=question_message.message_id)


@form_filling_router.message(F.text.regexp(r"^.{2,32}$"), FormFillingStates.app_name, flags=flags)
async def ask_app_level(message: Message, bot: Bot, state: FSMContext):
    """  Ask user how well he knows that application """
    await state.set_state(FormFillingStates.app_level)
    state_data = await state.get_data()
    # Application name which user sent
    form_text = state_data["form_text"] + f"{message.text.capitalize()}: "
    await message.delete()
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(text="<b>Bu dasturni qay darajada bilasiz?</b>", chat_id=message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=level_keyboard)
    await state.update_data(form_text=form_text, app_name=message.text.lower())


@form_filling_router.message(FormFillingStates.app_name)
async def incorrect_app_name_alert(message: Message, bot: Bot):
    """  Send an alert message about incorrect answer  """
    await message.delete()
    alert_message = await message.answer("<b>Lotincha harflar, raqam va belgilardan foydalangan holda faqatgina "
                                         "dasturning nomini kiriting, 32ta harfdan oshmasin!</b>\n"
                                         "Misol: <code>Adobe Photoshop</code>")
    await asleep(10)
    await bot.delete_message(chat_id=message.chat.id, message_id=alert_message.message_id)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data.in_([0, 25, 50, 75, 100])),
                                    FormFillingStates.app_level)
async def ask_again_q19(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory):
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q19_other_app)
    state_data = await state.get_data()
    applications = state_data["applications"]
    applications.append({"name": state_data["app_name"], "level": callback_data.data})
    form_text = state_data["form_text"] + f"{callback_data.data}%\n"
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await state.update_data(form_text=form_text, applications=applications)
    if len(applications) >= 10:
        await state.set_state(FormFillingStates.q20_working_style)
        await bot.edit_message_text(text="<b>Qanday ishlashni afzal ko'rasiz?</b>", chat_id=call.message.chat.id,
                                    message_id=state_data["question_message_id"], reply_markup=working_style_keyboard)
        return
    await bot.edit_message_text(text="<b>Yana boshqa bir dasturni bilasizmi?</b>", chat_id=call.message.chat.id,
                                message_id=state_data["question_message_id"], reply_markup=confirming_keyboard)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data == 0), FormFillingStates.q19_other_app)
async def ask_q20(call: CallbackQuery, state: FSMContext):
    """  Ask the user for which working style he prefers  """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q20_working_style)
    await call.message.edit_text("<b>Qanday ishlashni afzal ko'rasiz?</b>", reply_markup=working_style_keyboard)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data), FormFillingStates.q20_working_style)
async def ask_q21(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory):
    """  Ask user for how many salary suits him """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q21_salary)
    state_data = await state.get_data()
    working_style_uz = "Jamoada" if callback_data.data == "COLLECTIVE" else "Individual"
    form_text = state_data["form_text"] + f"<b>Ishlash uslubi:</b> {working_style_uz}\n"
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(
        text="<b>Qancha oylik maoshiga ishlagan bo'lar edingiz?</b>", chat_id=call.message.chat.id,
        message_id=state_data["question_message_id"], reply_markup=salary_keyboard
    )
    await state.update_data(form_text=form_text, working_style=callback_data.data)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.data), FormFillingStates.q21_salary)
async def ask_q22(call: CallbackQuery, bot: Bot, state: FSMContext, callback_data: MainCallbackFactory):
    """  Ask user for a positive self-assessment """
    await call.answer(cache_time=1)
    await state.set_state(FormFillingStates.q22_positive_assessment)
    state_data = await state.get_data()
    salary_uz = "1 - 2 milion so'm"
    if callback_data.data == 2:
        salary_uz = "3 - 4 million so'm"
    elif callback_data.data == 3:
        salary_uz = "5 million so'm va undan yuqori"
    form_text = state_data["form_text"] + f"<b>Oylik maoshi:</b> {salary_uz}\n"
    await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(
        text="<b>O'zingizga qanday ijobiy ta'rif bera olasiz?</b>", chat_id=call.message.chat.id,
        message_id=state_data["question_message_id"], reply_markup=menu_navigation_keyboard
    )
    await state.update_data(form_text=form_text, salary=callback_data.data)


@form_filling_router.message(F.text.func(lambda text: len(text) <= 250), FormFillingStates.q22_positive_assessment,
                             flags=flags)
async def ask_q23(message: Message, bot: Bot, state: FSMContext):
    """  Ask user for a negative self-assessment   """
    await state.set_state(FormFillingStates.q23_negative_assessment)
    state_data = await state.get_data()
    positive_assessment = html.quote(message.text.strip())
    form_text = state_data["form_text"] + f"<b>Ijobiy ta'rif:</b> {positive_assessment}\n"
    await message.delete()
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(
        text="<b>O'zingizga qanday salbiy ta'rif bera olasiz?</b>", chat_id=message.chat.id,
        message_id=state_data["question_message_id"], reply_markup=menu_navigation_keyboard
    )
    await state.update_data(form_text=form_text, positive_assessment=positive_assessment)


@form_filling_router.message(F.text.func(lambda text: len(text) <= 250), FormFillingStates.q23_negative_assessment,
                             flags=flags)
async def ask_q24(message: Message, bot: Bot, state: FSMContext):
    """  Ask for user to send his photo  """
    await state.set_state(FormFillingStates.q24_photo)
    state_data = await state.get_data()
    negative_assessment = html.quote(message.text.strip())
    form_text = state_data["form_text"] + f"<b>Salbiy ta'rif:</b> {negative_assessment}\n"
    await message.delete()
    await bot.edit_message_text(text=form_text, chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.edit_message_text(
        text="<b>O'zingizni rasmingizni jo'nating.</b>\n(Fayl ko'rinishida jo'natmang. Selfi ham bo'laveradi)",
        chat_id=message.chat.id, message_id=state_data["question_message_id"], reply_markup=menu_navigation_keyboard
    )
    await state.update_data(form_text=form_text, negative_assessment=negative_assessment)


@form_filling_router.message(FormFillingStates.q22_positive_assessment)
@form_filling_router.message(FormFillingStates.q23_negative_assessment)
async def incorrect_assessment_alert(message: Message, bot: Bot):
    """  Send an alert message about incorrect answer  """
    await message.delete()
    alert_message = await message.answer("<b>Ta'rifni faqat matn bilan bayon qiling, "
                                         "hajmi 250ta belgidan oshmasligi kerak!</b>")
    await asleep(10)
    await bot.delete_message(chat_id=message.chat.id, message_id=alert_message.message_id)


@form_filling_router.message(F.content_type == "photo", FormFillingStates.q24_photo, flags=flags)
async def confirming_form(message: Message, bot: Bot, state: FSMContext):
    await state.set_state(FormFillingStates.ready_form)
    state_data = await state.get_data()
    photo_id = message.photo[0].file_id
    form_text = state_data["form_text"]
    await message.delete()
    await bot.delete_message(chat_id=message.chat.id, message_id=state_data["question_message_id"])
    await bot.delete_message(chat_id=message.chat.id, message_id=state_data["form_message_id"])
    await bot.delete_message(chat_id=message.chat.id, message_id=state_data["anketa_text_message_id"])
    anketa_text_message = await message.answer("<b>Anketangiz tayyor!</b>")
    form_photo_message = await message.answer_photo(photo=photo_id)
    form_message = await bot.send_message(text=form_text, chat_id=message.chat.id,
                                          reply_to_message_id=form_photo_message.message_id,
                                          reply_markup=sending_keyboard)
    await state.update_data(photo_id=photo_id, form_message_id=form_message.message_id,
                            form_photo_message_id=form_photo_message.message_id,
                            anketa_text_message_id=anketa_text_message.message_id)


@form_filling_router.message(FormFillingStates.q24_photo)
async def incorrect_photo_alert(message: Message, bot: Bot):
    """  Send an alert message about incorrect answer  """
    await message.delete()
    alert_message = await message.answer("<b>Faqatgina rasm jo'nating, fayl ko'rinishida bo'lmasin!</b>")
    await asleep(10)
    await bot.delete_message(chat_id=message.chat.id, message_id=alert_message.message_id)


@form_filling_router.message(FormFillingStates())
async def other_incorrect_messages_alert(message: Message, bot: Bot):
    """  Send an alert message about incorrect answer  """
    await message.delete()
    alert_message = await message.answer("<b>Noto'g'ri ma'lumot kiritdingiz!</b>\n"
                                         "Iltimos, ma'lumotlarni ko'rsatilgan shakilda kiriting.")
    await asleep(10)
    await bot.delete_message(chat_id=message.chat.id, message_id=alert_message.message_id)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.action == "send"), FormFillingStates.ready_form)
async def send_form(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession, config: Config):
    """  Send the form to the group and admins and create a record in database about this form  """
    await call.answer(cache_time=1)
    state_data = await state.get_data()
    await call.message.edit_reply_markup()
    old_form_id = await get_users_form_id(session, telegram_id=call.from_user.id)
    username = "Mavjud emas!" if call.from_user.username is None else f"@{call.from_user.username}"
    form_text = state_data["form_text"] + f"<b>Telegramdagi ismi:</b> {call.from_user.full_name}\n" \
                                          f"<b>Telegramdagi nomi:</b> {username}\n" \
                                          f"<b>Telegram ID:</b> {call.from_user.id}\n"
    birth_date = datetime.strptime(state_data["birth_date"], '%Y-%m-%d')
    if old_form_id:  # If user already have another form update it
        await update_form(session, form_id=old_form_id, telegram_id=call.from_user.id,
                          full_name=state_data["full_name"], birth_date=birth_date,
                          gender=state_data["gender"], phonenum=state_data["phonenum"], address=state_data["address"],
                          nation=state_data["nation"], university_grade=state_data["university_grade"],
                          direction_id=state_data["direction_id"], marital_status=state_data["marital_status"],
                          driver_license=state_data["driver_license"], working_style=state_data["working_style"],
                          wanted_salary=state_data["salary"], positive_assessment=state_data["positive_assessment"],
                          negative_assessment=state_data["negative_assessment"], photo_id=state_data["photo_id"],
                          checked_professions=state_data["checked_professions"], company=state_data["company"],
                          languages=state_data["languages"], applications=state_data["applications"])
        form_text = form_text + "<code>YANGILANGAN!</code>"
        menu_keyboard = await make_menu_keyboard(session, call.from_user.id, config)
        await call.message.answer(f"<b>Anketangiz muvaffaqiyatli yangilandi va administratorlarga jo'natildi</b>"
                                  f"\U0001F389",
                                  reply_markup=menu_keyboard)
    else:
        await add_form(session, telegram_id=call.from_user.id, full_name=state_data["full_name"],
                       birth_date=birth_date, gender=state_data["gender"],
                       phonenum=state_data["phonenum"], address=state_data["address"], nation=state_data["nation"],
                       university_grade=state_data["university_grade"], direction_id=state_data["direction_id"],
                       marital_status=state_data["marital_status"], driver_license=state_data["driver_license"],
                       working_style=state_data["working_style"], wanted_salary=state_data["salary"],
                       positive_assessment=state_data["positive_assessment"],
                       negative_assessment=state_data["negative_assessment"], photo_id=state_data["photo_id"],
                       checked_professions=state_data["checked_professions"], company=state_data["company"],
                       languages=state_data["languages"], applications=state_data["applications"])
        menu_keyboard = await make_menu_keyboard(session, call.from_user.id, config)
        await call.message.answer(text=f"<b>Anketangiz muvaffaqiyatli shakillandi va administratorlarga jo'natildi</b>"
                                  f"\U0001F389",
                                  reply_markup=menu_keyboard)
    # Sending form to admins and administrator's group
    try:
        photo_message = await bot.send_photo(chat_id=config.tgbot.forms_group, photo=state_data["photo_id"])
        await bot.send_message(chat_id=config.tgbot.forms_group, text=form_text,
                               reply_to_message_id=photo_message.message_id)

    except Exception as error:
        for admin_id in config.tgbot.admins:
            with suppress(TelegramBadRequest):
                await bot.send_message(chat_id=admin_id, text=f"Guruhga anketa jo'natish jarayonida xatolik!\n"
                                                              f"<code>{error}</code>")
                photo_message = await bot.send_photo(chat_id=admin_id, photo=state_data["photo_id"])
                await bot.send_message(chat_id=admin_id, text=form_text, reply_to_message_id=photo_message.message_id)
    await state.clear()


# --------------------------------------------------Back Buttons------------------------------------------------------ #

async def edit_form_question(callback_query: CallbackQuery, bot: Bot, state: FSMContext, text_to_cut: str,
                             question_text: str, reply_markup: InlineKeyboardMarkup):
    """
    Edit current question and cut the given text from form text.
    Use this function when handling back buttons in form filling
    """
    state_data = await state.get_data()
    form_text = state_data["form_text"]
    last_answer_index = form_text.find(text_to_cut)
    form_text = form_text[:last_answer_index]  # Form text where deleted the answer to last question
    await bot.edit_message_text(text=question_text, chat_id=callback_query.message.chat.id, 
                                message_id=state_data["question_message_id"], reply_markup=reply_markup)
    await bot.edit_message_text(text=form_text, chat_id=callback_query.message.chat.id,
                                message_id=state_data["form_message_id"])
    await state.update_data(form_text=form_text)


@form_filling_router.callback_query(MainCallbackFactory.filter(F.action == "back"), FormFillingStates())
async def form_filling_back_buttons(call: CallbackQuery, bot: Bot, state: FSMContext, session: AsyncSession):
    await call.answer(cache_time=1)
    current_state = await state.get_state()
    state_data = await state.get_data()

    if current_state == "FormFillingStates:q2_birth_date":
        await state.set_state(FormFillingStates.q1_name)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=state_data["form_message_id"])
        form_message = await call.message.edit_text(
            "<b>Ism va familiyangizni to'liq kiriting.</b>\n(Ikramov Akrom)",
            reply_markup=home_keyboard)
        await state.update_data(form_message_id=form_message.message_id)

    elif current_state == "FormFillingStates:q3_gender":
        await state.set_state(FormFillingStates.q2_birth_date)
        await edit_form_question(call, bot, state, text_to_cut="<b>Tug'ilgan sana:</b>",
                                 question_text="<b>Tug'ilgan sanangizni kiriting.</b>\n(24.03.1998)",
                                 reply_markup=menu_navigation_keyboard)

    elif current_state == "FormFillingStates:q4_phonenum":
        await state.set_state(FormFillingStates.q3_gender)
        await edit_form_question(call, bot, state, text_to_cut="<b>Jins:</b>",  question_text="<b>Jinsingiz:</b>",
                                 reply_markup=genders_keyboard)

    elif current_state == "FormFillingStates:q5_professions":
        await state.set_state(FormFillingStates.q4_phonenum)
        await edit_form_question(
            call, bot, state, text_to_cut="<b>Telefon raqam:</b>", reply_markup=menu_navigation_keyboard,
            question_text="<b>Siz bilan bog'lanishimiz mumkin bo'lgan telefon raqamni kiriting.</b>\n(+998333360006)")

    elif current_state == "FormFillingStates:q6_address":
        await state.set_state(FormFillingStates.q5_professions)
        keyboard = await make_professions_keyboard(session)
        await edit_form_question(
            call, bot, state, text_to_cut="<b>Qiziqtirgan sohalar:</b>", question_text="<b>Qiziqtirgan sohalar:</b>",
            reply_markup=keyboard)
        await state.update_data(checked_professions=[])

    elif current_state == "FormFillingStates:q7_nation":
        await state.set_state(FormFillingStates.q6_address)
        await edit_form_question(
            call, bot, state, text_to_cut="<b>Yashash manzil:</b>",
            question_text="<b>Doyimiy yashash manzilingizni kiriting.</b>\n(Qoʻqon shahri, Turkiston koʻchasi, 28-A uy)",
            reply_markup=menu_navigation_keyboard)

    elif current_state == "FormFillingStates:q8_university_grade":
        await state.set_state(FormFillingStates.q7_nation)
        await edit_form_question(
            call, bot, state, text_to_cut="<b>Millat:</b>", question_text="<b>Millatingiz:</b>",
            reply_markup=nations_keyboard)

    elif current_state == "FormFillingStates:q9_university_direction":
        await state.set_state(FormFillingStates.q8_university_grade)
        await edit_form_question(
            call, bot, state, text_to_cut="<b>Kurs:</b>", question_text="<b>Nechanchi kurs talabasisiz?</b>",
            reply_markup=university_grades_keyboard)

    elif current_state == "FormFillingStates:q10_working_company":
        await state.set_state(FormFillingStates.q9_university_direction)
        keyboard = await make_directions_keyboard(session)
        await edit_form_question(
            call, bot, state, text_to_cut="<b>Ta'lim yo'nalishi: </b>", question_text="<b>Ta'lim yo'nalishingiz:</b>",
            reply_markup=keyboard)

    elif current_state in ["FormFillingStates:company_name", "FormFillingStates:company_position",
                           "FormFillingStates:q11_marital_status"]:
        await state.set_state(FormFillingStates.q10_working_company)
        await edit_form_question(
            call, bot, state, text_to_cut="<b>Ish o'rni: </b>", question_text="<b>Hozirda ish bilan bandmisiz?</b>",
            reply_markup=confirming_keyboard)

    elif current_state == "FormFillingStates:q12_driver_license":
        await state.set_state(FormFillingStates.q11_marital_status)
        await edit_form_question(
            call, bot, state, text_to_cut="<b>Oilaviy ahvol:</b>", question_text="<b>Oilaviy ahvolingiz:</b>",
            reply_markup=marital_status_keyboard)

    elif current_state == "FormFillingStates:q13_ru_lang":
        await state.set_state(FormFillingStates.q12_driver_license)
        await edit_form_question(
            call, bot, state, text_to_cut="<b>Haydovchilik guvohnomasi:</b>",
            question_text="<b>Haydovchilik guvohnomangiz bormi?</b>",
            reply_markup=confirming_keyboard)

    elif current_state == "FormFillingStates:q14_eng_lang":
        await state.set_state(FormFillingStates.q13_ru_lang)
        await edit_form_question(
            call, bot, state, text_to_cut="Rus tili:",
            question_text="<b>Rus tilida suhbatlashish darajangiz:</b>",
            reply_markup=level_keyboard)
        await state.update_data(languages=[])

    elif current_state == "FormFillingStates:q15_other_lang":
        await state.set_state(FormFillingStates.q14_eng_lang)
        await edit_form_question(
            call, bot, state, text_to_cut="Ingiliz tili:",
            question_text="<b>Ingiliz tilida suhbatlashish darajangiz:</b>",
            reply_markup=level_keyboard)
        languages = state_data["languages"]
        languages = languages[:1]
        await state.update_data(languages=languages)

    elif current_state == "FormFillingStates:lang_name":
        await state.set_state(FormFillingStates.q15_other_lang)
        state_data = await state.get_data()
        form_text = state_data["form_text"]
        languages = state_data["languages"]
        # Searching text about last added language
        text_to_cut = regexp_findall(r"Ingiliz tili: \d{0,3}%\n", form_text)
        if len(languages) > 2:  # If user didn't add other language
            last_answer_index = form_text.find(text_to_cut[0]) + len(text_to_cut[0])
            form_text = form_text[:last_answer_index]  # Form text where deleted the answer to last question
            await bot.edit_message_text(text="<b>Yana boshqa bir tilni bilasizmi?</b>",
                                        chat_id=call.message.chat.id, message_id=state_data["question_message_id"],
                                        reply_markup=confirming_keyboard)
            await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id,
                                        message_id=state_data["form_message_id"])
        else: 
            await bot.edit_message_text(text="<b>Yana boshqa bir tilni bilasizmi?</b>",
                                        chat_id=call.message.chat.id, message_id=state_data["question_message_id"],
                                        reply_markup=confirming_keyboard)

        languages = languages[:2]  # Deleting data about other languages
        await state.update_data(form_text=form_text, languages=languages)

    elif current_state == "FormFillingStates:lang_level":
        await state.set_state(FormFillingStates.q15_other_lang)
        state_data = await state.get_data()
        form_text = state_data["form_text"]
        last_answer_index = form_text.find(f"{state_data['lang_name'].capitalize()}:")
        form_text = form_text[:last_answer_index]  # Form text where deleted the answer to last question
        await bot.edit_message_text(text="<b>Yana boshqa bir tilni bilasizmi?</b>",
                                    chat_id=call.message.chat.id, message_id=state_data["question_message_id"],
                                    reply_markup=confirming_keyboard)
        await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id,
                                    message_id=state_data["form_message_id"])
        await state.update_data(form_text=form_text)

    elif current_state == "FormFillingStates:q16_word_app":
        await state.set_state(FormFillingStates.q15_other_lang)
        await edit_form_question(
            call, bot, state, text_to_cut="<b>Dasturlar:</b>",
            question_text="<b>Yana boshqa bir tilni bilasizmi?</b>",
            reply_markup=confirming_keyboard)

    elif current_state == "FormFillingStates:q17_excel_app":
        await state.set_state(FormFillingStates.q16_word_app)
        await edit_form_question(
            call, bot, state, text_to_cut="Word:",
            question_text="<b>Word dasturidan foydalana olish darajangiz:</b>",
            reply_markup=level_keyboard)
        await state.update_data(applications=[])

    elif current_state == "FormFillingStates:q18_1c_app":
        await state.set_state(FormFillingStates.q17_excel_app)
        await edit_form_question(
            call, bot, state, text_to_cut="Excel:",
            question_text="<b>Excel dasturidan foydalana olish darajangiz:</b>",
            reply_markup=level_keyboard)
        applications = state_data["applications"]
        applications = applications[:1]
        await state.update_data(applications=applications)

    elif current_state == "FormFillingStates:q19_other_app":
        await state.set_state(FormFillingStates.q18_1c_app)
        await edit_form_question(
            call, bot, state, text_to_cut="1C:",
            question_text="<b>1C dasturidan foydalana olish darajangiz:</b>",
            reply_markup=level_keyboard)
        applications = state_data["applications"]
        applications = applications[:2]
        await state.update_data(applications=applications)

    elif current_state in ["FormFillingStates:app_name", "FormFillingStates:q20_working_style"]:
        await state.set_state(FormFillingStates.q19_other_app)
        state_data = await state.get_data()
        form_text = state_data["form_text"]
        applications = state_data["applications"]
        # Searching text about last added application
        text_to_cut = regexp_findall(r"1C: \d{0,3}%\n", form_text)
        if len(state_data["applications"]) > 3:  # If user didn't add other application
            last_answer_index = form_text.find(text_to_cut[0]) + len(text_to_cut[0])
            form_text = form_text[:last_answer_index]  # Form text where deleted the answer to last question
            await bot.edit_message_text(text="<b>Yana boshqa bir dasturni bilasizmi?</b>",
                                        chat_id=call.message.chat.id, message_id=state_data["question_message_id"],
                                        reply_markup=confirming_keyboard)
            await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id,
                                        message_id=state_data["form_message_id"])
        else: 
            await bot.edit_message_text(text="<b>Yana boshqa bir dasturni bilasizmi?</b>",
                                        chat_id=call.message.chat.id, message_id=state_data["question_message_id"],
                                        reply_markup=confirming_keyboard)

        applications = applications[:3]  # Deleting data about other applications
        await state.update_data(form_text=form_text, applications=applications)

    elif current_state == "FormFillingStates:app_level":
        await state.set_state(FormFillingStates.q19_other_app)
        state_data = await state.get_data()
        form_text = state_data["form_text"]
        last_answer_index = form_text.find(f"{state_data['app_name'].capitalize()}:")
        form_text = form_text[:last_answer_index]  # Form text where deleted the answer to last question
        await bot.edit_message_text(text="<b>Yana boshqa biron dasturni bilasizmi?</b>",
                                    chat_id=call.message.chat.id, message_id=state_data["question_message_id"],
                                    reply_markup=confirming_keyboard)
        await bot.edit_message_text(text=form_text, chat_id=call.message.chat.id,
                                    message_id=state_data["form_message_id"])
        await state.update_data(form_text=form_text)

    elif current_state == "FormFillingStates:q21_salary":
        await state.set_state(FormFillingStates.q20_working_style)
        await edit_form_question(
            call, bot, state, text_to_cut="<b>Ishlash uslubi:</b>",
            question_text="<b>Qanday ishlashni afzal ko'rasiz?</b>",
            reply_markup=working_style_keyboard)

    elif current_state == "FormFillingStates:q22_positive_assessment":
        await state.set_state(FormFillingStates.q21_salary)
        await edit_form_question(
            call, bot, state, text_to_cut="<b>Oylik maoshi:</b>",
            question_text="<b>Qancha oylik maoshiga ishlagan bo'lar edingiz?</b>",
            reply_markup=salary_keyboard)

    elif current_state == "FormFillingStates:q23_negative_assessment":
        await state.set_state(FormFillingStates.q22_positive_assessment)
        await edit_form_question(
            call, bot, state, text_to_cut="<b>Ijobiy ta'rif:</b>",
            question_text="<b>O'zingizga qanday ijobiy ta'rif bera olasiz?</b>",
            reply_markup=menu_navigation_keyboard)

    elif current_state == "FormFillingStates:q24_photo":
        await state.set_state(FormFillingStates.q23_negative_assessment)
        await edit_form_question(
            call, bot, state, text_to_cut="<b>Salbiy ta'rif:</b>",
            question_text="<b>O'zingizga qanday salbiy ta'rif bera olasiz?</b>",
            reply_markup=menu_navigation_keyboard)

# ====================================================Back Buttons==================================================== #

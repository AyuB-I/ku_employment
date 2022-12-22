from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import CommandStart
from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.config import Config
from tgbot.database.functions.functions import get_form, add_user
from tgbot.database.models.models import Users, GendersEnum, NationsEnum, WorkingStylesEnum
from tgbot.keyboards.reply import make_menu_keyboard

flags = {"throttling_key": "default"}
basics_router = Router()


@basics_router.message(Command("help"), flags=flags)
async def command_help(message: Message):
    """  Help the user  """
    await message.answer(text="Har qanday xato, taklif va mulohazalaringizni\n"
                              "\"Startap va innovatsion tadbirkorlik\" departamenti boshlig’i @AA_Umarov'ga yuboring!\n"
                              "Bizning xizmatlarimizdan foydalanayotganingizdan minnatdormiz\U0001F60A")


@basics_router.message(CommandStart(), flags=flags)
async def user_start(message: Message, state: FSMContext, session: AsyncSession, config: Config):
    """  Great the user  """
    await state.clear()
    # Checking for user in database, if not exists add to database
    user = await session.get(Users, message.from_user.id)
    if not user:
        await add_user(session=session, telegram_id=message.from_user.id, username=message.from_user.username,
                       telegram_name=message.from_user.full_name)
    menu_keyboard = await make_menu_keyboard(session, message.from_user.id, config)
    await message.answer(
        f"<b>Assalamu Alaykum</b> {message.from_user.full_name}<b>!</b>\n\n"
        f"Men Qo'qon Universiteti \"Karyera Markazi\"ning asosiy ko'makchisiman.\n\n"
        f"Menda anketa to'ldiring va biz sizni tez orada ish bilan ta'minlaymiz\U0001F60A",
        reply_markup=menu_keyboard)


@basics_router.message(F.text == "\U0001F4CB Mening anketam", flags=flags)
async def show_my_form(message: Message, bot: Bot, session: AsyncSession):
    form_id = await session.scalar(select(Users.form_id).where(Users.telegram_id == message.from_user.id))
    form = await get_form(session, form_id)
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
        languages += f"<b>{i[0]}:</b> {i[1]}%\n"

    apps = ""
    for i in form.apps:
        apps += f"<b>{i[0]}:</b> {i[1]}%\n"

    working_style = 'Jamoada' if form.working_style == WorkingStylesEnum.COLLECTIVE else 'Individual'
    salary = "1 - 2 milion so'm"
    if form.wanted_salary == 2:
        salary = "3 - 4 million so'm"
    elif form.wanted_salary == 3:
        salary = "5 million so'm va undan yuqori"

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
                f"{languages}" \
                f"{apps}" \
                f"<b>Ishlash uslubi:</b> {working_style}\n" \
                f"<b>Oylik maoshi:</b> {salary}\n" \
                f"<b>Ijobiy ta'rif:</b> {form.positive_assessment}\n" \
                f"<b>Salbiy ta'rif:</b> {form.negative_assessment}\n" \
                f"<b>Tuzilgan vaqt:</b> {registered_at}" \
                f"{updated_at}"
    # Send form to user
    photo_message = await message.answer_photo(photo=form.photo_id)
    await bot.send_message(text=form_text, chat_id=message.chat.id, reply_to_message_id=photo_message.message_id)


@basics_router.message(F.text == "\U0001f3e2 Biz haqimizda", flags=flags)
async def show_information_about_us(message: Message):
    await message.answer(
        text="Salom! Men karyera markazi yordamchisiman.\n"
             "Mening yordamim bilan siz bo’sh ish o’rinlari bo’yicha takliflarga ega bo’lishingiz mumkin!")
    await message.answer(
        text="Anketani to’ldiring va o’zingiz istagan ish va maoshga ega bo’ling!")


@basics_router.message(F.text == "\U0000260E Kontaktlar", flags=flags)
async def show_contacts(message: Message):
    contacts_text = "<b><u>Kontaktlar</u></b>\n\n" \
                    "<b>Manzil:</b> <i>Farg‘ona viloyati, Qo‘qon shahri, Turkiston ko‘chasi, 28-A uy</i>\n\n" \
                    "<b>Telefon raqam:</b> <i>+998 (73) 545-55-55</i>\n\n" \
                    "<b>E-pochta:</b> <i>startup@kokanduni.uz</i>\n\n" \
                    "<a href='https://t.me/kokanduniversity'>Telegram</a> | " \
                    "<a href='https://www.instagram.com/kokanduniversity_official/'>Instagram</a> | " \
                    "<a href='https://www.facebook.com/kokanduniversity/'>Facebook</a> | " \
                    "<a href='https://www.youtube.com/@KokandUniversity/'>YouTube</a>"
    await message.answer(text=contacts_text, disable_web_page_preview=True)

import logging
from datetime import datetime
from typing import Optional, Union

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.database.functions.functions import get_forms, get_professions, get_directions
from tgbot.misc.cbdata import MainCallbackFactory

admin_functions = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001F4CB Anketalar",  # Emoji "clipboard"
                                 callback_data=MainCallbackFactory(action="show_forms").pack()),
            InlineKeyboardButton(text="\U0001F4C8 Statistika",  # Emoji "chart_with_upwards_trend"
                                 callback_data=MainCallbackFactory(action="show_stats").pack()),
            InlineKeyboardButton(text="\U00002709 E'lon berish",  # Emoji "envelope"
                                 callback_data=MainCallbackFactory(action="mailing").pack())
        ],
        [
            InlineKeyboardButton(text="\U0001F3E0",  # Emoji "house"
                                 callback_data=MainCallbackFactory(action="home").pack())
        ]
    ]
)

filter_categories_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="\U0001F465 Barcha",  # Emoji "busts_in_silhouette"
                                 callback_data=MainCallbackFactory(action="filter", data="everyone").pack()),
            InlineKeyboardButton(text="\U0001F464 Bitta foydalanuvchi",  # Emoji "bust_in_silhouette"
                                 callback_data=MainCallbackFactory(action="filter", data="one_user").pack())
        ],
        [
            InlineKeyboardButton(text="Jins", callback_data=MainCallbackFactory(action="filter", data="gender").pack()),
            InlineKeyboardButton(text="Kurs",
                                 callback_data=MainCallbackFactory(action="filter", data="university_grade").pack())
        ],
        [
            InlineKeyboardButton(text="Ta'lim yo'nalishi",
                                 callback_data=MainCallbackFactory(action="filter", data="university_direction").pack()),
            InlineKeyboardButton(text="Ishlash uslubi",
                                 callback_data=MainCallbackFactory(action="filter", data="working_style").pack())
        ],
        [
            InlineKeyboardButton(text="\U00002B05",  # Emoji "arrow_left"
                                 callback_data=MainCallbackFactory(action="back").pack()),
            InlineKeyboardButton(text="\U0001F3E0",  # Emoji "house"
                                 callback_data=MainCallbackFactory(action="home").pack())
        ]
    ]
)

home_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="\U0001F3E0",  # Emoji "house"
                              callback_data=MainCallbackFactory(action="home").pack())]
    ]
)

cancel_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="\U0000274C", callback_data=MainCallbackFactory(action="home").pack())]  # Emoji "x"
    ]
)

menu_navigation_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="\U00002B05",  # Emoji "arrow_left"
                                 callback_data=MainCallbackFactory(action="back").pack()),
            InlineKeyboardButton(text="\U0001F3E0",  # Emoji "house"
                                 callback_data=MainCallbackFactory(action="home").pack())
        ]
    ]
)

raw_true_false_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="\U00002714",  # Emoji "heavy_check_mark"
                                 callback_data=MainCallbackFactory(data=1).pack()),
            InlineKeyboardButton(text="\U0000274C",  # Emoji "x"
                                 callback_data=MainCallbackFactory(data=0).pack())
        ]
    ]
)

genders_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="\U0001F468 Erkak",  # Emoji "man"
                              callback_data=MainCallbackFactory(data="MALE").pack())],
        [InlineKeyboardButton(text="\U0001F469 Ayol",  # Emoji "man"
                              callback_data=MainCallbackFactory(data="FEMALE").pack())],
        [
            InlineKeyboardButton(text="\U00002B05",  # Emoji "arrow_left"
                                 callback_data=MainCallbackFactory(action="back").pack()),
            InlineKeyboardButton(text="\U0001F3E0",  # Emoji "house"
                                 callback_data=MainCallbackFactory(action="home").pack())
        ]
    ]
)

nations_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data=MainCallbackFactory(data="UZBEK").pack())
        ],
        [
            InlineKeyboardButton(text="🇷🇺 Rus", callback_data=MainCallbackFactory(data="RUSSIAN").pack())
        ],
        [
            InlineKeyboardButton(text="\U0001F3C1 Boshqa", callback_data=MainCallbackFactory(data="OTHER").pack())
        ],
        [
            InlineKeyboardButton(text="\U00002B05",  # Emoji "arrow_left"
                                 callback_data=MainCallbackFactory(action="back").pack()),
            InlineKeyboardButton(text="\U0001F3E0",  # Emoji "house"
                                 callback_data=MainCallbackFactory(action="home").pack())
        ]
    ],
)

university_grades_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="1", callback_data=MainCallbackFactory(data=1).pack()),
            InlineKeyboardButton(text="2", callback_data=MainCallbackFactory(data=2).pack())
        ],
        [
            InlineKeyboardButton(text="3", callback_data=MainCallbackFactory(data=3).pack()),
            InlineKeyboardButton(text="4", callback_data=MainCallbackFactory(data=4).pack())
        ],
        [
            InlineKeyboardButton(text="Magistr", callback_data=MainCallbackFactory(data=5).pack())
        ],
        [
            InlineKeyboardButton(text="\U00002B05",  # Emoji "arrow_left"
                                 callback_data=MainCallbackFactory(action="back").pack()),
            InlineKeyboardButton(text="\U0001F3E0",  # Emoji "house"
                                 callback_data=MainCallbackFactory(action="home").pack())
        ]
    ]
)

confirming_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="\U00002714",  # Emoji "heavy_check_mark"
                                 callback_data=MainCallbackFactory(data=True).pack()),
            InlineKeyboardButton(text="\U0000274C",  # Emoji "x"
                                 callback_data=MainCallbackFactory(data=False).pack())
        ],
        [
            InlineKeyboardButton(text="\U00002B05",  # Emoji 'arrow_left'
                                 callback_data=MainCallbackFactory(action="back").pack()),
            InlineKeyboardButton(text="\U0001F3E0",  # Emoji "house"
                                 callback_data=MainCallbackFactory(action="home").pack())
        ]
    ]
)

marital_status_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Turmush qurgan", callback_data=MainCallbackFactory(data=True).pack())],
        [InlineKeyboardButton(text="Turmush qurmagan", callback_data=MainCallbackFactory(data=False).pack())],
        [
            InlineKeyboardButton(text="\U00002B05",  # Emoji "arrow_left"
                                 callback_data=MainCallbackFactory(action="back").pack()),
            InlineKeyboardButton(text="\U0001F3E0",  # Emoji "house"
                                 callback_data=MainCallbackFactory(action="home").pack())
        ]
    ]
)

level_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="• 0%", callback_data=MainCallbackFactory(data=0).pack())],
        [InlineKeyboardButton(text="• 25%", callback_data=MainCallbackFactory(data=25).pack())],
        [InlineKeyboardButton(text="• 50%", callback_data=MainCallbackFactory(data=50).pack())],
        [InlineKeyboardButton(text="• 75%", callback_data=MainCallbackFactory(data=75).pack())],
        [InlineKeyboardButton(text="• 100%", callback_data=MainCallbackFactory(data=100).pack())],
        [
            InlineKeyboardButton(text="\U00002B05", callback_data=MainCallbackFactory(action="back").pack()),
            InlineKeyboardButton(text="\U0001F3E0", callback_data=MainCallbackFactory(action="home").pack())
        ]
    ]
)

working_style_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Jamoada", callback_data=MainCallbackFactory(data="COLLECTIVE").pack())],
        [InlineKeyboardButton(text="Individual", callback_data=MainCallbackFactory(data="INDIVIDUAL").pack())],
        [
            InlineKeyboardButton(text="\U00002B05", callback_data=MainCallbackFactory(action="back").pack()),
            InlineKeyboardButton(text="\U0001F3E0", callback_data=MainCallbackFactory(action="home").pack())
        ]
    ]
)

salary_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="1 - 2 million so'm", callback_data=MainCallbackFactory(data=1).pack())],
        [InlineKeyboardButton(text="3 - 4 million so'm", callback_data=MainCallbackFactory(data=2).pack())],
        [InlineKeyboardButton(text="5 million va undan yuqori", callback_data=MainCallbackFactory(data=3).pack())],
        [
            InlineKeyboardButton(text="\U00002B05", callback_data=MainCallbackFactory(action="back").pack()),
            InlineKeyboardButton(text="\U0001F3E0", callback_data=MainCallbackFactory(action="home").pack())
        ]
    ]
)

sending_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="\U00002714 Yuborish", callback_data=MainCallbackFactory(
                action="send").pack()),  # Emoji "heavy_check_mark"
            InlineKeyboardButton(text="\U0000274C Bekor qilish", callback_data=MainCallbackFactory(
                action="home").pack())  # Emoji "x"
        ]
    ]
)


async def make_professions_keyboard(session: AsyncSession, checked_professions: Union[list, tuple] = (),
                                    last_selected_profession: Union[int] = None, is_check: bool = True) -> Optional[
    InlineKeyboardMarkup
]:
    """  Make a keyboard that contains a list of professions and check or uncheck it
    when user selects that button  """
    builder = InlineKeyboardBuilder()
    all_professions = {k: v for k, v in await get_professions(session)}
    if not all_professions:
        return None
    checked_professions = checked_professions

    for profession_id, title in all_professions.items():
        # Uncheck button if user has already checked this button
        if not is_check and profession_id == last_selected_profession:
            builder.row(InlineKeyboardButton(
                text=title.capitalize(),
                callback_data=MainCallbackFactory(action="select", data=profession_id).pack()))
            continue
        # Check selected button
        builder.row(InlineKeyboardButton(
            text=f"\U00002705 {title.capitalize()}" if profession_id in checked_professions else title.capitalize(),
            callback_data=MainCallbackFactory(action="select", data=profession_id).pack()))

    if last_selected_profession:  # If the user selected a profession
        builder.row(
            InlineKeyboardButton(
                text="\U00002714",  # Emoji "heavy_check_mark"
                callback_data=MainCallbackFactory(action="confirm").pack()),
        )
    builder.row(
        InlineKeyboardButton(
            text="\U00002B05",  # Emoji "arrow_left"
            callback_data=MainCallbackFactory(action="back").pack()),
        InlineKeyboardButton(
            text="\U0001F3E0",  # Emoji "house"
            callback_data=MainCallbackFactory(action="home").pack())
    )
    return builder.as_markup()


async def make_professions_keyboard_for_admin(session: AsyncSession) -> Optional[
    InlineKeyboardMarkup
]:
    """  Make a keyboard that contains a list of professions with emoji "X"  """
    builder = InlineKeyboardBuilder()
    all_professions = {k: v for k, v in await get_professions(session)}
    counter = 1  # Using it to numerate the buttons

    for profession_id, title in all_professions.items():
        builder.row(InlineKeyboardButton(
            text=f"{counter}. {title.capitalize()} \U0000274C ",  # Emoji "X"
            callback_data=MainCallbackFactory(action="delete", data=profession_id).pack()))
        counter += 1

    builder.row(InlineKeyboardButton(
        text="\U0001F3E0",  # Emoji "house"
        callback_data=MainCallbackFactory(action="home").pack())
    )
    return builder.as_markup()


async def make_directions_keyboard(session: AsyncSession, with_cross: bool = False) -> Optional[
    InlineKeyboardMarkup
]:
    """  Make a keyboard that contains a list of university directions  """
    builder = InlineKeyboardBuilder()
    all_directions = {k: v for k, v in await get_directions(session)}
    counter = 1

    if with_cross:
        for direction_id, title in all_directions.items():
            builder.row(InlineKeyboardButton(
                text=f"{counter}. {title.capitalize()} \U0000274C ",  # Emoji "X"
                callback_data=MainCallbackFactory(action="delete", data=direction_id).pack()))
            counter += 1

        builder.row(InlineKeyboardButton(
            text="\U0001F3E0",  # Emoji "house"
            callback_data=MainCallbackFactory(action="home").pack())
        )
    else:
        for direction_id, title in all_directions.items():
            builder.row(InlineKeyboardButton(
                text=title.capitalize(),
                callback_data=MainCallbackFactory(action="select", data=direction_id).pack()))

        builder.row(
            InlineKeyboardButton(
                text="\U00002B05",  # Emoji "arrow_left"
                callback_data=MainCallbackFactory(action="back").pack()),
            InlineKeyboardButton(
                text="\U0001F3E0",  # Emoji "house"
                callback_data=MainCallbackFactory(action="home").pack())
        )
    return builder.as_markup()


async def make_forms_keyboard(session: AsyncSession, begin: Optional[datetime] = None, action: str = "first",
                              filter_type: str = None, counter: int = 0):
    # Getting forms from database
    db_data = await get_forms(session, begin, action, filter_type)
    forms_dict = db_data["forms_dict"]
    # Creating a form list with inline keyboard
    inline_keyboard = InlineKeyboardBuilder()
    if forms_dict:
        text = ""
        for key in forms_dict:
            counter += 1
            text += f"{counter}. {forms_dict[key]}\n"
            inline_keyboard.row(InlineKeyboardButton(text=counter, callback_data=MainCallbackFactory(action="select",
                                                                                                     data=key).pack()))
        inline_keyboard.adjust(5)
    else:
        text = "Anketa mavjud emas!"
        counter = 0
    # Making filter button
    if filter_type is None:
        inline_keyboard.row(InlineKeyboardButton(text="Filter - barchasi", callback_data=MainCallbackFactory(
            action="filter", data=None).pack()))
    elif filter_type == "male":
        inline_keyboard.row(InlineKeyboardButton(text="Filter - erkak", callback_data=MainCallbackFactory(
            action="filter", data="male").pack()))
    elif filter_type == "female":
        inline_keyboard.row(InlineKeyboardButton(text="Filter - ayol", callback_data=MainCallbackFactory(
            action="filter", data="female").pack()))
    elif filter_type == "working":
        inline_keyboard.row(InlineKeyboardButton(text="Filter - ish bilan band", callback_data=MainCallbackFactory(
            action="filter", data="working").pack()))
    elif filter_type == "not_working":
        inline_keyboard.row(InlineKeyboardButton(text="Filter - ishsiz", callback_data=MainCallbackFactory(
            action="filter", data="not_working").pack()))
    elif filter_type == 5:
        inline_keyboard.row(InlineKeyboardButton(text="Filter - Kurs: magistr", callback_data=MainCallbackFactory(
            action="filter", data="master").pack()))
    else:
        inline_keyboard.row(InlineKeyboardButton(
            text=f"Filter - Kurs: {filter_type}",
            callback_data=MainCallbackFactory(action="filter", data=filter_type).pack()), width=1)
    # Make next button if it's first row
    smallest_date = datetime.timestamp(db_data["smallest_date"]) if db_data["smallest_date"] else None
    biggest_date = datetime.timestamp(db_data["biggest_date"]) if db_data["biggest_date"] else None
    first_row_date = datetime.timestamp(db_data["first_row_date"]) if db_data["first_row_date"] else None
    last_row_date = datetime.timestamp(db_data["last_row_date"]) if db_data["last_row_date"] else None
    logging.info(f"{smallest_date=}")
    logging.info(f"{biggest_date=}")
    logging.info(f"{first_row_date=}")
    logging.info(f"{last_row_date=}")

    if smallest_date is not None and biggest_date == last_row_date and smallest_date != first_row_date:
        inline_keyboard.row(InlineKeyboardButton(text="\U000023ED", callback_data=MainCallbackFactory(
            action="next", counter=counter).pack()))
    elif biggest_date is not None and smallest_date == first_row_date and biggest_date != last_row_date:
        inline_keyboard.row(InlineKeyboardButton(text="\U000023EE", callback_data=MainCallbackFactory(
            action="previous", counter=counter).pack()))
    elif biggest_date is not None and biggest_date != last_row_date and smallest_date != first_row_date:
        inline_keyboard.row(InlineKeyboardButton(text="\U000023EE", callback_data=MainCallbackFactory(
            action="previous", counter=counter).pack()))
        inline_keyboard.add(InlineKeyboardButton(text="\U000023ED", callback_data=MainCallbackFactory(
            action="next", counter=counter).pack()))

    inline_keyboard.row(
        InlineKeyboardButton(text="\U00002B05", callback_data=MainCallbackFactory(action="back").pack()),
        InlineKeyboardButton(text="\U0001F3E0", callback_data=MainCallbackFactory(action="home").pack())
    )

    # Making a JSON because InlineKeyboardMarkup isn't JSON serializable
    # You can deserialize it using InlineKeyboardMarkup.parse_raw(keyboard_markup_json_here)
    keyboard_data = {"keyboard": inline_keyboard.as_markup().json(), "text": text, "smallest_date": smallest_date,
                     "biggest_date": biggest_date}
    return keyboard_data

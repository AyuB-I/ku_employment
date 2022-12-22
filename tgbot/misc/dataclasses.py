from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from tgbot.database.models.models import GendersEnum, NationsEnum, WorkingStylesEnum


@dataclass
class Form:
    from_id: int
    full_name: str
    birth_date: datetime
    gender: GendersEnum
    phonenum: str
    professions: list[str]
    address: str
    nation: NationsEnum
    university_grade: int
    direction: Optional[str]
    working_company: tuple[str]
    marital_status: bool
    driver_license: bool
    languages: list[tuple[str, int]]
    apps: list[tuple[str, int]]
    working_style: WorkingStylesEnum
    wanted_salary: int
    positive_assessment: str
    negative_assessment: str
    photo_id: str
    registered_at: datetime
    updated_at: datetime
    telegram_name: str
    username: str
    telegram_id: int


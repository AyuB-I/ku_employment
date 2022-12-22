import enum

from sqlalchemy import Column, BIGINT, SMALLINT, VARCHAR, TEXT, TIMESTAMP, DATE, ForeignKey, BOOLEAN, func, Enum
from .base import Base


#  Creating enum types
class GendersEnum(enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class NationsEnum(enum.Enum):
    UZBEK = "UZBEK"
    RUSSIAN = "RUSSIAN"
    OTHER = "OTHER"


class WorkingStylesEnum(enum.Enum):
    COLLECTIVE = "COLLECTIVE"
    INDIVIDUAL = "INDIVIDUAL"


# Creating database tables
class UniversityDirections(Base):
    __tablename__ = "university_directions"

    direction_id = Column(SMALLINT, primary_key=True, autoincrement=True)
    title = Column(VARCHAR(64), nullable=False, unique=True)


class Forms(Base):
    __tablename__ = "forms"

    form_id = Column(SMALLINT, primary_key=True, autoincrement=True)
    full_name = Column(VARCHAR(64), nullable=False)
    birth_date = Column(DATE, nullable=False)
    gender = Column(Enum(GendersEnum), nullable=False)
    phonenum = Column(VARCHAR(20), nullable=False)
    address = Column(VARCHAR(255), nullable=False)
    nation = Column(Enum(NationsEnum), nullable=False)
    university_grade = Column(SMALLINT, nullable=False)
    direction_id = Column(SMALLINT, ForeignKey("university_directions.direction_id", ondelete="SET NULL"),
                          nullable=True)
    marital_status = Column(BOOLEAN, nullable=False)
    driver_license = Column(BOOLEAN, nullable=False)
    working_style = Column(Enum(WorkingStylesEnum), nullable=False)
    wanted_salary = Column(SMALLINT, nullable=False)
    positive_assessment = Column(TEXT, nullable=False)
    negative_assessment = Column(TEXT, nullable=False)
    photo_id = Column(TEXT, nullable=False)
    registered_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, nullable=True)


class Professions(Base):
    __tablename__ = "professions"

    profession_id = Column(SMALLINT, primary_key=True, autoincrement=True)
    title = Column(VARCHAR(32), nullable=False, unique=True)


class FormsProfessions(Base):
    __tablename__ = "forms_professions"

    form_id = Column(SMALLINT, ForeignKey("forms.form_id", ondelete="CASCADE"), primary_key=True)
    profession_id = Column(SMALLINT, ForeignKey("professions.profession_id", ondelete="CASCADE"), primary_key=True)


class WorkingCompanies(Base):
    __tablename__ = "working_companies"

    form_id = Column(SMALLINT, ForeignKey("forms.form_id", ondelete="CASCADE"), primary_key=True)
    name = Column(VARCHAR(255), nullable=False)
    position = Column(VARCHAR(255), nullable=False)


class Languages(Base):
    __tablename__ = "languages"

    language_id = Column(SMALLINT, primary_key=True, autoincrement=True)
    form_id = Column(SMALLINT, ForeignKey("forms.form_id", ondelete="CASCADE"), nullable=False)
    name = Column(VARCHAR(32), nullable=False)
    level = Column(SMALLINT, nullable=False)


class Applications(Base):
    __tablename__ = "applications"

    application_id = Column(SMALLINT, primary_key=True, autoincrement=True)
    form_id = Column(SMALLINT, ForeignKey("forms.form_id", ondelete="CASCADE"), nullable=False)
    name = Column(VARCHAR(32), nullable=False)
    level = Column(SMALLINT, nullable=False)


class Users(Base):
    __tablename__ = "users"

    telegram_id = Column(BIGINT, primary_key=True)
    username = Column(VARCHAR(255), nullable=True)
    telegram_name = Column(VARCHAR(255), nullable=False)
    form_id = Column(SMALLINT, ForeignKey("forms.form_id", ondelete="SET NULL"), unique=True, nullable=True)
    registered_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

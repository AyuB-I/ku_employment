from contextlib import suppress
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, asc, desc, case, func, insert, delete, update
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError, NoResultFound

from tgbot.database.models.models import Forms, FormsProfessions, Professions, UniversityDirections, WorkingCompanies, \
    Languages, Applications, Users
from tgbot.misc.dataclasses import Form


# --------------------------------------Functions to work with table Users-------------------------------------------- #

async def add_user(session: AsyncSession, telegram_id, username, telegram_name):
    """  Add user to database  """
    query = insert(Users).values(telegram_id=telegram_id, username=username, telegram_name=telegram_name)
    await session.execute(query)
    with suppress(IntegrityError):
        await session.commit()


async def get_user_ids_by_filter(session: AsyncSession, target_category: str, target: str):
    if target_category == "gender":
        form_ids = (await session.scalars(select(Forms.form_id).where(Forms.gender == target))).all()
        query = await session.scalars(select(Users.telegram_id).where(Users.form_id.in_(form_ids)))
        result = query.all()

    elif target_category == "university_grade":
        form_ids = (await session.scalars(select(Forms.form_id).where(Forms.university_grade == target))).all()
        query = await session.scalars(select(Users.telegram_id).where(Users.form_id.in_(form_ids)))
        result = query.all()

    elif target_category == "university_direction":
        form_ids = (await session.scalars(select(Forms.form_id).where(Forms.direction_id == target))).all()
        query = await session.scalars(select(Users.telegram_id).where(Users.form_id.in_(form_ids)))
        result = query.all()
    elif target_category == "working_style":
        form_ids = (await session.scalars(select(Forms.form_id).where(Forms.working_style == target))).all()
        query = await session.scalars(select(Users.telegram_id).where(Users.form_id.in_(form_ids)))
        result = query.all()
    else:
        query = await session.scalars(select(Users.telegram_id))
        result = query.all()
    return result


# ======================================Functions to work with table Users============================================ #


# ---------------------------------Functions to work with table Professions------------------------------------------- #

async def add_profession(session: AsyncSession, title):
    """  Add a new profession to database  """
    query = insert(Professions).values(title=title)
    await session.execute(query)
    with suppress(IntegrityError):
        await session.commit()


async def get_professions(session: AsyncSession):
    """  Get professions' ids and titles  """
    query = select(Professions.profession_id, Professions.title)
    result = await session.execute(query)
    return result.all()


async def get_profession(session: AsyncSession, profession_id):
    """  Get a profession from database by its id  """
    query = select(Professions.title).where(Professions.profession_id == profession_id)
    result = await session.execute(query)
    return result.one()


async def delete_profession(session: AsyncSession, profession_id):
    """  Delete a profession from database  """
    query = delete(Professions).where(Professions.profession_id == profession_id)
    await session.execute(query)
    await session.commit()


# =================================Functions to work with table Professions=========================================== #


# ---------------------------------Functions to work with table UniversityDirections---------------------------------- #

async def add_direction(session: AsyncSession, title):
    """  Add a new university direction to database  """
    query = insert(UniversityDirections).values(title=title)
    await session.execute(query)
    with suppress(IntegrityError):
        await session.commit()


async def get_directions(session: AsyncSession):
    """  Get university directions' ids and titles  """
    query = select(UniversityDirections.direction_id, UniversityDirections.title)
    result = await session.execute(query)
    return result.all()


async def get_direction(session: AsyncSession, direction_id):
    """  Get a university direction from database by its id  """
    query = select(UniversityDirections.title).where(UniversityDirections.direction_id == direction_id)
    result = await session.execute(query)
    return result.one()


async def delete_direction(session: AsyncSession, direction_id):
    """  Delete a university direction from database  """
    query = delete(UniversityDirections).where(UniversityDirections.direction_id == direction_id)
    await session.execute(query)
    await session.commit()


# =================================Functions to work with table UniversityDirections================================== #


# -----------------------------------------Functions to work with table Forms----------------------------------------- #

async def get_users_form_id(session: AsyncSession, telegram_id):
    """  Get form_id from table users  """
    query = select(Users.form_id).where(Users.telegram_id == telegram_id)
    try:
        result = await session.scalar(query)
    except NoResultFound:
        result = None
    return result


async def update_users_form_id(session: AsyncSession, telegram_id, form_id):
    """  Update form_id in table users  """
    query = update(Users).where(Users.telegram_id == telegram_id).values(form_id=form_id)
    await session.execute(query)
    await session.commit()


async def is_form_updated(session: AsyncSession, form_id: int) -> bool:
    """  Check if there is data in the updated_at row in the table forms  """
    result = await session.scalar(select(Forms.updated_at).where(Forms.form_id == form_id))
    return True if result else False


async def add_form(session: AsyncSession, telegram_id: int, full_name: str, birth_date: datetime, gender: str,
                   phonenum: str, address: str, nation: str, university_grade: int, direction_id: int,
                   marital_status: bool, driver_license: bool, working_style: str, wanted_salary: int,
                   positive_assessment: str, negative_assessment: str, photo_id: str, checked_professions: list[dict],
                   company: list[str], languages: list[dict], applications: list[dict]):
    """  Add all data about forms to table forms and other related tables  """
    # Inserting all data about form to table forms
    form_query = insert(Forms).values(
        full_name=full_name, birth_date=birth_date, gender=gender, phonenum=phonenum, address=address, nation=nation,
        university_grade=university_grade, direction_id=direction_id, marital_status=marital_status,
        driver_license=driver_license, working_style=working_style, wanted_salary=wanted_salary,
        positive_assessment=positive_assessment, negative_assessment=negative_assessment, photo_id=photo_id).returning(
        Forms)
    result = await session.execute(form_query)
    form_id = result.first()[0]

    # Inserting all data about professions that user selected to table forms_professions
    if checked_professions:
        for profession_id in checked_professions:
            await session.execute(insert(FormsProfessions).values(form_id=form_id, profession_id=profession_id))
    # Inserting all data about user's working company
    if company:
        await session.execute(insert(WorkingCompanies).values(form_id=form_id, name=company[0], position=company[1]))
    # Inserting all data about languages to table languages
    for language_data in languages:
        await session.execute(insert(Languages).values(form_id=form_id, name=language_data["name"],
                                                       level=language_data["level"]))
    # Inserting all data about applications to table application
    for app_data in applications:
        await session.execute(insert(Applications).values(form_id=form_id, name=app_data["name"],
                                                          level=app_data["level"]))
    # Not committing here because function "update_users_form_id" will do it
    await update_users_form_id(session, telegram_id, form_id)
    return form_id


async def update_form(session: AsyncSession, form_id: int, telegram_id: int, full_name: str,
                      birth_date: datetime, gender: str, phonenum: str, address: str, nation: str,
                      university_grade: int, direction_id: int, marital_status: bool, driver_license: bool,
                      working_style: str, wanted_salary: int, positive_assessment: str, negative_assessment: str,
                      photo_id: str, checked_professions: list[dict], company: list[str], languages: list[dict],
                      applications: list[dict]):
    """  Update data about forms  """
    # Updating data about forms in table forms
    form_query = update(Forms).where(Forms.form_id == form_id).values(
        full_name=full_name, birth_date=birth_date, gender=gender, phonenum=phonenum, address=address, nation=nation,
        university_grade=university_grade, direction_id=direction_id, marital_status=marital_status,
        driver_license=driver_license, working_style=working_style, wanted_salary=wanted_salary,
        positive_assessment=positive_assessment, negative_assessment=negative_assessment, photo_id=photo_id)
    await session.execute(form_query)

    await session.execute(delete(FormsProfessions).where(FormsProfessions.form_id == form_id))
    # Inserting all data about professions that user selected to table forms_professions
    if checked_professions:
        for profession_id in checked_professions:
            await session.execute(insert(FormsProfessions).values(form_id=form_id, profession_id=profession_id))

    await session.execute(delete(WorkingCompanies).where(WorkingCompanies.form_id == form_id))
    # Inserting data about user's working company to table working_companies
    if company:
        await session.execute(insert(WorkingCompanies).values(form_id=form_id, name=company[0], position=company[1]))

    await session.execute(delete(Languages).where(Languages.form_id == form_id))
    # Inserting all data about languages to table languages
    for language_data in languages:
        await session.execute(insert(Languages).values(form_id=form_id, name=language_data["name"],
                                                       level=language_data["level"]))

    await session.execute(delete(Applications).where(Applications.form_id == form_id))
    # Inserting all data about applications to table application
    for app_data in applications:
        await session.execute(insert(Applications).values(form_id=form_id, name=app_data["name"],
                                                          level=app_data["level"]))
    # Setting new updated time to table Forms
    await session.execute(update(Forms).where(Forms.form_id == form_id).values(updated_at=datetime.now()))
    # Not committing here because function "update_users_form_id" will do it
    await update_users_form_id(session, telegram_id, form_id)


async def get_forms(session: AsyncSession, begin: Optional[datetime] = None, action: str = "first",
                    filter_type: Optional[str] = None, limit: int = 10):
    """  Get a list of forms depending on the condition  """
    case_xpr = case(
        [(Forms.updated_at is not None and Forms.updated_at > Forms.registered_at, Forms.updated_at)],
        else_=Forms.registered_at
    ).label("date")
    # Getting rows without filter
    if filter_type is None:
        if action == "next":
            query = select(Forms.form_id, Forms.full_name).where(begin > case_xpr).order_by(desc(case_xpr)).limit(limit)
            all_rows = (await session.execute(query)).all()
        elif action == "previous":
            subquery = select(Forms.form_id, Forms.full_name, case_xpr.label("reg_date")).where(
                begin < case_xpr).order_by(asc(case_xpr)).limit(limit).subquery()
            all_rows = (await session.execute(select(subquery.c.form_id, subquery.c.full_name).select_from(
                subquery).order_by(desc(subquery.c.reg_date)))).all()  # Reversing the result to the desc order
        else:  # If it is first request to get all forms
            query = select(Forms.form_id, Forms.full_name).order_by(
                desc(case_xpr)).limit(limit)
            all_rows = (await session.execute(query)).all()
        # Making a dict where the keys are form_ids and values are full_names
        forms_dict = {}
        for k, v in all_rows:
            forms_dict[k] = v
        # Getting the smallest and the biggest dates from all_rows
        if all_rows:
            smallest_date = (await session.execute(
                select(case_xpr).where(Forms.form_id == all_rows[-1][0])
            )).scalar()
            biggest_date = (await session.execute(
                select(case_xpr).where(Forms.form_id == all_rows[0][0])
            )).scalar()
        else:
            smallest_date = None
            biggest_date = None
        # Getting the earliest and the latest registered or updated date of the form from table forms
        first_row_date = (await session.execute(
            select(case_xpr).order_by(asc(case_xpr))
        )).scalar()
        last_row_date = (await session.execute(
            select(case_xpr).order_by(desc(case_xpr))
        )).scalar()

    # Getting all rows where gender is male
    elif filter_type == "male":
        if action == "next":
            query = select(Forms.form_id, Forms.full_name).where(begin > case_xpr, Forms.gender == "MALE").order_by(
                desc(case_xpr)).limit(limit)
            all_rows = (await session.execute(query)).all()
        elif action == "previous":
            subquery = select(Forms.form_id, Forms.full_name, case_xpr.label("reg_date")).where(
                begin < case_xpr, Forms.gender == "MALE").order_by(asc(case_xpr)).limit(limit).subquery()
            all_rows = (await session.execute(select(subquery.c.form_id, subquery.c.full_name).select_from(
                subquery).order_by(desc(subquery.c.reg_date)))).all()
        else:  # If it is first request with filter "MALE"
            query = select(Forms.form_id, Forms.full_name).where(Forms.gender == "MALE").order_by(desc(case_xpr)
                                                                                                  ).limit(limit)
            all_rows = (await session.execute(query)).all()
        forms_dict = {}
        for k, v in all_rows:
            forms_dict[k] = v
        if all_rows:
            smallest_date = (await session.execute(
                select(case_xpr).where(Forms.form_id == all_rows[-1][0])
            )).scalar()
            biggest_date = (await session.execute(
                select(case_xpr).where(Forms.form_id == all_rows[0][0])
            )).scalar()
        else:
            smallest_date = None
            biggest_date = None
        first_row_date = (await session.execute(
            select(case_xpr).where(Forms.gender == "MALE").order_by(asc(case_xpr))
        )).scalar()
        last_row_date = (await session.execute(
            select(case_xpr).where(Forms.gender == "MALE").order_by(desc(case_xpr))
        )).scalar()

    # Getting all rows where gender is female
    elif filter_type == "female":
        if action == "next":
            query = select(Forms.form_id, Forms.full_name).where(
                begin > case_xpr, Forms.gender == "FEMALE").order_by(desc(case_xpr)).limit(limit)
            all_rows = (await session.execute(query)).all()
        elif action == "previous":
            subquery = select(Forms.form_id, Forms.full_name, case_xpr.label("reg_date")).where(
                begin < case_xpr, Forms.gender == "FEMALE").order_by(asc(case_xpr)).limit(limit).subquery()
            all_rows = (await session.execute(select(subquery.c.form_id, subquery.c.full_name).select_from(
                subquery).order_by(desc(subquery.c.reg_date)))).all()
        else:  # If it is first request with filter "MALE"
            query = select(Forms.form_id, Forms.full_name).where(Forms.gender == "FEMALE").order_by(desc(case_xpr)
                                                                                                    ).limit(limit)
            all_rows = (await session.execute(query)).all()
        forms_dict = {}
        for k, v in all_rows:
            forms_dict[k] = v
        if all_rows:
            smallest_date = (await session.execute(
                select(case_xpr).where(Forms.form_id == all_rows[-1][0])
            )).scalar()
            biggest_date = (await session.execute(
                select(case_xpr).where(Forms.form_id == all_rows[0][0])
            )).scalar()
        else:
            smallest_date = None
            biggest_date = None

        first_row_date = (await session.execute(
            select(case_xpr).where(Forms.gender == "FEMALE").order_by(asc(case_xpr))
        )).scalar()
        last_row_date = (await session.execute(
            select(case_xpr).where(Forms.gender == "FEMALE").order_by(desc(case_xpr))
        )).scalar()

    # Getting all form ids where there is a record in table working_companies
    elif filter_type == "working":
        if action == "next":
            query = select(Forms.form_id, Forms.full_name).where(
                begin > case_xpr, Forms.form_id.in_(select(WorkingCompanies.form_id))
            ).order_by(desc(case_xpr)).limit(limit)
            all_rows = (await session.execute(query)).all()
        elif action == "previous":
            subquery = select(Forms.form_id, Forms.full_name, case_xpr.label("reg_date")).where(
                begin < case_xpr, Forms.form_id.in_(select(WorkingCompanies.form_id))).order_by(
                asc(case_xpr)).limit(limit).subquery()
            all_rows = (await session.execute(select(subquery.c.form_id, subquery.c.full_name).select_from(
                subquery).order_by(desc(subquery.c.reg_date)))).all()
        else:  # If it is first request with filter "MALE"
            query = select(Forms.form_id, Forms.full_name).where(
                Forms.form_id.in_(select(WorkingCompanies.form_id))
                ).order_by(desc(case_xpr)).limit(limit)
            all_rows = (await session.execute(query)).all()
        forms_dict = {}
        for k, v in all_rows:
            forms_dict[k] = v
        if all_rows:
            smallest_date = (await session.execute(
                select(case_xpr).where(Forms.form_id == all_rows[-1][0])
            )).scalar()
            biggest_date = (await session.execute(
                select(case_xpr).where(Forms.form_id == all_rows[0][0])
            )).scalar()
        else:
            smallest_date = None
            biggest_date = None

        first_row_date = (await session.execute(
            select(case_xpr).where(Forms.form_id.in_(select(WorkingCompanies.form_id))).order_by(asc(case_xpr))
        )).scalar()
        last_row_date = (await session.execute(
            select(case_xpr).where(Forms.form_id.in_(select(WorkingCompanies.form_id))).order_by(desc(case_xpr))
        )).scalar()

    # Getting all form ids where there isn't any record in table working_companies
    elif filter_type == "not_working":
        if action == "next":
            query = select(Forms.form_id, Forms.full_name).where(
                begin > case_xpr, Forms.form_id.not_in(select(WorkingCompanies.form_id))
            ).order_by(desc(case_xpr)).limit(limit)
            all_rows = (await session.execute(query)).all()
        elif action == "previous":
            subquery = select(Forms.form_id, Forms.full_name, case_xpr.label("reg_date")).where(
                begin < case_xpr, Forms.form_id.not_in(select(WorkingCompanies.form_id))).order_by(
                asc(case_xpr)).limit(limit).subquery()
            all_rows = (await session.execute(select(subquery.c.form_id, subquery.c.full_name).select_from(
                subquery).order_by(desc(subquery.c.reg_date)))).all()
        else:  # If it is first request with filter "MALE"
            query = select(Forms.form_id, Forms.full_name).where(
                Forms.form_id.not_in(select(WorkingCompanies.form_id))
                ).order_by(desc(case_xpr)).limit(limit)
            all_rows = (await session.execute(query)).all()
        forms_dict = {}
        for k, v in all_rows:
            forms_dict[k] = v
        if all_rows:
            smallest_date = (await session.execute(
                select(case_xpr).where(Forms.form_id == all_rows[-1][0])
            )).scalar()
            biggest_date = (await session.execute(
                select(case_xpr).where(Forms.form_id == all_rows[0][0])
            )).scalar()
        else:
            smallest_date = None
            biggest_date = None

        first_row_date = (await session.execute(
            select(case_xpr).where(Forms.form_id.not_in(select(WorkingCompanies.form_id))).order_by(asc(case_xpr))
        )).scalar()
        last_row_date = (await session.execute(
            select(case_xpr).where(Forms.form_id.not_in(select(WorkingCompanies.form_id))).order_by(desc(case_xpr))
        )).scalar()

    # Getting all rows where university_grade is 5 (5 means master)
    elif filter_type == 5:
        if action == "next":
            query = select(Forms.form_id, Forms.full_name).where(
                begin > case_xpr, Forms.university_grade == 5).order_by(desc(case_xpr)).limit(limit)
            all_rows = (await session.execute(query)).all()
        elif action == "previous":
            subquery = select(Forms.form_id, Forms.full_name, case_xpr.label("reg_date")).where(
                begin < case_xpr, Forms.university_grade == 5).order_by(asc(case_xpr)).limit(limit).subquery()
            all_rows = (await session.execute(select(subquery.c.form_id, subquery.c.full_name).select_from(
                subquery).order_by(desc(subquery.c.reg_date)))).all()
        else:  # If it is the first request with filter 5
            query = select(Forms.form_id, Forms.full_name).where(Forms.university_grade == 5).order_by(
                desc(case_xpr)).limit(limit)
            all_rows = (await session.execute(query)).all()
        forms_dict = {}
        for k, v in all_rows:
            forms_dict[k] = v
        if all_rows:
            smallest_date = (await session.execute(
                select(case_xpr).where(Forms.form_id == all_rows[-1][0])
            )).scalar()
            biggest_date = (await session.execute(
                select(case_xpr).where(Forms.form_id == all_rows[0][0])
            )).scalar()
        else:
            smallest_date = None
            biggest_date = None
        first_row_date = (await session.execute(
            select(case_xpr).where(Forms.university_grade == 5).order_by(asc(case_xpr))
        )).scalar()
        last_row_date = (await session.execute(
            select(case_xpr).where(Forms.university_grade == 5).order_by(desc(case_xpr))
        )).scalar()

    # Getting all rows where university_grade is equal to 1, 2, 3 or 4
    else:
        if action == "next":
            query = select(Forms.form_id, Forms.full_name).where(
                begin > case_xpr, Forms.university_grade == filter_type).order_by(desc(case_xpr)).limit(limit)
            all_rows = (await session.execute(query)).all()
        elif action == "previous":
            subquery = select(Forms.form_id, Forms.full_name, case_xpr.label("reg_date")).where(
                begin < case_xpr, Forms.university_grade == filter_type).order_by(asc(case_xpr)).limit(limit).subquery()
            all_rows = (await session.execute(select(subquery.c.form_id, subquery.c.full_name).select_from(
                subquery).order_by(desc(subquery.c.reg_date)))).all()
        else:  # If it is first request with filter university grade 1 - 4
            query = select(Forms.form_id, Forms.full_name).where(Forms.university_grade == filter_type).order_by(
                desc(case_xpr)).limit(limit)
            all_rows = (await session.execute(query)).all()
        forms_dict = {}
        for k, v in all_rows:
            forms_dict[k] = v
        if all_rows:
            smallest_date = (await session.execute(
                select(case_xpr).where(Forms.form_id == all_rows[-1][0])
            )).scalar()
            biggest_date = (await session.execute(
                select(case_xpr).where(Forms.form_id == all_rows[0][0])
            )).scalar()
        else:
            smallest_date = None
            biggest_date = None
        first_row_date = (await session.execute(
            select(case_xpr).where(Forms.university_grade == filter_type).order_by(asc(case_xpr))
        )).scalar()
        last_row_date = (await session.execute(
            select(case_xpr).where(Forms.university_grade == filter_type).order_by(desc(case_xpr))
        )).scalar()

    db_data = {"forms_dict": forms_dict, "smallest_date": smallest_date, "biggest_date": biggest_date,
               "first_row_date": first_row_date, "last_row_date": last_row_date}
    return db_data


async def get_form(session: AsyncSession, form_id) -> Form:
    """  Get all data about form from database by its id  """
    form = await session.scalar(select(Forms).where(Forms.form_id == form_id))
    profession_ids = select(FormsProfessions.profession_id).where(FormsProfessions.form_id == form_id)
    profession_titles = (await session.scalars(
        select(Professions.title).where(Professions.profession_id.in_(profession_ids))
    )).all()
    direction_title = await session.scalar(
        select(UniversityDirections.title).where(UniversityDirections.direction_id == form.direction_id)
    )
    company = (await session.execute(
        select(WorkingCompanies.name, WorkingCompanies.position, ).where(WorkingCompanies.form_id == form_id))).all()
    company = None if not company else company[0]  # If no data about company set None
    languages = (await session.execute(
        select(Languages.name, Languages.level).where(Languages.form_id == form_id))).all()
    apps = (await session.execute(
        select(Applications.name, Applications.level).where(Applications.form_id == form_id))).all()
    user = await session.scalar(select(Users).where(Users.form_id == form_id))

    return Form(
        form.form_id, form.full_name, form.birth_date, form.gender, form.phonenum, profession_titles, form.address,
        form.nation, form.university_grade, direction_title, company, form.marital_status, form.driver_license,
        languages, apps, form.working_style, form.wanted_salary, form.positive_assessment, form.negative_assessment,
        form.photo_id, form.registered_at, form.updated_at, user.telegram_name, user.username, user.telegram_id
    )

# =========================================Functions to work with table Forms========================================= #


async def get_stats(session: AsyncSession):
    """  Get statistics of users and forms, exactly,
    count of registered users, registered forms and updated forms in periods:
    last day, last week, last month, last half year, last year, all time  """
    users_all_time = await session.scalar(select(func.count(Users.telegram_id)))
    users_one_day = await session.scalar(
        select(func.count(Users.telegram_id)).where(Users.registered_at >= datetime.now() - timedelta(hours=24))
    )
    users_one_week = await session.scalar(
        select(func.count(Users.telegram_id)).where(Users.registered_at >= datetime.now() - timedelta(days=7))
    )
    users_one_month = await session.scalar(
        select(func.count(Users.telegram_id)).where(Users.registered_at >= datetime.now() - timedelta(days=30))
    )
    users_half_year = await session.scalar(
        select(func.count(Users.telegram_id)).where(Users.registered_at >= datetime.now() - timedelta(days=183))
    )
    users_one_year = await session.scalar(
        select(func.count(Users.telegram_id)).where(Users.registered_at >= datetime.now() - timedelta(days=365))
    )
    forms_all_time = await session.scalar(select(func.count(Forms.form_id)))
    forms_one_day = await session.scalar(
        select(func.count(Forms.form_id)).where(Forms.registered_at >= datetime.now() - timedelta(hours=24))
    )
    forms_one_week = await session.scalar(
        select(func.count(Forms.form_id)).where(Forms.registered_at >= datetime.now() - timedelta(days=7))
    )
    forms_one_month = await session.scalar(
        select(func.count(Forms.form_id)).where(Forms.registered_at >= datetime.now() - timedelta(days=30))
    )
    forms_half_year = await session.scalar(
        select(func.count(Forms.form_id)).where(Forms.registered_at >= datetime.now() - timedelta(days=183))
    )
    forms_one_year = await session.scalar(
        select(func.count(Forms.form_id)).where(Forms.registered_at >= datetime.now() - timedelta(days=365))
    )
    updated_forms_all_time = await session.scalar(select(func.count(Forms.form_id)).where(
        Forms.updated_at.is_not(None)))
    updated_forms_one_day = await session.scalar(
        select(func.count(Forms.form_id)).where(Forms.updated_at >= datetime.now() - timedelta(hours=24))
    )
    updated_forms_one_week = await session.scalar(
        select(func.count(Forms.form_id)).where(Forms.updated_at >= datetime.now() - timedelta(days=7))
    )
    updated_forms_one_month = await session.scalar(
        select(func.count(Forms.form_id)).where(Forms.updated_at >= datetime.now() - timedelta(days=30))
    )
    updated_forms_half_year = await session.scalar(
        select(func.count(Forms.form_id)).where(Forms.updated_at >= datetime.now() - timedelta(days=183))
    )
    updated_forms_one_year = await session.scalar(
        select(func.count(Forms.form_id)).where(Forms.updated_at >= datetime.now() - timedelta(days=365))
    )
    stats = {"users_all_time": users_all_time, "users_one_day": users_one_day, "users_one_week": users_one_week,
             "users_one_month": users_one_month, "users_half_year": users_half_year, "users_one_year": users_one_year,
             "forms_all_time": forms_all_time, "forms_one_day": forms_one_day, "forms_one_week": forms_one_week,
             "forms_one_month": forms_one_month, "forms_half_year": forms_half_year, "forms_one_year": forms_one_year,
             "updated_forms_all_time": updated_forms_all_time, "updated_forms_one_day": updated_forms_one_day,
             "updated_forms_one_week": updated_forms_one_week, "updated_forms_one_month": updated_forms_one_month,
             "updated_forms_half_year": updated_forms_half_year, "updated_forms_one_year": updated_forms_one_year}
    return stats

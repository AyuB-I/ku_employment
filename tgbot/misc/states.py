from aiogram.filters.state import StatesGroup, State


class AdminStates(StatesGroup):
    admin_mode = State()
    forms = State()
    stats = State()
    mailing_target_categories = State()
    mailing_target = State()
    mailing_user_id = State()
    mailing_text = State()
    mailing_confirm = State()


class ProfessionStates(StatesGroup):
    asking_title = State()
    waiting_for_confirmation = State()
    showing_professions_list = State()
    deleting_profession = State()


class DirectionStates(StatesGroup):
    asking_title = State()
    waiting_for_confirmation = State()
    showing_directions_list = State()
    deleting_direction = State()


class FormFillingStates(StatesGroup):
    q1_name = State()
    q2_birth_date = State()
    q3_gender = State()
    q4_phonenum = State()
    q5_professions = State()
    q6_address = State()
    q7_nation = State()
    q8_university_grade = State()
    q9_university_direction = State()
    q10_working_company = State()
    company_name = State()
    company_position = State()
    q11_marital_status = State()
    q12_driver_license = State()
    q13_ru_lang = State()
    q14_eng_lang = State()
    q15_other_lang = State()
    lang_name = State()
    lang_level = State()
    q16_word_app = State()
    q17_excel_app = State()
    q18_1c_app = State()
    q19_other_app = State()
    app_name = State()
    app_level = State()
    q20_working_style = State()
    q21_salary = State()
    q22_positive_assessment = State()
    q23_negative_assessment = State()
    q24_photo = State()
    ready_form = State()


class FeedbackStates(StatesGroup):
    asking_text = State()
    asking_contact = State()
    waiting_for_confirmation = State()



from aiogram.filters.callback_data import CallbackData
from typing import Union, Optional


class MainCallbackFactory(CallbackData, prefix="main"):
    action: Optional[str]
    data: Union[int, str, bool, None]
    counter: int = 0

from aiogram import Bot, types


async def setup_default_commands(bot: Bot):
    await bot.set_my_commands(
        commands=[
            types.BotCommand(command="start", description="\U0001F504 Botni qayta yuklash"),
            types.BotCommand(command="help", description="\U0001F198 Yordam")
        ]
    )

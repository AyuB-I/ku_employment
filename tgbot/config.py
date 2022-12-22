from dataclasses import dataclass
from environs import Env
from sqlalchemy.engine.url import URL


@dataclass
class DBConfig:
    user: str
    password: str
    host: str
    port: int
    database: str
    pg_password: str

    # We provide a method to create a connection string easily
    def construct_sqlalchemy_url(self, driver="postgresql+asyncpg") -> URL:
        return URL.create(
            drivername=driver,
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database
        )


@dataclass
class TgBot:
    bot_token: str
    admins: list[int]
    forms_group: int
    feedbacks_group: int
    use_redis: bool
    redis_url: str


@dataclass
class Miscellaneous:
    other_params: str = None


@dataclass
class Config:
    tgbot: TgBot
    db: DBConfig
    misc: Miscellaneous


def load_config(path: str = None):
    env = Env()
    env.read_env(path)

    return Config(
        tgbot=TgBot(
            bot_token=env.str("BOT_TOKEN"),
            admins=list(map(int, env.list("ADMINS"))),
            forms_group=env.int("FORMS_GROUP"),
            feedbacks_group=env.int("FEEDBACKS_GROUP"),
            use_redis=env.bool("USE_REDIS"),
            redis_url=env.str("REDIS_URL")
        ),
        db=DBConfig(
            user=env.str('DB_USER'),
            password=env.str('DB_PASS'),
            host=env.str('DB_HOST'),
            port=env.int('DB_PORT'),
            database=env.str('DB_NAME'),
            pg_password=env.str('PG_PASS')
        ),
        misc=Miscellaneous()
    )

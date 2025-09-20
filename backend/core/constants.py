DEFAULT_ALLOWED_HOSTS = "localhost,127.0.0.1"
DEFAULT_CSRF_TRUSTED_ORIGINS = "http://localhost,http://127.0.0.1"
DEFAULT_PAGE_SIZE = 6
DEFAULT_SQLITE_DB_NAME = "db.sqlite3"

INGREDIENT_NAME_MAX_LENGTH = 128
INGREDIENT_UNIT_MAX_LENGTH = 64

RECIPE_NAME_MAX_LENGTH = 256
SHORT_LINK_CODE_MAX_LENGTH = 16

COOKING_TIME_MIN = 1
COOKING_TIME_MAX = 1440

INGREDIENT_AMOUNT_MIN = 1
INGREDIENT_AMOUNT_MAX = 2_147_483_647

USERNAME_MAX_LENGTH = 150
USER_FIRST_NAME_MAX_LENGTH = 150
USER_LAST_NAME_MAX_LENGTH = 150

COOKING_TIME_MIN_MESSAGE = (
    "Время приготовления не может быть меньше {value} минуты."
)
COOKING_TIME_MAX_MESSAGE = (
    "Время приготовления не может превышать {value} минут."
)
INGREDIENT_MIN_MESSAGE = "Количество не может быть меньше {value}."
INGREDIENT_MAX_MESSAGE = "Количество не может превышать {value}."
USERNAME_HELP_TEXT_TEMPLATE = (
    "Обязательное поле. Не более {limit_value} символов."
)
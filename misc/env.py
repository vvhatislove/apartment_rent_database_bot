import os.path

from dotenv import load_dotenv


class EnvironmentVariable:
    BOT_TOKEN = None
    FIRST_ADMIN_ID = None
    FIRST_ADMIN_NAME = None

    @classmethod
    def load_env_vars(cls):
        cls._check_existing_env_file()
        cls.BOT_TOKEN = os.getenv('BOT_TOKEN')
        cls.FIRST_ADMIN_ID = os.getenv('FIRST_ADMIN_ID')
        cls.FIRST_ADMIN_NAME = os.getenv('FIRST_ADMIN_NAME')

    @staticmethod
    def _check_existing_env_file():
        path = '.env'
        if os.path.exists(path):
            load_dotenv(path)
        else:
            raise Exception('There is no file ".env" in root directory')

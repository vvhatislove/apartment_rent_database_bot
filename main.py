import os.path

from setup_bot import start_bot
from database import setup_db
import asyncio

from misc.env import EnvironmentVariable

if __name__ == '__main__':
    if not os.path.exists('./doc_images'):
        os.mkdir('./doc_images')
    EnvironmentVariable.load_env_vars()
    setup_db()
    start_bot()

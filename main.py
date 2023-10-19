from setup_bot import start_bot
from database import setup_db
import asyncio

from misc.env import EnvironmentVariable

if __name__ == '__main__':
    EnvironmentVariable.load_env_vars()
    asyncio.run(setup_db())
    start_bot()

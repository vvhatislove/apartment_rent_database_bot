from database.db import Database
from database.models import *
from misc.env import EnvironmentVariable


async def setup_db():
    db = Database()
    await db.create_tables([
        User,
        Apartment,
        Client,
        PhoneNumber,
        Lease
    ])

    first_admin_id = EnvironmentVariable.FIRST_ADMIN_ID
    first_admin_name = EnvironmentVariable.FIRST_ADMIN_NAME

    await db.create_user_if_not_exist(first_admin_name, first_admin_id, True)

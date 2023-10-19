from database.methods import DatabaseCreateMethods, DatabaseInsertMethods
from misc.env import EnvironmentVariable


async def setup_db():
    db_create = DatabaseCreateMethods()
    await db_create.create_user_table()

    db_insert = DatabaseInsertMethods()
    first_admin_id = EnvironmentVariable.FIRST_ADMIN_ID
    first_admin_name = EnvironmentVariable.FIRST_ADMIN_NAME

    await db_insert.add_user_if_not_exists(first_admin_name, first_admin_id, True)

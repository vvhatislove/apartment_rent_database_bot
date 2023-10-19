import aiosqlite

from database.models import User


class Database:
    def __init__(self, db_path='database/apartment_rent.db'):
        self.db_path = db_path


class DatabaseCreateMethods(Database):
    async def create_user_table(self):
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.cursor()
            create_table_sql = '''
                CREATE TABLE IF NOT EXISTS user (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    tg_user_id INTEGER,
                    is_admin BOOLEAN
                )
            '''
            await cur.execute(create_table_sql)
            await conn.commit()


class DatabaseInsertMethods(Database):
    async def add_user_if_not_exists(self, name, tg_user_id, is_admin):
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.cursor()

            # Проверяем, существует ли пользователь с таким tg_user_id
            check_user_sql = 'SELECT id FROM user WHERE tg_user_id = ?'
            await cur.execute(check_user_sql, (tg_user_id,))
            existing_user = await cur.fetchone()

            # Если пользователь не существует, добавляем его
            if existing_user is None:
                insert_user_sql = 'INSERT INTO user (name, tg_user_id, is_admin) VALUES (?, ?, ?)'
                await cur.execute(insert_user_sql, (name, tg_user_id, is_admin))
                await conn.commit()


class DatabaseGetMethods(Database):
    async def get_user_by_tg_user_id(self, tg_user_id):
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.cursor()

            # Проверяем, существует ли пользователь с таким tg_user_id
            check_user_sql = 'SELECT id, name, tg_user_id, is_admin FROM user WHERE tg_user_id = ?'
            await cur.execute(check_user_sql, (tg_user_id,))
            user_data = await cur.fetchone()

            if user_data is not None:
                id_, name, tg_user_id, is_admin = user_data
                return User(id_, name, tg_user_id, is_admin)
            else:
                return None

    async def get_all_users(self):
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.cursor()

            # Выбираем всех пользователей из таблицы user
            select_all_users_sql = 'SELECT id, name, tg_user_id, is_admin FROM user'
            await cur.execute(select_all_users_sql)
            user_data_list = await cur.fetchall()

            users = []
            for user_data in user_data_list:
                id_, name, tg_user_id, is_admin = user_data
                users.append(User(id_, name, tg_user_id, is_admin))

            return users


class DatabaseDeleteMethods(Database):
    async def delete_user_by_id(self, user_id):
        async with aiosqlite.connect(self.db_path) as conn:
            cur = await conn.cursor()

            # Удаляем пользователя по идентификатору
            delete_user_sql = 'DELETE FROM user WHERE id = ?'
            await cur.execute(delete_user_sql, (user_id,))
            await conn.commit()

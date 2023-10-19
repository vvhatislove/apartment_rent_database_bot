from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from database.models import User


class Database:
    def __init__(self, db_url='sqlite+aiosqlite:///database/apartment_rent.db'):
        self.engine = create_async_engine(db_url, echo=True)
        self.Session = sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def create_tables(self, models):
        async with self.engine.begin() as conn:
            for model in models:
                await conn.run_sync(model.metadata.create_all)

    async def create_user_if_not_exist(self, name, tg_user_id, is_admin):
        async with self.Session() as session:
            stmt = select(User).filter_by(tg_user_id=tg_user_id)
            existing_user = await session.execute(stmt)
            existing_user = existing_user.scalars().first()

            if not existing_user:
                user = User(name=name, tg_user_id=tg_user_id, is_admin=is_admin)
                session.add(user)
                await session.commit()

    async def get_user_by_tg_user_id(self, tg_user_id):
        async with self.Session() as session:
            stmt = select(User).filter_by(tg_user_id=tg_user_id)
            result = await session.execute(stmt)
            user = result.scalars().first()
            return user

    async def get_all_users(self):
        async with self.Session() as session:
            stmt = select(User)
            result = await session.execute(stmt)
            users = result.scalars().all()
            return users

    async def delete_user_by_id(self, user_id):
        async with self.Session() as session:
            stmt = select(User).filter_by(id=user_id)
            result = await session.execute(stmt)
            user = result.scalars().first()
            if user:
                session.delete(user)
                await session.commit()

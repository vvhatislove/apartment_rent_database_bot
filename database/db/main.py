from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy.future import select

from database.models import User, Apartment, Client, PhoneNumber, Document


class Database:
    def __init__(self, db_url='sqlite+aiosqlite:///database/apartment_rent.db'):
        self.engine = create_async_engine(db_url, echo=False)
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

    async def get_all_apartments(self):
        async with self.Session() as session:
            stmt = select(Apartment)
            result = await session.execute(stmt)
            apartments = result.scalars().all()
            return apartments

    async def get_client_by_phone_number(self, phone_number):
        async with self.Session() as session:
            # Используем selectinload для загрузки связанных номеров телефонов
            result = await session.execute(
                select(Client).options(selectinload(Client.phone_numbers)).join(PhoneNumber).filter(
                    PhoneNumber.number == phone_number)
            )
            client = result.scalar()
            return client

    async def add_client(self, name, phone_numbers, document_filenames):
        async with self.Session() as session:
            # Создаем нового клиента
            new_client = Client(name=name)

            # Создаем номера телефонов и связываем их с клиентом
            for phone_number in phone_numbers:
                new_phone_number = PhoneNumber(number=phone_number)
                new_phone_number.client = new_client

            # Создаем фотографии документов и связываем их с клиентом
            for document_filename in document_filenames:
                new_document = Document(filename=document_filename)
                new_document.client = new_client

            # Добавляем клиента и связанные с ним записи в базу данных
            session.add(new_client)
            await session.commit()

from datetime import datetime

from sqlalchemy import create_engine, or_, and_, func
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker, joinedload
from database.models.main import User, Apartment, Client, PhoneNumber, Document, Lease, Blacklist
from sqlalchemy.orm import selectinload


class Database:
    def __init__(self, db_url='sqlite:///database/apartment_rent.db'):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(self.engine)

    def create_tables(self, models):
        with self.engine.connect() as conn:
            for model in models:
                model.metadata.create_all(conn, checkfirst=True)

    def create_user_if_not_exist(self, name, tg_user_id, is_admin):
        with self.Session() as session:
            existing_user = session.query(User).filter_by(tg_user_id=tg_user_id).first()

            if not existing_user:
                user = User(name=name, tg_user_id=tg_user_id, is_admin=is_admin)
                session.add(user)
                session.commit()

    def get_user_by_tg_user_id(self, tg_user_id):
        with self.Session() as session:
            user = session.query(User).filter_by(tg_user_id=tg_user_id).first()
            return user

    def get_all_users(self):
        with self.Session() as session:
            users = session.query(User).all()
            return users

    def delete_user_by_id(self, user_id):
        with self.Session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                session.delete(user)
                session.commit()

    def get_all_apartments(self):
        with self.Session() as session:
            apartments = session.query(Apartment).all()
            return apartments

    def get_client_by_phone_number(self, phone_number):
        with self.Session() as session:
            client = (
                session.query(Client)
                .options(joinedload(Client.phone_numbers),
                         joinedload(Client.documents))
                .join(PhoneNumber)
                .filter(PhoneNumber.number == phone_number)
                .first()
            )
            return client

    def add_client(self, name, phone_numbers, document_filenames):
        with self.Session() as session:
            new_client = Client(name=name)

            for phone_number in phone_numbers:
                new_phone_number = PhoneNumber(number=phone_number)
                new_phone_number.client = new_client

            for document_filename in document_filenames:
                new_document = Document(filename=document_filename)
                new_document.client = new_client

            session.add(new_client)
            session.commit()
            return new_client.id

    def add_apartment(self, address):
        with self.Session() as session:
            new_apartment = Apartment(address=address)
            session.add(new_apartment)
            session.commit()
            return new_apartment.id

    def add_lease(self, client_id, apartment_id, start_date, end_date, rent_amount, deposit,
                  additional_details, is_deposit_paid):
        with self.Session() as session:
            new_lease = Lease(
                client_id=client_id,
                apartment_id=apartment_id,
                start_date=start_date,
                end_date=end_date,
                rent_amount=rent_amount,
                deposit=deposit,
                additional_details=additional_details,
                is_deposit_paid=is_deposit_paid
            )
            session.add(new_lease)
            session.commit()
            return new_lease.id

    def get_lease_by_id(self, lease_id):
        with self.Session() as session:
            return (
                session.query(Lease)
                .options(
                    joinedload(Lease.client).joinedload(Client.phone_numbers),
                    joinedload(Lease.client).joinedload(Client.documents),
                    joinedload(Lease.apartment),
                )
                .filter_by(id=lease_id)
                .first()
            )

    def search_leases(self, phone_number=None, address=None, start_date=None, end_date=None, is_deposit_paid=None):
        with self.Session() as session:
            query = session.query(Lease).join(Client).join(Apartment)

            if phone_number:
                query = query.filter(Client.phone_numbers.any(PhoneNumber.number == phone_number))

            if address:
                query = query.filter(Apartment.address == address)

            if start_date is not None:
                # Учитываем только дату, игнорируя время
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                query = query.filter(Lease.start_date >= start_date)

            if end_date:
                query = query.filter(Lease.end_date <= end_date)

            if is_deposit_paid is not None:
                query = query.filter(Lease.is_deposit_paid == is_deposit_paid)
                query = query.filter(Lease.deposit > 0.0)

            # Добавлен фильтр для дат, которые больше или равны текущей дате
            query = query.filter(Lease.start_date >= datetime.utcnow())

            leases = (
                query.options(
                    joinedload(Lease.client).joinedload(Client.phone_numbers),
                    joinedload(Lease.client).joinedload(Client.documents),
                    joinedload(Lease.apartment),
                )
                .all()
            )

            return leases

    def update_lease(self, lease_id, **kwargs):
        with self.Session() as session:
            try:
                lease = session.query(Lease).filter_by(id=lease_id).one()
                for key, value in kwargs.items():
                    setattr(lease, key, value)
                session.commit()
                return True  # Успешное обновление
            except NoResultFound:
                return False  # Запись с указанным ID не найдена

    def get_lease_id_by_date_time_range(self, apartment_id, start_datetime, end_datetime):
        with self.Session() as session:
            with session.begin():
                overlapping_lease = session.query(Lease).filter(
                    Lease.apartment_id == apartment_id,
                    or_(
                        and_(Lease.start_date <= start_datetime, Lease.end_date >= start_datetime),
                        and_(Lease.start_date <= end_datetime, Lease.end_date >= end_datetime),
                        and_(Lease.start_date >= start_datetime, Lease.end_date <= end_datetime),
                    )
                ).first()
                if overlapping_lease:
                    return overlapping_lease.id
                else:
                    return None

    def get_available_leases_today(self):
        today = datetime.today()
        midnight_start = datetime.combine(today, datetime.min.time())
        midnight_end = datetime.combine(today, datetime.max.time())

        with self.Session() as session:
            leases = (
                session.query(Lease)
                .options(joinedload(Lease.client).joinedload(Client.phone_numbers),
                         joinedload(Lease.client).joinedload(Client.documents),
                         joinedload(Lease.apartment))
                .filter(
                    Lease.start_date <= midnight_end,
                    Lease.end_date >= midnight_start,
                )
                .all()
            )

            return leases

    def update_client(self, client_id, name=None, phone_numbers=None, document_filenames=None):
        with self.Session() as session:
            client = session.query(Client).get(client_id)

            if client:
                if name:
                    client.name = name

                if phone_numbers:
                    # Предполагается, что phone_numbers - это список номеров телефонов
                    client.phone_numbers = [PhoneNumber(number=number, client=client) for number in phone_numbers]

                if document_filenames:
                    # Предполагается, что document_filenames - это список имен файлов документов
                    client.documents = [Document(filename=filename, client=client) for filename in document_filenames]

                session.commit()
                return True
            else:
                return False

    def add_to_blacklist(self, client_id, comment):
        with self.Session() as session:
            blacklist_entry = Blacklist(client_id=client_id, comment=comment)
            session.add(blacklist_entry)
            session.commit()

    def remove_from_blacklist(self, client_id):
        with self.Session() as session:
            entry = session.query(Blacklist).filter_by(client_id=client_id).first()
            if entry:
                session.delete(entry)
                session.commit()

    def get_blacklist_entry(self, client_id):
        with self.Session() as session:
            return session.query(Blacklist).filter_by(client_id=client_id).first()

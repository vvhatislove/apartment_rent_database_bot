from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from database.models.main import User, Apartment, Client, PhoneNumber, Document, Lease
from sqlalchemy.orm import selectinload


class Database:
    def __init__(self, db_url='sqlite:///database/apartment_rent.db'):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(self.engine)

    def create_tables(self, models):
        with self.engine.connect() as conn:
            for model in models:
                model.metadata.create_all(conn)

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
                .options(selectinload(Client.phone_numbers))
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
                  additional_details):
        with self.Session() as session:
            new_lease = Lease(
                client_id=client_id,
                apartment_id=apartment_id,
                start_date=start_date,
                end_date=end_date,
                rent_amount=rent_amount,
                deposit=deposit,
                additional_details=additional_details
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

    def search_leases(self, phone_number=None, address=None, start_date=None, end_date=None):
        with self.Session() as session:
            query = session.query(Lease).join(Client).join(Apartment)

            if phone_number:
                query = query.filter(Client.phone_numbers.any(PhoneNumber.number == phone_number))

            if address:
                query = query.filter(Apartment.address == address)

            if start_date:
                query = query.filter(Lease.start_date >= start_date)

            if end_date:
                query = query.filter(Lease.end_date <= end_date)

            leases = (
                query.options(
                    joinedload(Lease.client).joinedload(Client.phone_numbers),
                    joinedload(Lease.client).joinedload(Client.documents),
                    joinedload(Lease.apartment),
                )
                .all()
            )

            return leases

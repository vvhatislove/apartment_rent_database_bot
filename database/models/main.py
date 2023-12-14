from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    tg_user_id = Column(Integer, unique=True)
    is_admin = Column(Boolean)


class Blacklist(Base):
    __tablename__ = 'blacklist'
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('client.id'))
    comment = Column(String)
    client = relationship('Client', back_populates='blacklist')


class Client(Base):
    __tablename__ = 'client'

    id = Column(Integer, primary_key=True)
    name = Column(String)

    # Вспомогательная таблица для хранения номеров телефонов клиента
    phone_numbers = relationship('PhoneNumber', back_populates='client')

    # Вспомогательная таблица для хранения фотографий документов клиента
    documents = relationship('Document', back_populates='client')
    blacklist = relationship('Blacklist', back_populates='client')

    # Связь с таблицей аренды
    leases = relationship('Lease', back_populates='client')


class PhoneNumber(Base):
    __tablename__ = 'phone_number'

    id = Column(Integer, primary_key=True)
    number = Column(String)

    # Связь с таблицей Client
    client_id = Column(Integer, ForeignKey('client.id'))
    client = relationship('Client', back_populates='phone_numbers')


class Document(Base):
    __tablename__ = 'document'

    id = Column(Integer, primary_key=True)
    filename = Column(String)

    # Связь с таблицей Client
    client_id = Column(Integer, ForeignKey('client.id'))
    client = relationship('Client', back_populates='documents')


class Lease(Base):
    __tablename__ = 'lease'

    id = Column(Integer, primary_key=True)
    # Добавьте поля, связанные с информацией об аренде
    start_date = Column(DateTime, default=datetime.utcnow)  # Добавление даты начала аренды
    end_date = Column(DateTime, default=datetime.utcnow)  # Добавление даты окончания аренды
    rent_amount = Column(Float)  # Сумма арендной платы
    deposit = Column(Float)  # Сумма залога
    additional_details = Column(Text)  # Дополнительные детали
    created_at = Column(DateTime, default=datetime.utcnow)  # Дата создания записи о аренде
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)  # Дата последнего обновления записи о аренде
    is_deposit_paid = Column(Boolean, default=False)
    is_inhabited = Column(Boolean, default=False)
    # Связь с таблицей Client
    client_id = Column(Integer, ForeignKey('client.id'))
    client = relationship('Client', back_populates='leases')

    # Связь с таблицей Apartment
    apartment_id = Column(Integer, ForeignKey('apartment.id'))
    apartment = relationship('Apartment', back_populates='leases')


class Apartment(Base):
    __tablename__ = 'apartment'

    id = Column(Integer, primary_key=True)
    address = Column(String)

    # Связь с таблицей аренды
    leases = relationship('Lease', back_populates='apartment')

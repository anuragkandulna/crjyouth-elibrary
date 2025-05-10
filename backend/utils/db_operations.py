### utils/db_operations.py

from sqlalchemy.orm import Session
from models.user_role import UserRole
from models.library_membership import LibraryMembership
from models.author import Author
from models.publisher import Publisher
from models.library_office import LibraryOffice
from utils.my_logger import CustomLogger
from constants.constants import OPS_LOG_FILE
from constants.config import LOG_LEVEL


LOGGER = CustomLogger(__name__, level=LOG_LEVEL, log_file=OPS_LOG_FILE).get_logger()


def seed_roles(session: Session, predefined_roles: dict) -> None:
    """
    Core logic to seed user_roles.
    """
    inserted_count = 0
    for rank, (role_name, permissions) in predefined_roles.items():
        existing = session.query(UserRole).filter_by(rank=rank).first()
        if existing:
            LOGGER.info(f"ℹ️ Role '{role_name}' already exists, skipping.")
            continue

        new_role = UserRole(rank=rank, role=role_name, permissions=permissions)
        session.add(new_role)
        inserted_count += 1

    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new role(s).")
    else:
        LOGGER.info("✅ No new roles inserted. All roles already exist.")


def seed_memberships(session: Session, predefined_memberships: dict) -> None:
    """
    Core logic to seed library_memberships.
    """
    inserted_count = 0
    for rank, (membership, reg_fee, book_limit, days_count) in predefined_memberships.items():
        existing = session.query(LibraryMembership).filter_by(rank=rank).first()
        if existing:
            LOGGER.info(f"ℹ️ Membership class '{membership}' already exists, skipping.")
            continue

        new_membership = LibraryMembership(
            rank=rank,
            membership_title=membership,
            borrowing_limit=book_limit,
            borrow_duration_days=days_count,
            annual_fee=reg_fee
        )
        session.add(new_membership)
        inserted_count += 1

    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new membership(s).")
    else:
        LOGGER.info("✅ No new memberships inserted. All memberships already exist.")


# def seed_authors(session: Session, predefined_authors: dict) -> None:
#     """
#     Core logic to seed authors.
#     """
#     inserted_count = 0
#     for code, name in predefined_authors.items():
#         existing = session.query(Author).filter_by(code=code).first()
#         if existing:
#             LOGGER.info(f"ℹ️ Author with code '{code}' already exists: {existing.name}, skipping.")
#             continue

#         new_author = Author(code=code, name=name)
#         session.add(new_author)
#         inserted_count += 1

#     if inserted_count > 0:
#         session.commit()
#         LOGGER.info(f"✅ Seeded {inserted_count} new author(s).")
#     else:
#         LOGGER.info("✅ No new authors inserted. All authors already exist.")


# def seed_publishers(session: Session, predefined_publishers: dict) -> None:
#     """
#     Core logic to seed publishers.
#     """
#     inserted_count = 0
#     for code, name in predefined_publishers.items():
#         existing = session.query(Publisher).filter_by(code=code).first()
#         if existing:
#             LOGGER.info(f"ℹ️ Publisher with code '{code}' already exists: {existing.name}, skipping.")
#             continue

#         new_publisher = Publisher(code=code, name=name)
#         session.add(new_publisher)
#         inserted_count += 1

#     if inserted_count > 0:
#         session.commit()
#         LOGGER.info(f"✅ Seeded {inserted_count} new publisher(s).")
#     else:
#         LOGGER.info("✅ No new publishers inserted. All publishers already exist.")


def seed_library_offices(session: Session, predefined_offices: dict) -> None:
    """
    Core logic to seed library_offices table.
    :param session: Active SQLAlchemy session.
    :param predefined_offices: List of office dictionaries with office_code, city, state, country, pincode.
    """
    inserted_count = 0

    for key, (address, city, state, country, pincode) in predefined_offices.items():
        existing = session.query(LibraryOffice).filter_by(office_code=key).first()
        if existing:
            LOGGER.info(f"ℹ️ Library Office '{key}' already exists in '{city}', skipping.")
            continue

        new_office = LibraryOffice(
            office_code=key,
            address=address,
            city=city,
            state=state,
            country=country,
            pincode=pincode
        )
        session.add(new_office)
        inserted_count += 1

    if inserted_count > 0:
        session.commit()
        LOGGER.info(f"✅ Seeded {inserted_count} new library office(s).")
    else:
        LOGGER.info("✅ No new library offices inserted. All offices already exist.")

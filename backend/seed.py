from utils.psql_database import db_session
from models.library_user import UserRole

def seed_roles():
    """
    Seed the user_roles table with default roles and permissions.
    Will not overwrite or re-insert if the roles already exist.
    """
    # session = get_session()
    try:
        # Define role data
        predefined_roles = {
            1: ("Admin", [
                "add_book", "edit_book", "delete_book", "approve_lending", "manage_users"
            ]),
            2: ("Moderator", [
                "approve_lending", "manage_threads", "resolve_issues"
            ]),
            3: ("Member", [
                "borrow_book", "return_book", "suggest_book", "participate_threads"
            ]),
        }

        inserted_count = 0
        for rank, (role_name, permissions) in predefined_roles.items():
            existing = db_session.query(UserRole).filter_by(rank=rank).first()
            if existing:
                print(f"ℹ️ Role '{role_name}' already exists, skipping.")
                continue

            new_role = UserRole(rank=rank, role=role_name, permissions=permissions)
            db_session.add(new_role)
            inserted_count += 1

        if inserted_count > 0:
            db_session.commit()
            print(f"✅ Seeded {inserted_count} new role(s).")
        else:
            print("✅ No new roles inserted. All roles already exist.")

    except Exception as e:
        db_session.rollback()
        print(f"❌ Error during seeding: {e}")
    finally:
        db_session.close()

if __name__ == "__main__":
    seed_roles()

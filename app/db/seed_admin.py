import argparse

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.auth import UserRole, WebUser
from sqlalchemy import func, select


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the first admin web user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--full-name", default="Admin")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        count = db.scalar(select(func.count(WebUser.user_id))) or 0
        if count:
            print("Users already exist. Use POST /auth/users as ADMIN instead.")
            return

        user = WebUser(
            email=args.email.lower(),
            password_hash=hash_password(args.password),
            full_name=args.full_name,
            role=UserRole.ADMIN.value,
        )
        db.add(user)
        db.commit()
        print(f"Admin user created: {user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

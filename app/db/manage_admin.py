import argparse

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.auth import UserRole, WebUser


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or reset a website admin user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--full-name", default="Admin")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        email = args.email.lower()
        user = db.scalar(select(WebUser).where(WebUser.email == email))

        if user is None:
            user = WebUser(
                email=email,
                password_hash=hash_password(args.password),
                full_name=args.full_name,
                role=UserRole.ADMIN.value,
            )
            db.add(user)
            db.commit()
            print(f"Created admin user: {email}")
            return

        user.password_hash = hash_password(args.password)
        user.full_name = args.full_name
        user.role = UserRole.ADMIN.value
        user.is_active = True
        db.commit()
        print(f"Updated admin user: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

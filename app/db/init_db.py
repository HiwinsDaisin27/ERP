from app.db.base import Base
from app.db.session import engine
from app.models import auth, construction, payroll, telegram
from sqlalchemy import text


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS image_url VARCHAR(500)"))
    print("Database tables created.")


if __name__ == "__main__":
    main()

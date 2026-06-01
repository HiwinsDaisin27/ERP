from app.db.base import Base
from app.db.session import engine
from app.models import construction, telegram


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")


if __name__ == "__main__":
    main()


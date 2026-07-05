from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.auth import UserRole, WebUser
from app.schemas.auth import CreateUserRequest, TokenResponse, UserResponse


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.db.scalar(select(WebUser).where(WebUser.email == email.lower()))
        if user is None or not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password.")
        if not user.is_active:
            raise ValueError("This account is inactive.")

        token = create_access_token(user_id=user.user_id, email=user.email, role=user.role)
        return TokenResponse(access_token=token, user=self._to_user_response(user))

    def bootstrap_admin(self, email: str, password: str, full_name: str) -> UserResponse:
        existing = self.db.scalar(select(func.count(WebUser.user_id)))
        if existing:
            raise ValueError("Bootstrap is only allowed when no users exist.")

        user = WebUser(
            email=email.lower(),
            password_hash=hash_password(password),
            full_name=full_name,
            role=UserRole.ADMIN.value,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return self._to_user_response(user)

    def create_user(self, payload: CreateUserRequest) -> UserResponse:
        if payload.role not in {role.value for role in UserRole}:
            raise ValueError(f"Invalid role: {payload.role}")

        existing = self.db.scalar(select(WebUser).where(WebUser.email == payload.email.lower()))
        if existing:
            raise ValueError("A user with this email already exists.")

        user = WebUser(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            role=payload.role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return self._to_user_response(user)

    @staticmethod
    def _to_user_response(user: WebUser) -> UserResponse:
        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
        )

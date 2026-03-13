import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from typing import Optional

from app.infrastructure.file_note_repo import FileNoteRepository


class AuthService:
    def __init__(
        self, file_repo: "FileNoteRepository", secret_key: str, algorithm: str
    ):
        self.file_repo = file_repo
        self.secret_key = secret_key
        self.algorithm = algorithm

    async def register_user(self, name: str, password: str):
        """
        Registers a new user and initializes their note list in the manager file.
        """
        manager = self.file_repo.load_manager_data()

        if name in manager:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
            )

        manager[name] = {"password": password, "notes": []}
        self.file_repo.save_manager_data(manager)
        return name

    async def login(self, name: str, password: str) -> str:
        """
        Validates credentials and returns a JWT token.
        """
        manager = self.file_repo.load_manager_data()
        user = manager.get(name)

        if not user or user["password"] != password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        # Prepare JWT payload (using your old 35-minute expiration logic)
        payload = {"iss": name, "exp": datetime.utcnow() + timedelta(minutes=35)}

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> str:
        """
        Decodes the JWT and returns the username (subject).
        """
        if not token:
            raise HTTPException(status_code=401, detail="Missing token")

        # Clean the Bearer prefix if present
        if token.startswith("Bearer "):
            token = token.split(" ")[1]

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload["iss"]
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

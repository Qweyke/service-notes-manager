from dependency_injector import containers, providers
import redis.asyncio as redis
from app.infrastructure.file_note_repo import FileNoteRepository
from app.infrastructure.redis_repo import RedisRepository
from app.services.auth_service import AuthService
from app.services.notes_service import NotesService


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    config.secret_key.from_value("MyKey0377")
    config.algorithm.from_value("HS256")

    redis_client = providers.Singleton(
        redis.Redis,
        host="redis",
        port=6379,
        decode_responses=True,
    )

    redis_repo = providers.Singleton(RedisRepository, client=redis_client)

    file_repo = providers.Singleton(
        FileNoteRepository,
        notes_path="./server/notes",
        manager_path="./server/user_manager.json",
    )

    # 3. Services
    auth_service = providers.Singleton(
        AuthService,
        file_repo=file_repo,
        secret_key=config.secret_key,
        algorithm=config.algorithm,
    )

    notes_service = providers.Singleton(
        NotesService, file_repo=file_repo, redis_repo=redis_repo
    )

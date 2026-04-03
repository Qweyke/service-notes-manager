from app.infrastructure.redis_repo import RedisRepository
from fastapi import APIRouter, Depends, Header, HTTPException
from dependency_injector.wiring import inject, Provide


from app.containers import Container
from app.services.notes_service import NotesService
from app.services.auth_service import AuthService
from app.domain import models

app_router = APIRouter()


# --- Security Dependency ---
@inject
def get_current_user(
    authorization: str = Header(None),
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
) -> str:
    """
    Dependency that extracts the username from the JWT token.
    Replaces the old manual 'server.__verify_jwt(token)' calls.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    return auth_service.verify_token(authorization)


# --- Routes ---
@app_router.post("/users/register", response_model=models.RegisterUserResponse)
@inject
async def register_user(
    request_body: models.RegisterUser,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
):
    # Using AuthService to handle registration logic
    name = await auth_service.register_user(request_body.name, request_body.password)
    return models.RegisterUserResponse(info="Registered", name=name)


@app_router.get("/users/authorize", response_model=models.LogInResponse)
@inject
async def log_in(
    request_body: models.LogIn,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),
):
    # Generating JWT using the new centralized service
    token = await auth_service.login(request_body.name, request_body.password)
    return models.LogInResponse(name=request_body.name, token=token)


@app_router.post("/notes/new/{note_id}", response_model=models.CreateNoteResponse)
@inject
async def create_note(
    note_id: int,
    request_body: models.CreateNote,
    user_name: str = Depends(get_current_user),  # Identity is now pre-verified
    notes_service: NotesService = Depends(Provide[Container.notes_service]),
):
    # Logic now coordinated by NotesService (File + Redis)
    await notes_service.add_note(user_name, note_id, request_body.text)
    return models.CreateNoteResponse(id=note_id, name=user_name)


@app_router.get("/notes/text/{note_id}", response_model=models.GetNoteTextResponse)
@inject
async def get_note_text(
    note_id: int,
    user_name: str = Depends(get_current_user),
    notes_service: NotesService = Depends(Provide[Container.notes_service]),
):
    # Implementation of Cache-Aside (Hit/Miss) is hidden inside the service
    result = await notes_service.get_note_text(user_name, note_id)
    if not result:
        raise HTTPException(status_code=404, detail="Note not found")
    return models.GetNoteTextResponse(id=note_id, text=result["text"])


@app_router.delete("/notes/delete/{note_id}", response_model=models.DeleteNoteResponse)
@inject
async def delete_note(
    note_id: int,
    user_name: str = Depends(get_current_user),
    notes_service: NotesService = Depends(Provide[Container.notes_service]),
):
    # Full cleanup: Files + Redis Metadata + Redis Cache
    await notes_service.delete_note(user_name, note_id)
    return models.DeleteNoteResponse(id=note_id, name=user_name)


# --- Redis Direct Access Routes ---


@app_router.post("/redis/string")
@inject
async def redis_set_string(
    key: str,
    value: str,
    ttl: int | None = None,
    user_name: str = Depends(get_current_user),  # Опционально: только для залогиненных
    redis_repo: RedisRepository = Depends(Provide[Container.redis_repo]),
):
    """Directly set a string value in Redis."""
    await redis_repo.set_string(key, value, ttl)
    return {"status": "ok", "key": key}


@app_router.get("/redis/string/{key}")
@inject
async def redis_get_string(
    key: str,
    user_name: str = Depends(get_current_user),
    redis_repo: RedisRepository = Depends(Provide[Container.redis_repo]),
):
    """Directly get a string value from Redis."""
    value = await redis_repo.get_string(key)
    return {"key": key, "value": value}


@app_router.post("/redis/list/{key}")
@inject
async def redis_list_push(
    key: str,
    value: str,
    user_name: str = Depends(get_current_user),
    redis_repo: RedisRepository = Depends(Provide[Container.redis_repo]),
):
    """Push value to a Redis list."""
    await redis_repo.list_push(key, value)
    return {"status": "pushed", "key": key}


@app_router.delete("/redis/key/{key}")
@inject
async def redis_delete_key(
    key: str,
    user_name: str = Depends(get_current_user),
    redis_repo: RedisRepository = Depends(Provide[Container.redis_repo]),
):
    """Delete any key from Redis."""
    await redis_repo.delete(key)
    return {"status": "deleted", "key": key}

from datetime import datetime
from typing import Optional, Dict, Any

from app.infrastructure.file_note_repo import FileNoteRepository
from app.infrastructure.redis_repo import RedisRepository


class NotesService:
    def __init__(self, file_repo: FileNoteRepository, redis_repo: RedisRepository):
        self.file_repo = file_repo
        self.redis_repo = redis_repo

    async def add_note(self, user_name: str, note_id: int, text: str):
        note_data = {
            "id": note_id,
            "text": text,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        await self.file_repo.save_note(user_name, note_id, note_data)

        manager = self.file_repo.load_manager_data()
        if user_name in manager:
            if note_id not in manager[user_name]["notes"]:
                manager[user_name]["notes"].append(int(note_id))
                self.file_repo.save_manager_data(manager)

        meta_key = f"note:{note_id}:meta"
        await self.redis_repo.hash_set_all(meta_key, {"owner": user_name, "views": 0})
        await self.redis_repo.set_ttl(meta_key, 600)
        return user_name

    async def update_note(
        self, user_name: str, note_id: int, new_text: str
    ) -> Optional[str]:
        """
        Updates note content in the filesystem and invalidates the Redis cache.
        """
        # 1. Retrieve existing data from the persistent file storage
        note_data = await self.file_repo.read_note(user_name, note_id)
        if not note_data:
            return None

        # 2. Update fields
        note_data["text"] = new_text
        note_data["updated_at"] = datetime.now().isoformat()

        # 3. Save updated data back to the file
        await self.file_repo.save_note(user_name, note_id, note_data)

        # 4. Cache Invalidation: Remove the outdated text from Redis
        # This ensures the next 'get' request triggers a Cache Miss and fetches fresh data
        await self.redis_repo.delete(f"note:{note_id}:text")

        # 5. Update metadata in Redis Hash
        await self.redis_repo.hash_set_all(
            f"note:{note_id}:meta", {"updated_at": str(note_data["updated_at"])}
        )
        return user_name

    async def delete_note(self, user_name: str, note_id: int) -> Optional[str]:
        """
        Permanently deletes a note from the filesystem and clears all associated Redis data.
        """
        # 1. Update the user manager (ownership list)
        manager = self.file_repo.load_manager_data()
        if user_name in manager:
            # Это сработает, даже если в списке были и строки, и числа
            manager[user_name]["notes"] = [
                id for id in manager[user_name]["notes"] if int(id) != int(note_id)
            ]
            self.file_repo.save_manager_data(manager)

        # 2. Remove the physical JSON file
        await self.file_repo.delete_note_file(user_name, note_id)

        # 3. Complete Cleanup in Redis: remove text, metadata, and view counters
        await self.redis_repo.delete(f"note:{note_id}:text")
        await self.redis_repo.delete(f"note:{note_id}:meta")
        await self.redis_repo.delete(f"note:{note_id}:views")
        return user_name

    async def get_note_info(self, user_name: str, note_id: int) -> Dict[str, Any]:
        """
        Retrieves note metadata using a hybrid approach (Redis + File fallback).
        """

        meta_key = f"note:{note_id}:meta"
        meta = await self.redis_repo.hash_get_all(meta_key)
        views = await self.redis_repo.get_string(f"note:{note_id}:views") or 0

        # 3. Fallback: If Redis is empty, recover basic info from the file
        if not meta:
            note_data = await self.file_repo.read_note(user_name, note_id)
            if not note_data:
                return {"error": "Note not found"}

            meta_to_cache = {
                "owner": user_name,
                "created_at": note_data.get("created_at", "N/A"),
                "id": str(note_id),
            }

            await self.redis_repo.hash_set_all(meta_key, meta_to_cache)
            await self.redis_repo.set_ttl(meta_key, 3600)

            meta_to_cache["views"] = int(views)
            meta_to_cache["source"] = "filesystem_recovery_and_warmed"
            return meta_to_cache

        meta["views"] = int(views)
        meta["source"] = "redis_cache"
        return meta

    async def get_note_text(
        self, user_name: str, note_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Implements the Cache-Aside pattern for retrieving note content.
        """
        cache_key = f"note:{note_id}:text"

        # 1. Attempt Cache Hit: Check if the text is already in Redis
        text = await self.redis_repo.get_string(cache_key)
        if text:
            # Atomic increment for statistics on every hit
            await self.redis_repo.increment(f"note:{note_id}:views")
            return {"text": text, "cached": True}

        # 2. Cache Miss: Fetch data from the slower filesystem
        note_data = await self.file_repo.read_note(user_name, note_id)
        if note_data:
            # 3. Populate Cache: Store the text in Redis with a TTL (e.g., 600 seconds)
            # This makes subsequent requests much faster
            await self.redis_repo.set_string(cache_key, note_data["text"], ttl=600)
            return {"text": note_data["text"], "cached": False}

        return None

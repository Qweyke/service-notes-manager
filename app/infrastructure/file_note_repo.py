import os
import json
from typing import Optional, Dict

from app.domain.models import INoteRepository


class FileNoteRepository(INoteRepository):
    def __init__(self, notes_path: str, manager_path: str):
        self.notes_path = notes_path
        self.manager_path = manager_path

        if not os.path.exists(self.notes_path):
            os.makedirs(self.notes_path)

    def load_manager_data(self) -> Dict:
        if os.path.exists(self.manager_path):
            with open(self.manager_path, "r") as f:
                return json.load(f)
        return {}

    def save_manager_data(self, data: Dict):
        with open(self.manager_path, "w") as f:
            json.dump(data, f, indent=4)

    async def save_note(self, user_name: str, note_id: int, note_data: dict):
        user_dir = os.path.join(self.notes_path, user_name)
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)

        path = os.path.join(user_dir, f"{note_id}.json")
        with open(path, "w") as f:
            json.dump(note_data, f, default=str)

    async def delete_note_file(self, user_name: str, note_id: int):
        path = os.path.join(self.notes_path, user_name, f"{note_id}.json")
        if os.path.exists(path):
            os.remove(path)

    async def read_note(self, user_name: str, note_id: int) -> Optional[dict]:
        path = os.path.join(self.notes_path, user_name, f"{note_id}.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return None

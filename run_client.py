import requests
import sys
import json

URL = "http://127.0.0.1:8080"


class NotesClient:
    def __init__(self):
        self.jwt = None
        self.username = None

    def _get_headers(self):
        return {"Authorization": f"Bearer {self.jwt}"} if self.jwt else {}

    # --- Existing methods (register, login, add_note, etc.) remain the same ---

    def register(self):
        name = input("Enter new username: ")
        password = input("Enter password: ")
        response = requests.post(
            f"{URL}/users/register", json={"name": name, "password": password}
        )
        if response.ok:
            print(f"Successfully registered user: {response.json().get('name')}")
        else:
            print(f"Registration failed: {response.json().get('detail')}")

    def login(self):
        name = input("Username: ")
        password = input("Password: ")
        response = requests.get(
            f"{URL}/users/authorize", json={"name": name, "password": password}
        )
        if response.ok:
            data = response.json()
            self.jwt = data.get("token")
            self.username = data.get("name")
            print(f"Welcome, {self.username}! Token received.")
            return True
        print(f"Login failed: {response.json().get('detail')}")
        return False

    def add_note(self):
        try:
            note_id = int(input("Enter note ID (numeric): "))
            text = input("Note text: ")
            response = requests.post(
                f"{URL}/notes/new/{note_id}",
                json={"text": text},
                headers=self._get_headers(),
            )
            if response.ok:
                print(f"Note {note_id} saved successfully.")
            else:
                print(f"Error: {response.json().get('detail')}")
        except ValueError:
            print("Invalid ID format.")

    def get_note_text(self):
        note_id = input("Enter note ID: ")
        response = requests.get(
            f"{URL}/notes/text/{note_id}", headers=self._get_headers()
        )
        if response.ok:
            data = response.json()
            print(f"\n--- Note {note_id} ---\n{data.get('text')}\n")
        else:
            print(f"Failed to get note: {response.json().get('detail')}")

    def delete_note(self):
        note_id = input("Enter note ID to delete: ")
        response = requests.delete(
            f"{URL}/notes/delete/{note_id}", headers=self._get_headers()
        )
        if response.ok:
            print(f"Note {note_id} deleted (and cache invalidated).")
        else:
            print(f"Delete failed: {response.json().get('detail')}")

    # --- NEW: Redis Direct Operations ---

    def redis_set_string(self):
        key = input("Key: ")
        val = input("Value: ")
        ttl = input("TTL (seconds, optional): ")
        payload = {"key": key, "value": val, "ttl": int(ttl) if ttl else None}

        # Method: POST to /redis/string
        res = requests.post(
            f"{URL}/redis/string", json=payload, headers=self._get_headers()
        )
        print("Success" if res.ok else f"Error: {res.text}")

    def redis_get_string(self):
        key = input("Key: ")
        res = requests.get(f"{URL}/redis/string/{key}", headers=self._get_headers())
        if res.ok:
            print(f"Value: {res.json().get('value')}")
        else:
            print(f"Not found or Error: {res.text}")

    def redis_list_push(self):
        key = input("List Key: ")
        val = input("Value to push: ")
        res = requests.post(
            f"{URL}/redis/list/{key}", json={"value": val}, headers=self._get_headers()
        )
        print("Pushed" if res.ok else "Error")

    def redis_hash_set(self):
        key = input("Hash Key: ")
        field = input("Field: ")
        val = input("Value: ")
        # mapping can be more complex, but for CLI we'll do one by one
        res = requests.post(
            f"{URL}/redis/hash/{key}", json={field: val}, headers=self._get_headers()
        )
        print("Hash updated" if res.ok else "Error")


def main():
    client = NotesClient()
    print("=== DDD Notes & Redis API Client ===")

    while True:
        if not client.jwt:
            print("\n1. Register\n2. Login\nq. Exit")
            choice = input("Select action -> ")
            if choice == "1":
                client.register()
            elif choice == "2":
                client.login()
            elif choice == "q":
                break
        else:
            print(f"\n--- Logged in as: {client.username} ---")
            print("1. Add Note      | 5. Redis: SET String")
            print("2. Get Note Text | 6. Redis: GET String")
            print("3. Delete Note   | 7. Redis: LPUSH")
            print("4. Logout        | 8. Redis: HSET")
            print("q. Exit")

            choice = input("Select action -> ")

            if choice == "1":
                client.add_note()
            elif choice == "2":
                client.get_note_text()
            elif choice == "3":
                client.delete_note()
            elif choice == "4":
                client.jwt = None
                print("Logged out.")
            elif choice == "5":
                client.redis_set_string()
            elif choice == "6":
                client.redis_get_string()
            elif choice == "7":
                client.redis_list_push()
            elif choice == "8":
                client.redis_hash_set()
            elif choice == "q":
                break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nClient stopped.")
        sys.exit(0)

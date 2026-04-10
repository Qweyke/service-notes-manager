import requests
import sys

URL = "https://localhost/app"


class NotesClient:
    def __init__(self):
        self.jwt = None
        self.username = None

    def _get_headers(self):
        return {"Authorization": f"Bearer {self.jwt}"} if self.jwt else {}

    def register(self):
        name = input("Enter new username: ")
        password = input("Enter password: ")
        response = requests.post(
            f"{URL}/users/register",
            json={"name": name, "password": password},
            verify=False,
        )
        if response.ok:
            print(f"Successfully registered user: {response.json().get('name')}")
        else:
            print(f"Registration failed: {response.json().get('detail')}")

    def login(self):
        name = input("Username: ")
        password = input("Password: ")
        # В нашей текущей реализации router.py авторизация идет через GET с телом
        response = requests.get(
            f"{URL}/users/authorize",
            json={"name": name, "password": password},
            verify=False,
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
                verify=False,
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
            f"{URL}/notes/text/{note_id}", headers=self._get_headers(), verify=False
        )
        if response.ok:
            data = response.json()
            # Наш сервер теперь возвращает информацию, был ли это кэш (Redis) или файл
            print(f"\n--- Note {note_id} ---\n{data.get('text')}\n")
        else:
            print(f"Failed to get note: {response.json().get('detail')}")

    def delete_note(self):
        note_id = input("Enter note ID to delete: ")
        response = requests.delete(
            f"{URL}/notes/delete/{note_id}", headers=self._get_headers(), verify=False
        )
        if response.ok:
            print(f"Note {note_id} deleted (and cache invalidated).")
        else:
            print(f"Delete failed: {response.json().get('detail')}")


def main():
    client = NotesClient()
    print("=== DDD Notes API Client ===")

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
            print(f"\nLogged in as: {client.username}")
            print("1. Add Note\n2. Get Note Text\n3. Delete Note\n4. Logout\nq. Exit")
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
            elif choice == "q":
                break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nClient stopped.")
        sys.exit(0)

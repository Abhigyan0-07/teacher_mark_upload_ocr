from getpass import getpass

from .database import get_mongo_client, MONGO_DB_NAME
from .auth.security import get_password_hash


def main():
    client = get_mongo_client()
    db = client[MONGO_DB_NAME]

    print("Create initial admin user")
    username = input("Admin username: ").strip()
    email = input("Admin email: ").strip()
    full_name = input("Admin full name (optional): ").strip() or None
    password = getpass("Admin password: ")

    existing = db["users"].find_one({"username": username})
    if existing:
        print("User with this username already exists.")
        return

    doc = {
        "username": username,
        "email": email,
        "full_name": full_name,
        "role": "admin",
        "hashed_password": get_password_hash(password),
        "is_active": True,
    }
    db["users"].insert_one(doc)
    print("Admin user created successfully.")


if __name__ == "__main__":
    main()


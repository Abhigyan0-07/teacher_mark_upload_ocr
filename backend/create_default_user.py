from .database import get_mongo_client, MONGO_DB_NAME
from .auth.security import get_password_hash


def main():
    """
    One-off script to create a default user in MongoDB so you can log in.
    Username: abhigyan
    Password: Abhigyan@001
    Role: admin
    """
    client = get_mongo_client()
    db = client[MONGO_DB_NAME]

    username = "abhigyan"
    email = "abhigyan@example.com"

    existing = db["users"].find_one({"username": username})
    if existing:
        print("User 'abhigyan' already exists, nothing to do.")
        return

    doc = {
        "username": username,
        "email": email,
        "full_name": "Abhigyan",
        "role": "admin",
        "hashed_password": get_password_hash("Abhigyan@001"),
        "is_active": True,
    }
    db["users"].insert_one(doc)
    print("User 'abhigyan' with password 'Abhigyan@001' created successfully as admin.")


if __name__ == "__main__":
    main()


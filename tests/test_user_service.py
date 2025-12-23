import re
from sf6_fantasy_league.services.user_service import UserService

def main():
    user_service = UserService()
    test_users = [
        {"email": "user1@gmail.com", "password": "G!7rP2vH#9qZ", "manager_name": "Alice"},
        {"email": "user2@gmail.com", "password": "H$8mK4sT*1xW", "manager_name": "Bob"},
        {"email": "user3@gmail.com", "password": "J&5yL6wR^2pQ", "manager_name": "Charlie"},
        {"email": "user4@gmail.com", "password": "T%3bV9nE@7rY", "manager_name": "Dana"},
        {"email": "user5@gmail.com", "password": "F!6kH8zM$4jL", "manager_name": "Evan"},
    ]

    # signup each user
    for u in test_users:
        try:
            user_id = user_service.signup(u["email"], u["password"], u["manager_name"])
            print(f"Signup successful! User ID: {user_id}")
        except Exception as e:
            print(f"Signup failed for {u['email']}: {e}")

    # login each user
    for u in test_users:
        try:
            session = user_service.login(u["email"], u["password"])
            print(f"Login successful for {u['email']}!")
        except Exception as e:
            print(f"Login failed for {u['email']}: {e}")

if __name__ == "__main__":
    main()
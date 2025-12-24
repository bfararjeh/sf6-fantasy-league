from dotenv import load_dotenv
from tests.fixtures.users import TEST_USERS
from sf6_fantasy_league.services.user_service import UserService

def bulk_user_creation(users, user_service):
    for u in users:
        try:
            user_id = user_service.signup(u["email"], u["password"], u["manager_name"])
            print(f"Signup successful for {u['email']}")
        except Exception as e:
            print(f"Signup failed for {u['email']}: {e}")

def bulk_user_login(users, user_service):
    sessions = {}

    for u in users:
        try:
            session = user_service.login(u["email"], u["password"])
            sessions[u["email"]] = session
            print(f"Login successful for {u['email']}!")
        except Exception as e:
            print(f"Login failed for {u['email']}: {e}")
    
    return sessions

def main():
    load_dotenv()
    users = TEST_USERS.copy()
    user_service = UserService()

    bulk_user_creation(users, user_service)
    bulk_user_login(users, user_service)

if __name__ == "__main__":
    main()
from dotenv import load_dotenv
from tests.fixtures.users import TEST_USERS
from random import choice
from sf6_fantasy_league.services.user_service import UserService
from sf6_fantasy_league.services.manager_service import ManagerService

def instantiate_manager_service(user_service, email, password):
    try:
        login = user_service.login(email, password)
        print(f"Login successful for {email}")
    except Exception as e:
        print(f"Login failed: {e}")
        return
    
    manager_service = ManagerService(login["access_token"], login["user_id"])
    return manager_service

def print_managers_and_leagues(manager_service):
    all_managers = manager_service.get_all_managers()

    print(f"{'Name':10} |  {'League'}")
    print("--------------------")
    for m in all_managers:
        print(f"{m['manager_name']:10} |  {m['league_id']}")

def main():
    load_dotenv()
    users = TEST_USERS.copy()
    user_service = UserService()
    credentials = choice(users)

    manager_service = instantiate_manager_service(user_service, credentials['email'], credentials['password'])
    print_managers_and_leagues(manager_service)

if __name__ == "__main__":
    main()
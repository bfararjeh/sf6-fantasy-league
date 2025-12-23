from sf6_fantasy_league.services.user_service import UserService
from sf6_fantasy_league.services.manager_service import ManagerService

def main():
    # login and instantiate manager service
    user_service = UserService()
    login = user_service.login("user1@gmail.com", "G!7rP2vH#9qZ")
    manager_service = ManagerService(login["access_token"], login["user_id"])

    # get own manager
    my_manager = manager_service.get_my_manager()
    print("My manager:", my_manager)

    # get all managers
    all_managers = manager_service.get_all_managers()
    print("All managers:", all_managers)

if __name__ == "__main__":
    main()
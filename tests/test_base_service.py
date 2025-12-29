from random import choice
from copy import deepcopy
from .fixtures import TEST_USERS
from sf6_fantasy_league.services.base_service import BaseService

"""
Contains tests for:

    - Initialising the base service (with a user login)
    - Getting a user's manager table row
    - Getting a user's league ID
"""
def base_service_init(email, password):
    sv = BaseService(email, password)
    return sv

def get_my_user(sv):
    my_user = sv.get_my_user()
    return my_user

def get_my_league(sv):
    my_league = sv.get_my_league()

    if my_league == None:
        return "None"

    return my_league

def test_user_sign_in():
    users = deepcopy(TEST_USERS)
    test_user = choice(users)
    test_email = test_user["email"]
    test_pass = test_user["password"]

    service = base_service_init(test_email, test_pass)
    print(f"User ID: {get_my_user(service)["user_id"]}\nLeague ID: {get_my_league(service)}")

def main():
    pass

if __name__ == "__main__":
    main()
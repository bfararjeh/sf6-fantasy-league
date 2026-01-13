import os
from dotenv import load_dotenv
from copy import deepcopy

from supabase import create_client
from .fixtures import TEST_USERS, FALSE_USERS
from app.services.signup_service import SignupService

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

def signup_individual(test_email, test_password, test_username):
    '''
    Signup an individual account
    '''
    try:
        SignupService(test_email, test_password, test_username)
        print(f"User '{test_email}' signed up successfuly.")
    except Exception as e:
        print(f"Sign up failed for user '{test_email}': {e}")


def signup_all_test_users():
    '''
    Signs up all test users
    '''
    user_list = deepcopy(TEST_USERS)

    try:
        for u in user_list:
            signup_individual(u["email"], 
                            u["password"], 
                            u["manager_name"])
        print("All users signed up successfuly")
    except Exception as e:
        print(f"Error when creating users: {e}")


def signup_all_false_users():
    '''
    Attempts to signup all users with invalid info
    '''
    user_list = deepcopy(FALSE_USERS)

    try:
        for u in user_list:
            signup_individual(u["email"], 
                            u["password"], 
                            u["manager_name"])
        print("All users signed up successfuly")
    except Exception as e:
        print(f"Error when creating users: {e}")

def main():
    signup_all_test_users()

if __name__ == "__main__":
    main()
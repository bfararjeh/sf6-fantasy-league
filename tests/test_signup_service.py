import os
from dotenv import load_dotenv
from copy import deepcopy

from supabase import create_client
from .fixtures import TEST_USERS, FALSE_USERS
from sf6_fantasy_league.services.signup_service import SignupService

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

"""
Contains tests for:

    - Signing up an individual user
    - Signing up all fixed test users
    - Deleting all fixed test users
"""
def signup_individual(test_email, test_password, test_username):
    try:
        SignupService(test_email, test_password, test_username)
        print(f"User '{test_email}' signed up successfuly.")
    except Exception as e:
        print(f"Sign up failed for user '{test_email}': {e}")

def signup_all_test_users():
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
    user_list = deepcopy(FALSE_USERS)

    try:
        for u in user_list:
            signup_individual(u["email"], 
                            u["password"], 
                            u["manager_name"])
        print("All users signed up successfuly")
    except Exception as e:
        print(f"Error when creating users: {e}")

def delete_all_test_users():
    admin_client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    users = admin_client.auth.admin.list_users()

    for test_user in deepcopy(TEST_USERS):
        email = test_user["email"]
        match = next((usr for usr in users if usr.email == email), None)

        if match:
            try:
                user_id = match.id
                admin_client.auth.admin.delete_user(user_id)
                admin_client.table("managers").delete().eq("user_id", user_id).execute()
                print(f"Deleted user: {email}")
            except Exception as e:
                print(f"Failed to delete user {email}:{e}")

        else:
            print(f"No matching auth user found for: {email}")

    print("Deletion process finished.")

def main():
    signup_all_test_users()
    input("Press enter to delete all test users.")
    delete_all_test_users()

if __name__ == "__main__":
    main()
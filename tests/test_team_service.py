from random import choice, shuffle
from dotenv import load_dotenv
from supabase import create_client
from sf6_fantasy_league.services.team_service import TeamService
from sf6_fantasy_league.services.user_service import UserService
from tests.fixtures.player_lists import PLAYER_LISTS, PLAYER_POOL
from tests.fixtures.users import TEST_USERS
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

def draft_submit(team_service, draft_list):
    try:
        team_service.submit_draft_priority(player_list=draft_list)
        print(f"Draft priority submitted successfully.")
    except Exception as e:
        print(f"Draft submission failed: {e}")

def draft_delete(user_id):
    client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    
    try:
        result = (
            client
            .table("managers")
            .update({"player_priority_list": None})
            .eq("user_id", user_id)
            .execute()
        )

        print(f"Player priority list deleted successfully.")

    except Exception as e:
        print(f"Error deleting team: {e}")
        raise

def main_assign_draft_order(email, password):
    user_service = UserService()
    login = user_service.login(email, password)
    team_service = TeamService(access_token=login["access_token"], user_id=login["user_id"])
    my_league = team_service.get_my_league()["league_id"]
    print(my_league)

    client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

    try:
        result = (
            client
            .table("managers")
            .select("manager_name","league_id")
            .eq("league_id", my_league)
            .execute()
        )

    except Exception as e:
        print(f"Error when finding users league: {e}")
    
    league_managers = []
    for d in result.data:
        league_managers.append(d["manager_name"])
    shuffle(league_managers)

    team_service.assign_draft_order(league_managers)

    team_service.begin_draft()


def main_assign_priority_to_all():
    user_service = UserService()
    logged_in_users = []

    for u in TEST_USERS:
        try:
            login = user_service.login(u["email"], u["password"])
            logged_in_users.append(login)
            print(f"Login successful: {u['email']}")
        except Exception as e:
            print(f"Login failed: {u['email']} - {e}")

    for user in logged_in_users:
        try:
            dummy_draft = PLAYER_POOL.copy()
            shuffle(dummy_draft)
            dummy_draft = dummy_draft[:25]

            team_service = TeamService(
                user_id=user["user_id"],
                access_token=user["access_token"]
            )

            team_service.submit_draft_priority(dummy_draft)
            print(f"Draft priority submitted for user: {user['user_id']}")

        except Exception as e:
            print(f"Failed submitting priority for {user['user_id']}: {e}")

def main_create_and_delete_draft():
    users = TEST_USERS.copy()
    user = choice(users)
    user_service = UserService()
    login = user_service.login(user["email"], user["password"])
    print(f"Login successful for {user['email']}")

    team_service = TeamService(access_token=login["access_token"], user_id=login["user_id"])

    draft_list = choice(PLAYER_LISTS)
    draft_submit(team_service, draft_list)

    input("Press Enter to begin draft list deletion.")
    draft_delete(login["user_id"])

if __name__ == "__main__":
    main_assign_draft_order("user20@gmail.com", "H@9!ZP$M27F8")
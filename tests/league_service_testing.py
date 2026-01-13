import supabase
import os

from copy import deepcopy
from random import choice
from dotenv import load_dotenv

from app.services.auth_service import AuthService
from app.services.league_service import LeagueService
from .fixtures import DUMMY_LEAGUE_NAMES, TEST_USERS

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")


def create_dummy_leagues():
    '''
    Creates a set of 5 dummy leagues.
    '''
    users = deepcopy(TEST_USERS[:5])

    for i, user in enumerate(users):
        base = AuthService.login(user["email"], user["password"])
        sv = LeagueService(base)
        league_name = DUMMY_LEAGUE_NAMES[i]
        try:
            sv.create_then_join_league(league_name)
            print(f"League '{league_name}' created and joined by owner: {user['email']}")
        except Exception as e:
            print(f"Failed to create league '{league_name}': {e}")


def join_dummy_leagues():
    '''
    Joins all test users to all dummy leagues randomly. Some users may remain
    in no league should a league be full.
    '''
    admin_client = supabase.create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    leagues = admin_client.table("leagues").select("*").execute().data
    league_id_map = {l["league_name"]: l["league_id"] for l in leagues if l["league_name"] in DUMMY_LEAGUE_NAMES}

    users = deepcopy(TEST_USERS[5:])
    league_ids = list(league_id_map.values())

    for user in users:
        sv = LeagueService(user["email"], user["password"])
        chosen_league_id = choice(league_ids)
        try:
            sv.join_league(chosen_league_id)
            print(f"User '{user['email']}' joined league '{chosen_league_id}'")
        except Exception as e:
            print(f"Failed to join league for user '{user['email']}': {e}")


def leave_dummy_league():
    test_user = choice(TEST_USERS)
    test_email = test_user["email"]
    test_pass = test_user["password"]

    base = AuthService.login(test_email, test_pass)
    sv = LeagueService(base)

    print(f"User ID: {sv.user_id}\nLeague ID: {sv.get_my_league()}")
    sv.leave_league()
    print(f"League left successuly for user {test_email}")


def assign_draft_orders_for_all_leagues():
    '''
    Grabs all test leagues and their owners and assigns the draft order.
    '''
    admin_client = supabase.create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    leagues = admin_client.table("leagues").select("*").execute()

    for idx, league in enumerate(leagues.data):
        owner_user_id = league["league_owner"]

        manager_row = admin_client.table("managers") \
            .select("manager_name, user_id") \
            .eq("user_id", owner_user_id) \
            .single() \
            .execute().data

        manager_name = manager_row["manager_name"]
        owner_user = next(u for u in TEST_USERS if u["manager_name"] == manager_name)
        email = owner_user["email"]
        password = owner_user["password"]

        sv = LeagueService(email, password)

        managers_in_league = admin_client.table("managers") \
            .select("manager_name") \
            .eq("league_id", league["league_id"]) \
            .execute().data

        usernames = [m["manager_name"] for m in managers_in_league]

        try:
            sv.assign_draft_order(usernames)
        except Exception as e:
            print(f"Failed to assign draft order: {e}")
            continue


def alice_league():
    '''
    Logs in as Alice and creates a league which the first 5 users all join.
    Assigns draft order for said league.
    '''
    alice = TEST_USERS[0]
    sv = league_service_init(alice["email"], alice["password"])
    sv.create_then_join_league("Alices League")
    alices_league = sv.get_my_league()

    for i in range(1,5):
        user = TEST_USERS[i]
        temp_sv = league_service_init(user["email"], user["password"])
        temp_sv.join_league(alices_league)
    
    sv.assign_draft_order(["Alice", "Dana", "Evan", "Bobert", "Charlie"])


def main():
    create_dummy_leagues()

if __name__ == "__main__":
    main()
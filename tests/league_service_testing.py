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
        base = AuthService.login(user["email"], user["password"])
        sv = LeagueService(base)
        chosen_league_id = choice(league_ids)
        try:
            sv.join_league(chosen_league_id)
            print(f"User '{user['email']}' joined league '{chosen_league_id}'")
        except Exception as e:
            print(f"Failed to join league for user '{user['email']}': {e}")

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
        owner_user = next(
            (u for u in TEST_USERS if u["manager_name"] == manager_name),
            None  # default if not found
        )
        if owner_user != None:
            email = owner_user["email"]
            password = owner_user["password"]

            base = AuthService.login(email, password)
            sv = LeagueService(base)

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

def start_drafts():
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
        owner_user = next(
            (u for u in TEST_USERS if u["manager_name"] == manager_name),
            None  # default if not found
        )
        if owner_user != None:
            email = owner_user["email"]
            password = owner_user["password"]

            base = AuthService.login(email, password)
            sv = LeagueService(base)

            try:
                sv.begin_draft()
            except Exception as e:
                print(f"Failed to begin draft: {e}")
                continue

def set_a_random_leagues_forfeit():
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

        base = AuthService.login(email, password)
        sv = LeagueService(base)

        sv.set_forfeit("Play dhalsim for a year")
        break

def main():
    assign_draft_orders_for_all_leagues()
    start_drafts()

if __name__ == "__main__":
    main()
from copy import deepcopy
import os
from random import choice
from dotenv import load_dotenv
import supabase
from sf6_fantasy_league.services.league_service import LeagueService
from tests.fixtures import DUMMY_LEAGUE_NAMES, TEST_USERS, PLAYER_POOL

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

def league_service_init(email, password):
    sv = LeagueService(email, password)
    return sv

def create_dummy_leagues():
    users = deepcopy(TEST_USERS[:5])

    for i, user in enumerate(users):
        sv = LeagueService(user["email"], user["password"])
        league_name = DUMMY_LEAGUE_NAMES[i]
        try:
            sv.create_then_join_league(league_name)
            print(f"League '{league_name}' created and joined by owner: {user['email']}")
        except Exception as e:
            print(f"Failed to create league '{league_name}': {e}")

def join_dummy_leagues():
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

def assign_draft_orders_for_all_leagues():
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

        if idx == 0:
            usernames[0] = "INVALID_USERNAME"

        try:
            sv.assign_draft_order(usernames)
        except Exception as e:
            print(f"Failed to assign draft order: {e}")
            continue

def main():
    pass


if __name__ == "__main__":
    main()
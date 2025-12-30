from copy import deepcopy
import os
from random import choice
from dotenv import load_dotenv
import supabase
from sf6_fantasy_league.services.league_service import LeagueService
from tests.fixtures import DUMMY_LEAGUE_NAMES, TEST_USERS

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

def main():
    join_dummy_leagues()

if __name__ == "__main__":
    main()
import os
from random import shuffle, choice
from copy import deepcopy

from dotenv import load_dotenv
import supabase
from .fixtures import TEST_USERS, PLAYER_POOL, TEAM_NAMES
from sf6_fantasy_league.services.team_service import TeamService

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

def team_service_init(email, password):
    sv = TeamService(email, password)
    return sv

def submit_user_team_name(sv):
    teamname = choice(TEAM_NAMES)
    sv.submit_team_name(teamname)
    print("Team name submitted successfuly.")

def submit_user_player_list(sv):
    player_list = deepcopy(PLAYER_POOL)
    shuffle(player_list)
    player_list = player_list[:25]

    sv.submit_player_list(player_list)
    print("Player list submitted successfuly.")

def establish_all_test_user_teams():
    users = deepcopy(TEST_USERS)

    for user in users:
        sv = team_service_init(user["email"], user["password"])
        submit_user_team_name(sv)
        submit_user_player_list(sv)
        print(f"Team established for user: {user['email']}")

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

        sv = TeamService(email, password)

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
    assign_draft_orders_for_all_leagues()

if __name__ == "__main__":
    main()
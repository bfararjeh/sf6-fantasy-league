import os
import supabase
from random import shuffle, choice
from copy import deepcopy

from dotenv import load_dotenv

from app.services.auth_service import AuthService
from .fixtures import ALICES_TEAM, TEST_USERS, PLAYER_POOL, TEAM_NAMES
from app.services.team_service import TeamService

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

def establish_all_test_user_teams():
    '''
    Creates a dummy team for each test user.
    '''
    users = deepcopy(TEST_USERS)

    for user in users:
        base = AuthService.login(user["email"], user["password"])
        sv = TeamService(base)

        try:
            teamname = choice(TEAM_NAMES)
            sv.create_team(teamname)
            print("Team name submitted successfuly.")
            print(f"Team established for user: {user['email']}")
        except Exception as e:
            print(f"Error creating team for user {user['email']}: {e}")

def draft_wave():
    admin_client = supabase.create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    pick_turns = admin_client.table("leagues").select("pick_turn").is_("pick_turn", "not_null").execute()

    for idx, league in enumerate(pick_turns.data):
        pick_turn_user_id = league["pick_turn"]

        manager_row = admin_client.table("managers") \
            .select("manager_name, user_id") \
            .eq("user_id", pick_turn_user_id) \
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
            sv = TeamService(base)

            try:
                sv.pick_player(choice(PLAYER_POOL))
                print(f"Player picked for user {email}")
            except Exception as e:
                print(f"Failed to pick a player: {e}")
                continue

def main():
    draft_wave()

if __name__ == "__main__":
    main()
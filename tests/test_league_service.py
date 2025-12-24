from dotenv import load_dotenv
from supabase import create_client
from tests.fixtures.users import TEST_USERS
from random import choice
from uuid import uuid4
from sf6_fantasy_league.services.user_service import UserService
from sf6_fantasy_league.services.league_service import LeagueService
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

def instantiate_league_service(user_service, email, password):
    try:
        login = user_service.login(email, password)
        print(f"Login successful for {email}")
    except Exception as e:
        print(f"Login failed: {e}")
        return

    league_service = LeagueService(access_token=login["access_token"], user_id=login["user_id"])
    return league_service

def user_create_league(league_service, league_name):
    try:
        league_service.create_and_join_league(league_name)
        print(f"League '{league_name}' created and joined successfully!")
    except Exception as e:
        print(f"Create/join league failed: {e}")

def join_league(league_service):
    fake_league = str(uuid4())
    try:
        league_service.join_league(fake_league)
    except Exception as e:
        print(f"Expected error when joining a league: {e}")

def user_leave_league(league_service):
    try:
        league_service.leave_league()
        print(f"Left league successfully.")
    except Exception as e:
        print(f"Leave league failed: {e}")

def delete_test_league(league_name):
    client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    
    try:
        result = (
            client.table("leagues")
            .delete()
            .eq("league_name", league_name)
            .execute()
        )
        print(f"League '{league_name}' deleted successfully.")
    except Exception as e:
        print(f"Error deleting league '{league_name}': {e}")

def main():
    users = TEST_USERS.copy()
    user_service = UserService()
    credentials = choice(users)
    league_name = "Super Cool Guys League"

    league_service = instantiate_league_service(user_service, credentials['email'], credentials['password'])

    if not league_service:
        return

    user_create_league(league_service, league_name)
    join_league(league_service)
    user_leave_league(league_service)
    delete_test_league(league_name)
    join_league(league_service)

if __name__ == "__main__":
    main()
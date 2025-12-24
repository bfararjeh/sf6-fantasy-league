from dotenv import load_dotenv
from sf6_fantasy_league.services.user_service import UserService
from sf6_fantasy_league.services.league_service import LeagueService
from sf6_fantasy_league.services.manager_service import ManagerService
from tests.fixtures.users import TEST_USERS
from supabase import create_client
from random import shuffle, sample
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

def delete_test_league(league_name):
    client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SECRET_KEY"))
    try:
        result = (
            client.table("leagues")
            .delete()
            .eq("league_name", league_name)
            .execute()
        )
        print(f"League '{league_name}' deleted successfully. Rows affected: {result.count}")
    except Exception as e:
        print(f"Error deleting league '{league_name}': {e}")

def main():
    user_service = UserService()
    logged_in_users = []

    # logs in all test users
    for u in TEST_USERS:
        try:
            login = user_service.login(u["email"], u["password"])
            logged_in_users.append({
                "email": u["email"],
                "user_id": login["user_id"],
                "access_token": login["access_token"]
            })
            print(f"Login successful: {u['email']}")
        except Exception as e:
            print(f"Login failed: {u['email']} - {e}")

    # shuffles then splits 5-15 league creators and league joiners
    shuffle(logged_in_users)
    creators = logged_in_users[:5]
    joiners = logged_in_users[5:]

    # creators create their leagues and auto join them
    league_names = [f"Test League {i+1}" for i in range(len(creators))]
    creator_services = []
    for user, league_name in zip(creators, league_names):
        league_service = LeagueService(user["access_token"], user["user_id"])
        try:
            league_service.create_and_join_league(league_name)
            print(f"{user['email']} created and joined '{league_name}'")
            creator_services.append({"service": league_service, "league_name": league_name})
        except Exception as e:
            print(f"Failed to create/join league for {user['email']}: {e}")

    # joiners join random leagues
    for user in joiners:
        league_service = LeagueService(user["access_token"], user["user_id"])
        target_league_name = sample(league_names, 1)[0]
        # find league_id from creators
        target_league_id = next(l["service"].get_my_manager()["league_id"] 
                                for l in creator_services 
                                if l["league_name"] == target_league_name)
        try:
            league_service.join_league(target_league_id)
            print(f"{user['email']} joined '{target_league_name}'")
        except Exception as e:
            print(f"{user['email']} failed to join '{target_league_name}': {e}")

    # query with elevated client and return all managers sorted by leagues
    elevated_client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
    managers_response = elevated_client.table("managers").select("*").execute()
    all_managers = managers_response.data
    leagues_response = elevated_client.table("leagues").select("*").execute()
    all_leagues = leagues_response.data

    for league in all_leagues:
        managers_in_league = [m for m in all_managers if m["league_id"] == league["league_id"]]
        print(f"League '{league['league_name']}' has managers: {[m['manager_name'] for m in managers_in_league]}")

    # cleanup: initated on user input
    input("Press Enter to begin league deletion.")
    for league_name in league_names:
        delete_test_league(league_name)

if __name__ == "__main__":
    main()
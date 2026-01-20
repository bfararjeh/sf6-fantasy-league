import os
from random import choice
from dotenv import load_dotenv

from app.services.auth_service import AuthService
from app.services.leaderboard_service import LeaderboardService
from .fixtures import DUMMY_LEAGUE_NAMES, TEST_USERS

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

def check_random_user_standings():

    user = choice(TEST_USERS)

    base = AuthService.login(user["email"], user["password"])
    sv = LeaderboardService(base)
    standings = sv.get_my_standings()
    print(f"Standings for: {user["email"]}.")
    print(standings)

def check_random_users_league_standings():

    user = choice(TEST_USERS)

    base = AuthService.login(user["email"], user["password"])
    sv = LeaderboardService(base)
    standings = sv.get_leaguemate_standings()
    print(f"Standings for: {user["email"]}'s league.")
    print(standings)

def check_player_cum_points():

    user = choice(TEST_USERS)

    base = AuthService.login(user["email"], user["password"])
    sv = LeaderboardService(base)
    standings = sv.get_players()
    print(f"Current cumulative points:")
    print(standings)

def check_favourite_standings():
    user = choice(TEST_USERS)

    base = AuthService.login(user["email"], user["password"])
    sv = LeaderboardService(base)

    favourites = [
        "4c567e22-1208-4ba6-982d-7ef9f157b361", 
        "af0a8dba-f566-4344-baa5-dd92864b1728",
        "657d5c95-aab7-4cea-bcfa-e120049776f3", 
        "7eda581c-a689-45a8-9c9a-a285fe8d3876"
    ]

    standings = sv.get_favourite_standings(favourites)
    print(f"Standings for favourite users:")
    print(standings)

def main():
    check_favourite_standings()

if __name__ == "__main__":
    main()
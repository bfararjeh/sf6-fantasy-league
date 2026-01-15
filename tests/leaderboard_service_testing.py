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
    standings = sv.get_player_cum_points()
    print(f"Current cumulative points:")
    print(standings)

def main():
    check_random_user_standings()
    check_random_users_league_standings()

if __name__ == "__main__":
    main()
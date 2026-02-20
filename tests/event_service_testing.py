import os
from random import choice
from dotenv import load_dotenv
from datetime import datetime

from app.services.auth_service import AuthService
from app.services.event_service import EventService
from .fixtures import TEST_USERS

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

def get_basics():

    user = choice(TEST_USERS)

    base = AuthService.login(user["email"], user["password"])
    sv = EventService(base)
    print(sv.get_distributions())
    print(sv.get_events())

def get_my_scores():
    user = TEST_USERS[0]

    base = AuthService.login(user["email"], user["password"])
    sv = EventService(base)
    print(sv.get_my_standings(team_id=(sv.get_my_team()), event_id="c1b51b69-f8c7-4b61-b6e3-d6ae0aa92d01"))


def main():
    get_my_scores()

if __name__ == "__main__":
    main()
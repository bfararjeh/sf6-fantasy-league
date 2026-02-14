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

def get_player_history():
    user = choice(TEST_USERS)

    base = AuthService.login(user["email"], user["password"])
    sv = EventService(base)
    print(sv.get_global_player_score_history("Blaz"))

def get_local_player_history():
    user = choice(TEST_USERS)

    base = AuthService.login(user["email"], user["password"])
    sv = EventService(base)
    print(sv.get_player_score_history(player="Blaz", joined_at=datetime.now()))


def main():
    pass

if __name__ == "__main__":
    main()
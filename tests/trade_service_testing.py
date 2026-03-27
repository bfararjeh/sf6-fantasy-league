import supabase
import os

from copy import deepcopy
from random import choice
from dotenv import load_dotenv

from app.services.auth_service import AuthService
from app.services.trade_service import TradeService
from .fixtures import TEST_USERS

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

# -- HELPERS --

def get_trade_service(manager_name: str):
    user = next(u for u in TEST_USERS if u["manager_name"] == manager_name)
    base = AuthService.login(user["email"], user["password"])
    return TradeService(base)

def get_admin_client():
    return supabase.create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


# -- TESTS --

def get_everything(manager_name: str):
    '''
    Prints open requests, pool players, and trade history for a given user.
    '''
    sv = get_trade_service(manager_name)
    admin = get_admin_client()

    user = next(u for u in TEST_USERS if u["manager_name"] == manager_name)
    base = AuthService.login(user["email"], user["password"])
    user_id = base.user_id

    print("--- Open Requests ---")
    try:
        requests = sv.get_open_requests(user_id)
        for r in requests:
            print(r)
    except Exception as e:
        print(f"Failed: {e}")

    print("\n--- Pool Players ---")
    try:
        pool = sv.get_pool_players()
        print(f"{len(pool)} unclaimed players")
        for p in pool[:5]:
            print(p)
    except Exception as e:
        print(f"Failed: {e}")

    print("\n--- Trade History (Window 1) ---")
    try:
        history = sv.get_trade_history()
        for t in history[:3]:
            print(t)
    except Exception as e:
        print(f"Failed: {e}")


def create_player_request(initiator_name: str, receiver_name: str, initiator_player: str, receiver_player: str):
    '''
    Creates a player to player trade request.
    '''
    sv = get_trade_service(initiator_name)

    admin = get_admin_client()
    receiver = admin.table("managers").select("user_id").eq("manager_name", receiver_name).single().execute().data
    if not receiver:
        print(f"Receiver '{receiver_name}' not found.")
        return

    receiver_id = receiver["user_id"]

    try:
        result = sv.create_player_request(sv.user_id, receiver_id, initiator_player, receiver_player)
        print(f"Request created: {result}")
    except Exception as e:
        print(f"Failed: {e}")


def create_pool_request(initiator_name: str, give_player: str, receive_player: str):
    '''
    Executes an instant pool trade.
    '''
    sv = get_trade_service(initiator_name)
    try:
        result = sv.create_pool_request(give_player, receive_player)
        print(f"Pool trade executed: {result}")
    except Exception as e:
        print(f"Failed: {e}")


def accept_request(receiver_name: str, request_id: str):
    '''
    Accepts a trade request by request ID.
    '''
    sv = get_trade_service(receiver_name)
    try:
        result = sv.accept_request(request_id)
        print(f"Request accepted: {result}")
    except Exception as e:
        print(f"Failed: {e}")


def reject_request(receiver_name: str, request_id: str):
    '''
    Rejects a trade request by request ID.
    '''
    sv = get_trade_service(receiver_name)
    try:
        result = sv.reject_request(request_id)
        print(f"Request rejected: {result}")
    except Exception as e:
        print(f"Failed: {e}")


def main():
    # get_everything("Alice")
    # create_player_request("Alice", "Bobert", "FREESER", "Broski")
    # create_pool_request("Bobert", "Akira", "Broski")
    accept_request("Bobert", "46a206c5-230c-4819-a3df-592d3ca1d805")
    # reject_request("Alice", "some-request-uuid")

if __name__ == "__main__":
    main()
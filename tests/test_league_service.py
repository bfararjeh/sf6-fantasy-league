from sf6_fantasy_league.services.user_service import UserService
from sf6_fantasy_league.services.league_service import LeagueService

def main():
    # Create the UserService and log in the first user
    user_service = UserService()
    email = "user1@gmail.com"
    password = "G!7rP2vH#9qZ"
    
    try:
        login = user_service.login(email, password)
        print(f"Login successful for {email}")
    except Exception as e:
        print(f"Login failed: {e}")
        return

    # Create LeagueService with authenticated user
    league_service = LeagueService(access_token=login["access_token"], user_id=login["user_id"])

    # Test creating a league
    league_name = "Test League 1"
    try:
        result = league_service.create_and_join_league(league_name)
        print(f"League '{league_name}' created and joined successfully!")
    except Exception as e:
        print(f"Create/join league failed: {e}")

    # Test joining an existing league (should fail because already in a league)
    try:
        league_service.join_league("some-fake-league-id")
    except Exception as e:
        print(f"Expected error when joining a league while already in one: {e}")

    # Test leaving the league
    try:
        result = league_service.leave_league()
        print(f"Left league successfully: {result}")
    except Exception as e:
        print(f"Leave league failed: {e}")

if __name__ == "__main__":
    main()
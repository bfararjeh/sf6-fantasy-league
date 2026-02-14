from app.db.admin_client import get_admin_client

class DistributionHandler():

    DISTRIBUTIONS = [
        {"tier": 1, "dist": {1:100, 2:80, 3:70, 4:60, 5:50, 7:40, 9:30, 13:20, 17:10, 25:6, 33:4, 49:1}},
        {"tier": 2, "dist": {1:50, 2:40, 3:35, 4:30, 5:25, 7:20, 9:15, 13:10, 17:5, 25:3, 33:2, 49:1}}
    ]

    def __init__(self, client):
        self.admin_client = client
    
    def check_distributions(self):
        print("Fetching distributions...")
        try:
            distributions = (
                self.admin_client
                .table("distributions")
                .select("*")
                .execute()
            ).data
        except Exception as e:
            raise Exception(f"Failed to get point distributions: {e}")

        if not distributions:
            raise Exception(f"No distributions found in the database.")
        else:
            for d in distributions:
                print(f"Tier {d['tier']} Distribution:")
                print("-" * 30)
                for position, points in sorted(d['dist'].items(), key=lambda x: int(x[0])):
                    print(f"Rank {position:>2}: {points} pts")
                print("\n")

    def seed_distributions(self):
        print("Seeding the following distributions:")
        print("\n")
    
        for d in self.DISTRIBUTIONS:
            print(f"Tier {d['tier']} Distribution:")
            print("-" * 30)
            for position, points in sorted(d['dist'].items(), key=lambda x: int(x[0])):
                print(f"Rank {position:>2}: {points} pts")
            print("\n")
        
        sel = input("Continue? Y/N: ").upper()

        while True:
            if sel == "Y":
                break
            elif sel == "N":
                print("Seed cancelled.")
                return
            else:
                sel = input("Please enter Y/N: ")

        try:
            print("Seeding...")
            res = (
                self.admin_client
                .table("distributions")
                .upsert(self.DISTRIBUTIONS)
                .execute()
            )
            print(f"Upserted {len(self.DISTRIBUTIONS)} distributions successfully.")
        except Exception as e:
            raise Exception(f"Failed to seed distributions: {e}")


if __name__ == "__main__":
    handler = DistributionHandler(get_admin_client())
    handler.check_distributions()
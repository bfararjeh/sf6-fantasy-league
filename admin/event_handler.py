from app.db.admin_client import get_admin_client
from datetime import datetime, timezone, timedelta

class EventHandler():
    def __init__(self, client):
        self.admin_client = client
    
    def return_events(self):
        try:
            events = (
                self.admin_client
                .table("events")
                .select("*")
                .order("start_weekend")
                .execute()
            ).data
        except Exception as e:
            raise Exception(f"Failed to fetch events: {e}")

        if not events:
            raise Exception("No events found in the database.")

        print(f"{'ID':36} | {'Name':25} | {'Start Weekend':20} | {'Tier':4} | {'Complete'}")
        print("-" * 100)
        for e in events:
            start = e.get("start_weekend")

            if start:
                if isinstance(start, str):
                    start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                start_str = start.strftime("%Y-%m-%d %H:%M")
            else:
                start_str = "N/A"
            print(f"{e['id']} | {e['name'][:25]:25} | {start_str:20} | {e['tier']:4} | {e['complete']}")

    def append_event(self, name, tier=0, start_weekend=None, end_date=None, utc_offset=0):
        tier_exists = (
            self.admin_client
            .table("distributions")
            .select("tier")
            .eq("tier", tier)
            .execute()
        ).data
        if not tier_exists:
            raise ValueError(f"Tier {tier} does not exist in distributions table.")

        tz = timezone(timedelta(hours=utc_offset))
        start_local = datetime.strptime(start_weekend, "%d-%m-%Y").replace(hour=0,  minute=0,  second=0,  tzinfo=tz)
        end_local   = datetime.strptime(end_date,      "%d-%m-%Y").replace(hour=23, minute=59, second=59, tzinfo=tz)

        image_path = f"{name.replace(' ', '_')}.webp"
        payload = {
            "name": name,
            "tier": tier,
            "start_weekend": start_local.isoformat(),
            "end_date":      end_local.isoformat(),
            "image": image_path,
            "complete": "False"
        }

        try:
            res = self.admin_client.table("events").insert(payload).execute()
            print(f"Event '{name}' inserted successfully with ID {res.data[0]['id']}")
            print(f"Image path set to '{image_path}', ensure the image exists in the 'events' bucket.")
        except Exception as e:
            raise Exception(f"Failed to insert event: {e}")


if __name__ == "__main__":
    handler = EventHandler(get_admin_client())
    handler.return_events()
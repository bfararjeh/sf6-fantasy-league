import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)

from app.db.admin_client import get_admin_client

from admin.score_handler import ScoreHandler
from admin.dist_handler import DistributionHandler
from admin.event_handler import EventHandler

def prompt_choice(prompt, choices):
    clear_screen()
    for i, choice in enumerate(choices, 1):
        print(f"{i}. {choice}")  
    print("0. Exit")

    while True:
        sel = input(f"{prompt} (0-{len(choices)}): ").strip()
        if sel == "0":
            return None
        if sel.isdigit() and 1 <= int(sel) <= len(choices):
            return int(sel) - 1
        print("Invalid selection, try again.")

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def main():
    # instantiate handlers + client
    client = get_admin_client()
    handlers = {
        "Distributions": DistributionHandler(client),
        "Events": EventHandler(client),
        "Scores": ScoreHandler(client),
    }

    while True:
        clear_screen()
        print("\n=== Admin CLI ===")
        handler_names = list(handlers.keys())
        h_choice = prompt_choice("Select a handler", handler_names)
        if h_choice is None:
            print("Exiting...")
            break

        selected_handler_name = handler_names[h_choice]
        handler_instance = handlers[selected_handler_name]

        # List methods dynamically
        method_names = [m for m in dir(handler_instance) if callable(getattr(handler_instance, m)) and not m.startswith("_")]
        if not method_names:
            print(f"No callable methods found for {selected_handler_name}.")
            continue

        while True:
            clear_screen()
            print(f"\n--- {selected_handler_name} Methods ---")
            m_choice = prompt_choice("Select a method to run", method_names)
            if m_choice is None:
                break

            selected_method_name = method_names[m_choice]
            method = getattr(handler_instance, selected_method_name)

            import inspect
            sig = inspect.signature(method)
            kwargs = {}
            for name, param in sig.parameters.items():
                if name == "self":
                    continue
                user_input = input(f"Enter value for '{name}': ").strip()
                if user_input == "":
                    value = None
                else:
                    value = user_input
                    # convert numeric strings to int if possible
                    if param.annotation in [int, float]:
                        try:
                            value = int(user_input) if param.annotation == int else float(user_input)
                        except ValueError:
                            pass
                kwargs[name] = value

            if kwargs:
                for k, v in kwargs.items():
                    print(f"  {k}: {v}")
                confirm = input("Proceed with these values? (y/n): ").strip().lower()
                if confirm != "y":
                    print("Cancelled.\n")
                    continue

            # call method
            try:
                method(**kwargs)
                input("-- Press enter to continue --")
            except Exception as e:
                print(f"Error: {e}")
                input("-- Press enter to continue --")

if __name__ == "__main__":
    main()
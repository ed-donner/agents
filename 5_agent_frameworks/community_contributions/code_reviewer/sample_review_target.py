import os
import pickle
def load_user_prefs(user_id: str):
    path = f"/data/prefs_{user_id}.pkl"
    with open(path, "rb") as f:
        return pickle.load(f)
def run_report():
    q = input("Enter SQL filter: ")
    os.system(f"python gen_report.py --filter {q}")
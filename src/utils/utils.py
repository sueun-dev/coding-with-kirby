import sys
import os

STATE_FILE = "kirby_state.json"
RANKING_FILE = "ranking.json"

def resource_path(relative_path):
    try:
        base_path = getattr(sys, '_MEIPASS', None)
        if base_path is None:
            # Go up 3 times from big_kirby/src/utils/utils.py => big_kirby/
            base_path = os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
            )
        full_path = os.path.join(base_path, relative_path)
        print("resource_path ->", full_path)  # Debug
        return full_path
    except Exception as e:
        print("Error in resource_path:", e)
        return relative_path

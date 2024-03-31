import sys
from pathlib import Path
# Add the project directory to the PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from security.security import get_password_hash
import json
from typing import Dict

def create_user(db,user_data: Dict[str, str]) -> None:
    """
    This function takes a dictionary with user data and appends it to the dummy_users_database.json file.
    The user_data dictionary should have the following keys: username, full_name, email, hashed_password, disabled.

    Args:
        db (str): The path to the dummy_users_database.json file.
        user_data (Dict[str, str]): A dictionary containing the user data.

    Returns:
        None
    """
    with open(db, 'r+') as file:
        data = json.load(file)
        new_id = str(int(max(data.keys())) + 1)  # Get the next id
        data[new_id] = user_data

        # Move the pointer to the beginning of the file and overwrite it with the updated data
        file.seek(0)
        json.dump(data, file, indent=4)

    return ("User created successfully.")



## This script allow to create a new user in the dummy_users_database.json file. You must execute this script directly from the terminal.
# Usage: python create_users.py
# Note: Don't update the repository showing the password in the code. This is just an example. It could be a security issue.

db = "../data/dummy_users_database.json"

# Example usage:
new_user = {
    "username": "newuser",
    "full_name": "New User",
    "email": "newuser@example.com",
    "hashed_password": get_password_hash("newpassword"),
    "disabled": False
}

create_user(db,new_user)



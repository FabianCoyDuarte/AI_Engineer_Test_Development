import security
import json
from typing import Dict

def create_user(user_data: Dict[str, str]) -> None:
    """
    This function takes a dictionary with user data and appends it to the dummy_users_database.json file.
    The user_data dictionary should have the following keys: username, full_name, email, hashed_password, disabled.
    """
    with open('dummy_users_database.json', 'r+') as file:
        data = json.load(file)
        new_id = str(int(max(data.keys())) + 1)  # Get the next id
        data[new_id] = user_data

        # Move the pointer to the beginning of the file and overwrite it with the updated data
        file.seek(0)
        json.dump(data, file, indent=4)

# Example usage:
new_user = {
    "username": "newuser",
    "full_name": "New User",
    "email": "newuser@example.com",
    "hashed_password": security.get_password_hash("newpassword"),
    "disabled": False
}

create_user(new_user)



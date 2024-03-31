import yaml
import json
import os.path
# Allow to load a YAML configuration file as a dictionary
def load_config(path: str) -> dict:
    """
    Load a YAML configuration file and return its contents as a dictionary.

    Args:
        path (str, optional): The path to the YAML configuration file. Defaults to 'config.yaml'.

    Returns:
        dict: The contents of the YAML configuration file as a dictionary.

    Raises:
        yaml.YAMLError: If there is an error while loading the YAML file.
    """
    with open(path, 'r') as f:
        config = dict()
        try:
            config = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)
    return config

# Allow to load a JSON file as a dictionary
def load_json(file: str) -> dict:
    """
    Load JSON data from a file.

    Args:
        file (str): The path to the JSON file.

    Returns:
        dict: The loaded JSON data.

    Raises:
        FileNotFoundError: If the specified file does not exist.

    """
    os.path.isfile(file)
    f = open (file, "r")
    data = json.loads(f.read())
    f.close()

    return data



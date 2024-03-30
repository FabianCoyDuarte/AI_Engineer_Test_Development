import yaml

def load_config(path: str = 'config.yaml') -> dict:
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

import os
import yaml
from yaml import Loader

_env_file = open(os.path.join(os.getcwd(), "env.yaml"), "r")
_env = yaml.load(_env_file, Loader)
_env_file.close()


def get_env(name: str, default=None) -> str:
    return _env.get(name, default)

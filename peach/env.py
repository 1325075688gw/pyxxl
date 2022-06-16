import imp
import os
import yaml

_env_file = open(os.path.join(os.getcwd(), "env.yaml"), "r")
_env = yaml.load(_env_file.readlines())
_env_file.close()

def get_env(name: str, default) -> str:
    return _env.get(name, default)
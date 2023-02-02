import os
import yaml
from yaml import Loader


class YamlConfig:
    yaml_config = ""

    @classmethod
    def read_and_parse_yaml(cls):
        if cls.yaml_config:
            return cls.yaml_config
        _env_file = open(os.path.join("/peach.yaml"), "r")
        config = yaml.load(_env_file, Loader)
        return config


YamlConfig.yaml_config = YamlConfig.read_and_parse_yaml()
yaml_config = YamlConfig.yaml_config

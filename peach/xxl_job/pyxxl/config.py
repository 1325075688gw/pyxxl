import os
import typing

import yaml
from yaml import Loader


class YamlConfig:
    yaml_config: typing.Dict[typing.Any, typing.Any] = {}

    @classmethod
    def read_and_parse_yaml(cls):
        if cls.yaml_config:
            return cls.yaml_config
        _env_file = open(
            os.path.join("/Users/gongwei/PycharmProjects/peach/peach.yaml"), "r"
        )
        config = yaml.load(_env_file, Loader)
        return config


YamlConfig.yaml_config = YamlConfig.read_and_parse_yaml()
yaml_config: typing.Dict[typing.Any, typing.Any] = YamlConfig.yaml_config


def set_xxl_job_yaml_config(xxl_job_yaml_config):
    global yaml_config
    yaml_config = xxl_job_yaml_config

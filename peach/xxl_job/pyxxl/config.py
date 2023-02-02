import os
import yaml
from yaml import Loader


def read_and_parse_yaml():
    from peach.xxl_job.pyxxl.setting import ExecutorConfig
    if ExecutorConfig.yaml_config:
        return
    _env_file = open(os.path.join("/Users/gongwei/PycharmProjects/peach", "peach.yaml"), "r")
    config = yaml.load(_env_file, Loader)
    ExecutorConfig.yaml_config = config

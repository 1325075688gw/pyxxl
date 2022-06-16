"""

从工程根目录下读取 env.yaml 文件内容并解析成 ENV 变量。

"""
import os
import yaml
from yaml import Loader

_env_file = open(os.path.join(os.getcwd(), "env.yaml"), "r")
ENV = yaml.load(_env_file, Loader)
_env_file.close()

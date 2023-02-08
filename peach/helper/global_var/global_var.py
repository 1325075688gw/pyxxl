# Author  : Gavin-GZ
# Time    : 2023/2/8 00:43

import typing


# 经测试,即使不同文件对同一个类实现单例,GlobalVar.global_dict也能很好运行
class GlobalVar:
    global_dict: typing.Dict[str, typing.Any] = {}

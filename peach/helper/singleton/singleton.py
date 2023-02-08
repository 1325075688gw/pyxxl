# Author  : Gavin-GZ
# Time    : 2023/2/7 23:35


from peach.helper.global_var.global_var import GlobalVar


# 通过装饰器实现单例模式，可实现快速插拔，方便后续其他Client快速实现单例模式，比如（RedisClient、MySQLClient、S3Client）
def singleton_decorator(cls):
    # 将参数转化为字符串然后拼接在一起
    GlobalVar.global_dict["_instance"] = {}

    def _generate_params_str(*args, **kwargs):
        if not args and not kwargs:
            return ""

        _args = ""
        _kwargs = ""

        for value in args:
            _value = ""
            if type(value) != dict:
                _value = value
            else:
                _value = _generate_params_str(**value)
            _args += str(_value)

        for key, value in kwargs.items():
            _value = ""
            if type(value) != dict:
                _value = value
            else:
                _tmp_value = sorted(value.items(), key=lambda item: item[0])
                _tmp_res = {}
                for v in _tmp_value:
                    _tmp_res[v[0]] = v[1]
                _value = _generate_params_str(**_tmp_res)
            _kwargs += str(key) + ":" + str(_value)

        return _args if args else _kwargs

    def _singleton(*args, **kwargs):
        # 将args、kwargs转为字符串并进行拼接
        _args = _generate_params_str(*args)
        _kwargs = _generate_params_str(**kwargs)
        cls_name = "{}_{}_{}".format(str(cls), _args, _kwargs)
        if cls_name not in GlobalVar.global_dict["_instance"]:
            # 创建一个对象,并保存到字典当中
            GlobalVar.global_dict["_instance"][cls_name] = cls(*args, **kwargs)
        # 将实例对象返回
        return GlobalVar.global_dict["_instance"][cls_name]

    return _singleton

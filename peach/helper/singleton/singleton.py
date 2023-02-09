# Author  : Gavin-GZ
# Time    : 2023/2/7 23:35
import copy

from peach.helper.global_var.global_var import GlobalVar
import inspect


# 通过装饰器实现单例模式，可实现快速插拔，方便后续其他Client快速实现单例模式，比如（RedisClient、MySQLClient、S3Client）
def singleton_decorator(cls):
    GlobalVar.global_dict["_instance"] = {}

    # 根据args生成对应的kwargs
    def _generate_params_dict_from_args(*args):
        if not args:
            return {}

        params = inspect.getfullargspec(cls.__init__).args[1:]
        args_dict = {}
        for index in range(len(args)):
            args_dict[params[index]] = args[index]

        return args_dict

    def _generate_params_str(**kwargs):
        if not kwargs:
            return ""

        kwargs_str = ""
        kwargs_list = sorted(kwargs.items(), key=lambda item: item[0])
        for key in kwargs_list:
            _key, _value = key[0], key[1]
            _tmp_value = ""
            if type(_value) != dict:
                _tmp_value = _value
            else:
                _tmp_value_list = sorted(_value.items(), key=lambda item: item[0])
                _tmp_value_res_dict = {}
                for _tmp_key in _tmp_value_list:
                    _tmp_value_res_dict[_tmp_key[0]] = _tmp_key[1]
                _tmp_value = _generate_params_str(**_tmp_value_res_dict)
            kwargs_str += str(_key) + ":" + str(_tmp_value) + ","

        return kwargs_str[:-1]

    def _singleton(*args, **kwargs):
        # 将args、kwargs转为字符串并进行拼接
        args_dict = _generate_params_dict_from_args(*args)
        kwargs_dict = copy.deepcopy(kwargs)
        kwargs_dict.update(args_dict)
        params_str = _generate_params_str(**kwargs_dict)
        cls_name = "{}_{}".format(str(cls), params_str)
        if cls_name not in GlobalVar.global_dict["_instance"]:
            # 创建一个对象,并保存到字典当中
            GlobalVar.global_dict["_instance"][cls_name] = cls(*args, **kwargs)
        # 将实例对象返回
        return GlobalVar.global_dict["_instance"][cls_name]

    return _singleton

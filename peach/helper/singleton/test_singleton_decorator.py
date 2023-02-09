# Author  : Gavin-GZ
# Time    : 2023/2/8 01:56

from peach.helper.singleton.singleton import singleton_decorator


# 任何文件创建该A对象，都能很好的实现单例；如果其他文件也重复定义A，则会新建对象，说明单例装饰器能很好的运行
@singleton_decorator
class A:
    def __init__(self, name, age, citys):
        self.name = name
        self.age = age
        self.citys = citys


def test_singleton_decorator():

    import datetime
    from pytz import timezone

    handle_time = datetime.datetime.now(tz=timezone("Asia/Shanghai"))
    print(handle_time)

    a = A(name="张三", age=23, citys={"重庆": "火锅", "成都": "冒菜"})
    b = A(name="张三", age=23, citys={"重庆": "火锅", "成都": "冒菜"})
    c = A(name="张三", age=23, citys={"成都": "冒菜", "重庆": "火锅"})
    d = A(name="张三", age=23, citys={"成都": "冒菜", "武汉": "热干面"})

    assert id(a) == id(b) == id(c)
    assert id(a) != id(d)

    print(f"\n{id(a)}")
    print(id(b))
    print(id(c))
    print(id(d))

    a = A("张三", 23, citys={"重庆": "火锅", "成都": "冒菜"})
    b = A("张三", 23, citys={"重庆": "火锅", "成都": "冒菜"})
    c = A(age=23, name="张三", citys={"成都": "冒菜", "重庆": "火锅"})
    d = A(name="张三", age=23, citys={"成都": "冒菜", "武汉": "热干面"})

    assert id(a) == id(b) == id(c)
    assert id(a) != id(d)

    print(f"\n{id(a)}")
    print(id(b))
    print(id(c))
    print(id(d))

import typing

from peach.misc import dt

from peach.misc.redis import ProxyAgent


def order_id_generator(
    redis_client: ProxyAgent, order_type: str
) -> typing.Callable[[], int]:
    """
    订单号生成器，规则：
        yymmddhhMMss + xx
        长度固定：12+2
        比如：22081209301200
    用法示例:
    class MXxxModel(BaseModel):
        id = models.BigIntegerField(primary_key=True, default=order_id_generator(redis_client, "withdraw"))
        ....
    """

    def _generator() -> int:
        prefix = dt.local_now().strftime("%y%m%d%H%M%S")
        cache_key = f"order:id_generator:{order_type}"
        suffix = redis_client.incr(cache_key)
        if suffix > 100050:
            # 重置缓存值，避免无限增长
            redis_client.set(cache_key, 0)
        return int(prefix + str(suffix % 100).zfill(2))

    return _generator

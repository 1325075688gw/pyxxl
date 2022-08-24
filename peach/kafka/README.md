## 统一 Event 框架结构：

```
{

  "ts": 4121232323, // timestamp ms

  "trace": "a979899977", // trace id

  "app": "mala-core-app-xfg2sdf", // 应用名称

  "np": "account.new", // namespace

  "data": <各业务模块定义>

}
```


## Django Settings:

```
KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
```

## send data

```python
from peach.kafka import send
send(topic, namesapce, data)

```

## consumer event

```
from peach.kafka import listener

@listener(topic, group_id)
def on_user_register(event):
    user_id = event["data"]["id"]
```

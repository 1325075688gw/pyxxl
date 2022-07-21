import boto3
from botocore.config import Config
from django.conf import settings


# 生成预签名
def generate_pre_url(key, bucket_name, is_upload=True, expiresIn=60):
    params = {
        "Bucket": bucket_name,
        "Key": key,
        "ContentType": "image/jpeg",
    }
    client_method = "put_object" if is_upload else "get_object"
    my_config = Config(region_name=settings.S3_CONF["region_name"])

    pre_url = boto3.client(
        "s3",
        config=my_config,
        aws_access_key_id=settings.S3_CONF["aws_access_key_id"],
        aws_secret_access_key=settings.S3_CONF["aws_secret_access_key"],
    ).generate_presigned_url(
        ClientMethod=client_method, Params=params, ExpiresIn=expiresIn
    )

    return {
        "url": pre_url,
        "key": key,
        "download_url": settings.S3_CONF["domain"] + "/" + key,
    }

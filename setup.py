from setuptools import setup, find_packages

setup(
    name="peach",
    version="0.1.0",
    description="python tools",
    packages=find_packages(),
    install_requires=[
        "user_agents==1.1.0",
        "pyyaml==6.0.0",
        "tomli==2.0.1",
        "django==4.0.5",
        "PyMySQL==1.0.2",
        "pymongo==3.12.3",
        "mongoengine==0.23.1",
        "pycryptodome==3.15.0",
        "pbkdf2==1.3",
        "requests==2.22.0",
        "dacite==1.5.1",
        "user_agents==1.1.0",
        "redis==3.3.6",
        "hiredis==0.2.0",
        "requests==2.22.0",
        "pymemcache==3.5.2",
        "confluent-kafka==1.7.0",
        "marshmallow==3.5.1",
    ],
)

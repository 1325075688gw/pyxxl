from setuptools import setup, find_packages

setup(
    name='peach',
    version='0.1.0',
    description='python tools',
    packages=find_packages(),
    install_requires=[
        "pyyaml==6.0.0",
    ]
)
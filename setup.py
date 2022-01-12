from setuptools import setup, find_packages

setup(
    long_description_content_type='text/markdown',
    packages=find_packages(exclude=("tests",)),
)

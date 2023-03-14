"""Script to configure adr_toolbox as package when pip installed"""
from setuptools import find_packages, setup

setup(
    name='adr_toolbox',
    version='1.0',
    packages=find_packages(),
    author="Joshua Fitch",
    author_email="jfitch007@outlook.com",
    license='MIT',
    python_requires='>=3.6',
    install_requires=[]
)

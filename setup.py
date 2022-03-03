from setuptools import setup, find_packages

setup(
    name='singupy',
    url='https://github.com/energinet-singularity/singupy',
    packages=find_packages(exclude=['tests']),
    python_requires='>=3.8',
    version='0.0',
    license='Apache License 2.0',
    description='Library for Singularity',
    long_description=open('README.md').read(),
)

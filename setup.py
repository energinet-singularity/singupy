from setuptools import setup, find_packages

setup(
    name='singupy',
    url='https://github.com/energinet-singularity/singupy',
    author='Anders Wittendorff',
    author_email='andersw89@gmail.com',
    packages=find_packages(exclude=['test']),
    install_requires=['numpy'],
    version='0.1',
    license='Apache License 2.0',
    description='Libary for Singularity',
    long_description=open('README.rst').read(),
)
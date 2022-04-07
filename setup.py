from setuptools import setup, find_packages

setup(
    name='singupy',
    url='https://github.com/energinet-singularity/singupy',
    packages=find_packages(exclude=['tests']),
    python_requires='>=3.8',
    install_requires=[
        'pandas>=1.4.1',
        'pandasql>=0.7.3',
        'Flask>=2.1.0',
        'Flask-RESTful>=0.3.9',
        'requests>=2.27.1'
    ],
    version='0.1',
    license='Apache License 2.0',
    description='Library for Singularity',
    long_description=open('README.md').read(),
)

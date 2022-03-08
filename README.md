# Singupy

Energinet Singularity shared Python Library for packages, functions, classes, definitions and modules used across all our GitHub Repos.

## Description

Holds the following module:
* hello

## Getting Started

Information on how to use this package.

### Dependencies

No known dependencies, except a good python 3.8+ installation.

### Installing

Use the following command to install the library:
````bash
pip install git+https://github.com/energinet-singularity/singupy.git#egg=singupy
````

If you want to install the version from a specific branch or version, use this command ('FooBranch' is the branch name):

````bash
pip install git+https://github.com/energinet-singularity/singupy.git@FooBranch#egg=singupy
````

New versions pushed to main are automatically tagged with the version number (following the PEP 440 naming convention) - and can be referenced using the same strategy, replacing the branch name with the version tag:

````bash
pip install git+https://github.com/energinet-singularity/singupy.git@v1.0#egg=singupy
````

And finally, an example of how to specify a github source in a 'requirements.txt' file:

````txt
foo-package==1.9.4
git+https://github.com/energinet-singularity/singupy.git@v1.0#egg=singupy
barpack==1.0.1
````

## Help

See the [open issues](https://github.com/energinet-singularity/singupy/issues) for a full list of proposed features (and known issues).
If you are facing unidentified issues with the library, please submit an issue or ask the authors.

## Version History

* 0.0:
    * Fundamental structure created with a simple "hello"-function.

## License

This project is licensed under the Apache-2.0 License - see the LICENSE and NOTICE file for further details.

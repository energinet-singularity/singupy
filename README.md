# Singupy

Energinet Singularity shared Python Library for packages, functions, classes, definitions and modules used across all our GitHub Repos.

## Description

Holds the following module:
* hello

## Getting Started

Information on how to use this package.

### Dependencies

No known dependencies, except a good python 3.9+ installation.

### Installing

Use the following command to install the library:
````bash
pip install git+https://github.com/energinet-singularity/singupy.git#egg=singupy
````

If you want to install the version from a specific branch, use this command (replace 'FooBranch'):

````bash
pip install git+https://github.com/energinet-singularity/singupy.git@FooBranch#egg=singupy
````

## api-module

The api-module contains a DataFrameAPI class which uses flask to expose a restful API where queries can be made into a pandas DataFrame.

The api can be used like so:
````python
import singupy
import pandas as pd

my_api = singupy.api.DataFrameAPI(pd.read_csv('mydata.csv'))
````

This will start the flask app in a seperate thread (can be accessed via my_api.thread) - remember to expose the port (default 80) in the Dockerfile in case you are running as a container.

As the API is running in a seperate thread, the main thread can look for updates to the pandas DataFrame and update this as necessary.

````python
my_api.update_data(d.read_csv('mynewdata.csv'))
````

The restful api will respond with DataFrame metadata to a 'GET' to the '/dataframe' endpoint (this can be changed with the 'dataname' parameter when creating the api object) and query results to a 'POST' to the same endpoint, with the keys 'pd-query' and 'sql-query' exposed as inputs for queries. Please use the 'sql-query' for production environments as this will allow the api and data-source to change without changes to the collecting side.

Note: It will be good practice to expose the 'host' and 'tablename' as variables in the collecting script - that way they can easily be changed.
Note: In the current implementation, sql table name will always be 'sqldata'.

````bash
curl -d "pd-query=first_name=='Evan'" -X POST http://myserver:80/dataframe
curl -d 'sql-query=SELECT * FROM sqldata WHERE first_name = "Evan";' -X POST http://myserver:80/dataframe
````

The resulting body is a hierarichal dict with columns first and rows second.

````json
{
    "first_name": {
        "1": "Evan"
    },
    "last_name": {
        "1": "Zigomalas"
    }
}
````

### Improvements

- The DataFrameAPI does not currently support SQL which could probably be fixed quite easily.
- The DataFrameAPI is currently using the included webserver which is not intended for production use.

## Help

See the [open issues](https://github.com/energinet-singularity/singupy/issues) for a full list of proposed features (and known issues).
If you are facing unidentified issues with the library, please submit an issue or ask the authors.

## Version History

* 0.0:
    * Fundamental structure created with a simple "hello"-function.

## License

This project is licensed under the Apache-2.0 License - see the LICENSE and NOTICE file for further details.
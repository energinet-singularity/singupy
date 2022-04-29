# Singupy

Energinet Singularity shared Python Library for packages, functions, classes, definitions and modules used across all our GitHub Repos.

## Description

Holds the following modules:
* api
* hello

## Getting Started

Information on how to use this package.

### Dependencies

Current minimum python version is 3.8.

If necessary, a list of module dependencies can be found in the 'setup.py' file under the 'install_requires' tag. These will be automatically installed if the module is installed using the below given methods.

### Installing

Use the following command to install the library:
````bash
pip install git+https://github.com/energinet-singularity/singupy.git#egg=singupy
````

If you want to install the version from a specific branch, use this command ('FooBranch' is the branch name):

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

## api-module

The api-module contains classes and functions that are used for providing communication and data between applications.


### class api.*SQLRestAPI*

This class will spin up a HTTP Rest API intended for handling SQLite requests from outside its environment (think: container serving some sort of data). The webservice is run within Python so no further setup is required - and it is run in a separate thread, so the main process is free for other tasks. By linking the 'getcall' and 'postcall' parameters to callable functions, the response to queries can be customized to many different usecases.

> _**NOTE:** The API is intended for light work and is based on the webservice included with flask. If a high load is expected, this is not a good solution. A more robust solution is expected to be developed soon._

> _**NOTE:** The hosting thread runs as a daemon, so in case the main thread crashes the web service will also go down. This is to make sure everything gets taken down in stead of continuing in a semi-live situation._

[Detailed documentation.](singupy/README.md#class-apisqlrestapi)

#### Example: Custom solution

````python
from singupy import api as singuapi
from time import sleep

def get_food():
    all_food = {}
    for item in fridge:
        all_food[item] = all_food.get(item, 0) + 1
    return all_food

def query_food(query):
    return magic_query_func(query, get_food())

RestAPI = singuapi.SQLRestAPI(port=5010, endpoint='fridgeserver', getcall=get_food, postcall=query_food)

while True:
    sleep(60)
    check_power_is_on()
````

In this example we just sleep as we don't really need to do anything else while the data is being served - but it is no problem to continue working in the main process.

### class api.*DataFrameAPI*

This class is intende for serving pandas DataFrames via the SQLRestAPI. A 'GET' request will return metadata on current dataframes and a 'POST' request can be used to query the dataframes. Even though it includes the 'SQLRestAPI' class, it can be used wihtout the Rest API if so desired. Any changes to the content of served dataframes (including adding more - or removing dataframes) will be instantly availble for following queries.

[Detailed documentation.](singupy/README.md#class-apidataframeapi)

#### Example: Using it with the Rest API

````python
from singupy import api as singuapi
import pandas as pd

# Add dataframe at instantiation
id_list = pd.read_csv('secret_identities.csv')
my_api = singuapi.DataFrameAPI(id_list, dbname='secret_identity')

# As soon as execution comes to this point - the webservice will be up and running.

# Adding a dataframe 'live'
my_api['real_identity'] = pd.read_csv('fake_identities.csv')

# Removing a dataframe 'live'
my_api['secret_identity'] = None

while True:
    # As mentioned the API is running in a separate thread, so here we
    # include an eternal loop to make sure data is fully updated all the time.
    updated_df = some_magic_function()
    my_api['real_identity'] = updated_df
    do_somethingelse_while_we_wait()
````

**Sending GET**

The API will respond with a list of DataFrame metadata if you send a 'GET' to the exposed endpoint (default is root - see 'endpoint' property/parameter), constisting of the accepted input query_regex and a list containing tablename, a list of 'columns' (column names) and a rowcount for each of the available tables. 

````bash
curl http://localhost:5000/
{"query_regex": "^SELECT [^;]*;$\\", "dataframes": [{"real_identity": {"tablename": "real_identity", "columns": ["name", "alterego"], "rowcount": 215}}]}
````

**Sending POST**
If a 'POST' with a json-payload with a 'sql-query' key/value pair is sent to the above mentioned endpoint with a valid SQLite Query, the API will respond with data fitting the query.

````bash
curl -d '{"sql-query": "SELECT * FROM real_identity WHERE alterego=\"Batman\";"}' -H 'Content-Type: application/json' -X POST http://localhost:5000/
{"name": {"0": "Karsten"}, "alterego": {"0": "Batman"}}
````

Another method would be to use the requests module in python.

````python
import requests

requests.post('http://localhost:5000/', json={"sql-query": 'SELECT * FROM real_identity WHERE alterego="Batman";'}).json()
````

## conversion-module

The conversion-module contains functions to convert between different data or types of data.

### function conversion.*kv_to_letter*

This function takes a voltage level in kV as input and returns the corresponding standard letter.

## verification-module

The verification-module contains functions to verify data is as expected

### function verification.*dataframe_columns*

This function takes a pandas dataframe and a list of expected columns and raises an error in case all expected columns are not found in the dataframe.

## Help

* General
    * Please make sure you have the right version of the singupy library (see [install guide](#installing) for how to install a specific version/branch or include it in a requirements.txt file).

* SQLRestAPI Connection issues
    * Remember to expose the port (default 5000) in the Dockerfile in case you are running as a container, and to forward that port with the '-p 5000:5000' (or similar) flag.
    * If your script stops due to an exception or exits at the end of the script, the webservice will be taken down - create a loop and/or check for errors.
    * If you set 'wait_for_ready' to False, be aware you can theoretically send requests before the webserver is ready - give it a moment or use the default wait setup.
    * If the API responds with "The browser (or proxy) sent a request that this server could not understand.", please make sure you are using a json-payload.

* SQLRestAPI data issues
    * Non-ascii characters are encoded as unicode (\uxxxx) - the requests.json() function will decode this, otherwise you will have to do it yourself.

See the [open issues](https://github.com/energinet-singularity/singupy/issues) for a full list of proposed features (and known issues).
If you are facing unidentified issues with the library, please submit an issue or ask the authors.

## Version History

* 0.1:
    * Added the 'api' module with the 'SQLRestAPI' and 'DataFrameAPI' classes.
* 0.0:
    * Fundamental structure created with a simple "hello"-function.

## License

This project is licensed under the Apache-2.0 License - see the LICENSE and NOTICE file for further details.

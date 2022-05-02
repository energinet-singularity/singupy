# api-module

The api-module contains classes and functions that are used for providing communication and data between applications.

## class api.*SQLRestAPI*

This class will spin up a HTTP Rest API intended for handling SQLite requests from outside its environment (think: container serving some sort of data). By linking the 'getcall' and 'postcall' parameters to callable functions, the response to queries can be customized to many given usecases.

> _**NOTE:** The API is intended for light work and is based on the webservice included with flask. If a high load is expected, this is not a good solution. A more robust solution is expected to be developed later._

### Parameters

:arrow_right: **port(5000) : *Portnumber to listen on***  
The API is served at 'http://host:port/endpoint'. Default value is 5000 as ports < 1024 requires root privileges.

:arrow_right: **endpoint('') : *part after the slash in the url***  
The API is served at 'http://host:port/endpoint'. The default of an empty string will result in root endpoint i.e. http://host:port/

:arrow_right: **getcall(None) : *function to call when a 'GET' is received***  
This variable must point to a function that will return a dict object when called.

:arrow_right: **postcall(None) : *function to call when a 'POST' is received***  
This variable must point to a function that will return a dict object when called - the received sql-query will be sent as a string as a parameter for the function.

:arrow_right: **start(True) : *enable webserver when instantiating object***  
If set to True, the webserver will start instantly. If set to False, it can be started later with the start() function.

:arrow_right: **host('0.0.0.0') : *the host to serve on***  
This is the host where the webservice is hosted - to make it accessible from the outside it must be '0.0.0.0'.

### Properties

:arrow_right: **port : *Portnumber to listen on***  
The API is served at 'http://host:port/endpoint'.

:arrow_right: **endpoint : *part after the slash in the url***  
The API is served at 'http://host:port/endpoint'.

:arrow_right: **getcall : *function to call when a 'GET' is received***  
Function must return a dict-object.

:arrow_right: **postcall : *function to call when a 'POST' is received***  
Function will get sql-query as input and must return a valid dict.

:arrow_right: **host : *the host to serve on***  
This is the host where the webservice is hosted - to make it accessible from the outside it must be '0.0.0.0'.

:arrow_right: **thread : *a mildly modified threading.Thread object that is serving the REST api***  
This is a custom thread object based on the standard threading.Thread object. It has the ability to shutdown the webserver.

:arrow_right: **ready : *bool indicating if the service is reachable***  
This value will be true if the webservice can be reached from the main process, false otherwise.

### Methods

:arrow_right: **start(wait_for_ready : bool = True) : *Starts the thread if not already started***  
If not started, calling this method will start the server. If wait_for_ready is set, the process will only return when the 'ready' property returns true.

:arrow_right: **stop : *Stops the running webservice***  
If it is necesary to take down the webservice, i.e. to change port, endpoint or similar, call this function.

## class api.*DataFrameAPI*

This class is intende for serving pandas DataFrames via the SQLRestAPI. A 'GET' request will return metadata on current dataframes and a 'POST' request can be used to query the dataframes. Even though it includes the 'SQLRestAPI' class, it can be used wihtout the Rest API if so desired. Any changes to the content of served dataframes (including adding more - or removing dataframes) will be instantly availble for following queries.

### Parameters

:arrow_right: **dataframe(None) : *Pandas dataframe to serve at startup***  
This is the dataframe that will be served trough the API. Default (or None) results in an empty dataframe being served (which cannot be queried).

:arrow_right: **dbname('dataframe') : *database name to use for the the sql query***  
When asking the REST API for data, this will be the name of the database i.e. 'SELECT * FROM dataframe;'

:arrow_right: **query_regex(^SELECT [^;]\*;$) : *any sql query will be validated against this regex***  
As a simple security measure, the interface will by default not allow more than one query and allow only SELECT.

:arrow_right: **port(5000) : *Portnumber to listen on***  
The API is served at 'http://host:port/endpoint'. Default value is 5000 as port < 1024 requires root privileges.

:arrow_right: **endpoint(None) : *part after the slash in the url***  
The API is served at 'http://host:port/endpoint'. The default of None will result in root endpoint i.e. http://host:port/

:arrow_right: **enable_web(True) : *run the web at startup***  
If set to true (default) the webservice is started at instantiation. If webservice is unwanted or further configuration is required, set this to False.

### Properties

:arrow_right: **['name'] : *Pandas dataframe to serve***  
When accessing the items of the DataFrameAPI they return a dfconfig object (dfconfig is a child-class of the DataFrameAPI class). This object has three properties, namely 'name' that will always be the same as the items name in the DataFrameAPI, 'dataframe' which is the served dataframe and finally 'metadata' which gives some insite into the dataframe. To change the dataframe, assign it directly to the name, i.e. "my_api['name'] = my_df". If a name is set to None, it is removed from the itemset if found.

:arrow_right: **query_regex : *regex to validate sql queries***  
If required this regex can be changed to allow other types of queries as well.

:arrow_right: **web : *a SQLRestAPI Object***  
The API is run in a separate thread that can be accessed with this property.

### Methods

:arrow_right: **clear : *remove all dataframes***  
Use this method to remove all served dataframes.

:arrow_right: **metadata : *return some data on the current config***  
This will return name, column names and a rowcount for the served dataframe in a dictionary.

:arrow_right: **query(query : str) : *returns a dict with a subset of data based on the dataframe***  
The function uses the pandasql module and sends the received query to the relevant dataframe and gets the data that fits the request.

# conversion-module

The conversion-module contains functions to convert between different data or types of data.

## function conversion.*kv_to_letter*

This function takes a voltage level in kV as input and returns the corresponding standard letter.

### Parameters

:arrow_right: **kv : *voltage level as int, float or string (MUST be numerical)***  

### Returns

:arrow_right: **str : *Standard-letter corresponding the input voltage level***  

### Raises

:arrow_right: **ValueError : *Input value is not a valid numerical value***  

# verification-module

The verification-module contains functions to verify data is as expected

## function verification.*dataframe_columns*

This function takes a pandas dataframe and a list of expected columns and raises an error in case all expected columns are not found in the dataframe. It does not return anything. It is possible to verify the order of the columns as well.

### Parameters

:arrow_right: **dataframe : *dataframe that needs to have its columns verified***  

:arrow_right: **expected_columns : *list of columns that are expected in the dataframe***  

:arrow_right: **allow_extra_columns(False) : *boolean - if true the list and columns must be 1:1, otherwise the dataframe may contain more columns***  

:arrow_right: **fixed_order(False) : *boolean - if true the order of the dataframe columns and expected list must be identical***  

### Raises

:arrow_right: **ValueError : *List and dataframe columns do not match***  

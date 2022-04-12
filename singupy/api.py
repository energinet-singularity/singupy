from __future__ import annotations

# Modules related to flask/web
from flask import Flask
from flask_restful import Resource, Api, reqparse
from werkzeug.serving import make_server
import requests

# Modules related to pandas
import pandas as pd
from pandasql import PandaSQL

# Generic modules
import logging
import time
import re
from threading import Thread
from typing import Callable

# Initialize log
log = logging.getLogger(__name__)


class SQLRestAPI():
    '''
    Class for creating a SQL Rest API/endpoint that will respond to SQL queries.

    Attributes
    ----------
    port : int
        The port to expose the webservice on
    endpoint : str
        The endpoint where the webservice is available (i.e. http:/host:port/endpoint)
    getcall : Callable[[], dict]
        Function to call when endpoint is called with a 'GET' - must return a 'dict' object
    postcall : Callable[[str], dict]
        Function to call when endpoint is called with a 'POST' and a sql-query - must return a 'dict' object
    host : str
        Can be changed if required, but will default to '0.0.0.0' which will allow access from outside as well
    ready : bool
        Will return true if webservice is up and false if it is not
    thread : Thread
        Mildly modified threading.Thread object which contains the running web-service

    '''
    def __init__(self, port: int = 5000, endpoint: str = '', getcall: Callable[[], dict] = None,
                 postcall: Callable[[str], dict] = None, start: bool = True, host: str = '0.0.0.0'):
        '''
        Parameters
        ----------
        port : int
            The port to expose the webservice on
        endpoint : str
            The endpoint where the webservice is available (i.e. http:/host:port/endpoint)
        getcall : Callable[[], dict]
            Function to call when endpoint is called with a 'GET' - must return a 'dict' object
        postcall : Callable[[str], dict]
            Function to call when endpoint is called with a 'POST' and a sql-query (string) - must return a 'dict' object
        start : bool
            Enable the webhost at instantiation
        host : str
            Can be changed if required, but will default to '0.0.0.0' which will allow access from outside as well
        '''
        self.__port = port
        self.__host = host
        self.__endpoint = endpoint
        self.getcall = getcall
        self.postcall = postcall
        self.__update_process()
        if start:
            self.start()

    def __update_process(self):
        '''
        This resets the config and adds the endpoint, including the ressouce class to handle it and the two called functions
        '''
        self.__app = Flask(__name__)
        self.__api = Api(self.__app)
        self.__api.add_resource(self.__QueryData, f"/{self.endpoint}",
                                resource_class_kwargs={'GET': self.getcall, 'POST': self.postcall})
        self.thread = self.__serverThread(self.host, self.port, self.__app)

    @property
    def port(self) -> int:
        return self.__port

    @port.setter
    def port(self, value: int):
        if self.thread.is_alive():
            log.error('Tried to set port while thread is running.')
            raise AttributeError('Cannot set port when thread is running.')
        else:
            self.__port = value
            self.__update_process()

    @property
    def endpoint(self) -> str:
        return self.__endpoint

    @endpoint.setter
    def endpoint(self, value: str):
        if self.thread.is_alive():
            log.error('Tried to set endpoint while thread is running.')
            raise AttributeError('Cannot set endpoint when thread is running.')
        else:
            self.__endpoint = value
            self.__update_process()

    @property
    def host(self) -> str:
        return self.__host

    @host.setter
    def host(self, value: str):
        if self.thread.is_alive():
            log.error('Tried to set host while thread is running.')
            raise AttributeError('Cannot set host when thread is running.')
        else:
            self.__host = value
            self.__update_process()

    @property
    def ready(self) -> bool:
        if self.thread.is_alive():
            try:
                requests.get(f'http://localhost:{self.port}/{self.endpoint}')
            except Exception:
                return False
            else:
                return True
        else:
            log.error('Webserver has not been started yet.')
            return False

    def start(self, wait_for_ready: bool = True, timeout: int = 15) -> None:
        '''
        Start the webservice

        Parameters
        ----------
        wait_for_ready : bool, default True
            If set, return will only be after webservice is up
        timeout : int, default 15
            How long to wait if "wait_for_ready" is true
        '''
        if self.thread.is_alive():
            log.error('START of webservice requested, but it has already been started.')
        else:
            log.info("Starting webservice..")
            self.thread.start()
            if wait_for_ready:
                req_start = time.time()
                while not self.ready:
                    time.sleep(0.25)
                    if time.time() - req_start > timeout:
                        log.error(f'Webservice did not start within timeout of {timeout} seconds.')
                        raise TimeoutError(f'Webservice did not start within timeout of {timeout} seconds.')

    def stop(self, timeout: int = 15) -> None:
        '''
        Stop the webservice

        Parameters
        ----------
        timeout : int, default 15
            How long to wait for webservice to stop
        '''
        if self.thread.is_alive():
            log.info("Stopping webservice..")
            self.thread.shutdown()
            req_start = time.time()
            while self.thread.is_alive():
                time.sleep(0.25)
                if time.time() - req_start > timeout:
                    log.error(f'Webservice did not stop within timeout of {timeout} seconds.')
                    raise TimeoutError(f'Webservice did not stop within timeout of {timeout} seconds.')
        else:
            log.error('STOP of webservice requested, but it has not been started.')

    class __serverThread(Thread):
        '''This subclass instantiates the server-thread and adds the ability to shut down the server.'''
        def __init__(self, host, port, app):
            self.__app = app
            self.__host = host
            self.__port = port
            self.server = None
            Thread.__init__(self, daemon=True)

        def run(self):
            '''Run the webserver'''
            log.info('starting server')
            self.server = make_server(host=self.__host, port=self.__port, app=self.__app, threaded=True)
            self.server.serve_forever()

        def shutdown(self):
            '''Shutdown the webserver'''
            if self.server is None:
                log.error('Server has not been started.')
            else:
                self.server.shutdown()

    class __QueryData(Resource):
        '''Subclass which acts as a resource for the endpoints'''
        def __init__(self, **kwargs):
            self.get_callable = kwargs['GET']
            self.post_callable = kwargs['POST']

        def get(self):
            '''Handles 'GET' requests to the endpoint'''
            try:
                state = 200
                message = self.get_callable()
            except Exception as e:
                state = 400
                message = {'error': f"'GET' failed with message '{e}'"}
            return message, state

        def post(self):
            '''Handles 'POST' requests to the endpoint'''
            parser = reqparse.RequestParser()
            parser.add_argument('sql-query')
            args = parser.parse_args(strict=True)

            if args['sql-query'] is not None:
                try:
                    state = 200
                    message = self.post_callable(args['sql-query'])
                    if 'error' in message:
                        state = 400
                        message = {'error': f"Query failed with message '{message['error']}'"}
                except Exception as e:
                    state = 400
                    message = {'error': f"Query failed with message '{e}'"}
            else:
                state = 400
                message = {'error': "No query specified - use the key 'sql-query' to POST a query."}
            return message, state


class DataFrameAPI():
    '''
    Class for creating an SQL API for a pandas DataFrame.
    It includes the 'SQLRestAPI' class so it can be exposed on a webservice.

    Attributes
    ----------
    ['name'] : pandas.DataFrame
        If a name of a valid dataframe is passed, the corresponding dataframe will be returned.
    web : SQLRestAPI
        A SQLRestAPI object (See class for more info)
    query_regex : str, default='^SELECT [^;]*;$'
        Regular expression that SQL queries are validated against

    '''
    def __init__(self, dataframe: pd.DataFrame = None, dbname: str = 'dataframe', query_regex: str = r'^SELECT [^;]*;$',
                 port: int = 5000, endpoint: str = '', enable_web: bool = True):
        '''
        Parameters
        ----------
        dataframe : pd.DataFrame, default=None
            If provided, this dataframe will be served at startup
        dbname : str, default='dataframe'
            Name of the database (i.e. SELECT * FROM <dbname>)
        query_regex : str, default='^SELECT [^;]*;$'
            Regular expression that SQL queries are validated against
        port : int, default=5000
            The port to expose the webservice on
        endpoint : str, default=''
            Route/Endpoint of the webservice (i.e. http://host:port/<endpoint>)
        enable_web : bool. default=True
            If true the webservice will be started at instantiation
        '''
        # Setup DataFrameAPI and add any included dataframes
        self.__dataframes = {}
        self.query_regex = query_regex
        self[dbname] = dataframe

        # Setup WEB Host / SQLRestAPI
        self.web = SQLRestAPI(port=port, endpoint=endpoint, getcall=self.metadata, postcall=self.query, start=enable_web)

    def __len__(self):
        return len(self.__dataframes)

    def __iter__(self):
        return iter(self.__dataframes.keys())

    def __getitem__(self, name) -> pd.DataFrame:
        try:
            return self.__dataframes[name]
        except Exception:
            log.error(f"Could not access DataFrame with name '{name}' in DataFrameAPI.")
            raise KeyError(f"API Contains no DataFrame with name '{name}'.")

    def __setitem__(self, name, dataframe):
        if isinstance(dataframe, pd.DataFrame):
            self.__dataframes[name] = dataframe
        elif dataframe is None:
            if name in self.__dataframes:
                del self.__dataframes[name]
        else:
            log.error(f"Tried to set value of '{name}' dataframe to an object of '{type(dataframe)} type in DataFrameAPI.'")
            raise ValueError("'dataframe' variable must be either a valid dataframe or 'None'")

    def __delitem__(self, name):
        if name in self.__dataframes:
            del self.__dataframes[name]
        else:
            log.error(f"Could not find (and thereby delete) DataFrame with name '{name}' in DataFrameAPI.")
            raise KeyError(f"API Contains no DataFrame with name '{name}'.")

    def clear(self):
        '''Remove all dataframes from API.'''
        self.__dataframes = {}

    def metadata(self) -> dict:
        '''
        Provide metadata about the API setup - used to query what is available.

        Returns
        -------
        dict
            Dict with the query-regex and metadata about the dataframes hosted by the API.
        '''
        return {
            'query_regex': self.query_regex,
            'dataframes': {dfname: {'columns': list(self[dfname].columns),
                                    'rowcount': self[dfname].shape[0]} for dfname in self}
        }

    def query(self, query: str) -> dict:
        '''
        Return data corresponding to the given query

        Parameters
        ----------
        query : str
            The query to respond to in SQLite style.

        Returns
        -------
        dict
            Dict with the data returned from the dataframe.
        '''
        log.debug(f"Received SQL Query: {query}")

        # Make sure sql-query fits regex - used for security reasons.
        if not re.search(self.query_regex, query):
            log.error('Tried to query data that did not fit the query regex.')
            raise PermissionError(f"Query was denied due to not matching regex '{self.query_regex}'")

        # Only include dataframes that are not empty
        dbdict = {dfname: self[dfname] for dfname in self if not self[dfname].empty}

        try:
            return PandaSQL(persist=False)(query, dbdict).to_dict()
        except Exception as e:
            if "no such table" in e.__str__():
                return {'error': "Requested dataframe does not exist or is empty."}
            else:
                return {'error': e}

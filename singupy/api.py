# Generic
from modulefinder import Module
import re
import os
import logging
from threading import Thread
from typing import Union, List
from datetime import datetime, timedelta, timezone

# For DataFrameAPI
from flask import Flask
from flask_restful import Resource, Api, reqparse
import pandas as pd
from pandasql import sqldf

# For FileManager
import smbclient as smb_src
import smbclient as smb_dst


# Initialize log
log = logging.getLogger(__name__)


class DataFrameAPI():
    def __init__(self, data: pd.DataFrame, host: str = '0.0.0.0', port: int = 80,
                 query_regex: str = r'^SELECT [^;]*;$', dataname: str = 'dataframe'):
        # Load dataframe and setup flask api environment
        self.update_data(data)
        self.__app = Flask(__name__)
        self.__api = Api(self.__app)

        # Add resource with constructur parameters to load dataframe and query regex
        self.__api.add_resource(self.__QueryData, f"/{dataname}",
                                resource_class_kwargs={'get_df': self.__get_df, 'query_regex': query_regex})

        # Setup thread and start it
        self.thread = Thread(target=self.__run, args=(host, port))
        self.thread.start()

    def __run(self, host, port):
        # Starts the flask app
        self.__app.run(host=host, port=port)

    def __get_df(self) -> pd.DataFrame:
        # Used to send the dataframe to the __querydata subclass
        return self.data

    def update_data(self, data: pd.DataFrame):
        # Validate input
        if not isinstance(data, pd.DataFrame):
            raise ValueError("'data' is not a valid pandas dataframe.")

        self.data = data

    class __QueryData(Resource):
        def __init__(self, **kwargs):
            # Load dataframe
            self.__get_df = kwargs['get_df']
            self.data = self.__get_df()

            # Regex to validate query
            self.query_regex = kwargs['query_regex']

        def get(self):
            try:
                return {'columns': list(self.data.columns), 'rowcount': self.data.shape[0]}, 200
            except Exception as e:
                return {'error': f"'GET' failed with message '{e}'"}, 401

        def post(self):
            parser = reqparse.RequestParser()
            parser.add_argument('sql-query')
            parser.add_argument('pd-query')
            args = parser.parse_args(strict=True)

            if None not in (args['sql-query'], args['pd-query']):
                return {'error': "Two queries specified - either use 'sql-query' or 'pd-query'."}, 401

            elif args['sql-query'] is not None:
                log.debug(f"SQL Query: {args['sql-query']}")

                # Make sure sql-query fits regex - used for security reasons.
                if not re.search(self.query_regex, args['sql-query']):
                    log.error(f"User query was denied due to not matching regex '{self.query_regex}'")
                    return {'error': f"Query must fit '{self.query_regex}' regex."}, 401

                # pandasql needs a variable in globals or locals - so give it one
                global sqldata
                sqldata = self.data

                try:
                    return sqldf(args['sql-query'], globals()).to_dict(), 200
                except Exception as e:
                    return {'error': f"Query failed with message '{e}'", 'example': "sql-query=SELECT * FROM sqldata WHERE first_name='Evan';"}, 401

            elif args['pd-query'] is not None:
                log.debug(f"PD Query: {args['pd-query']}")
                try:
                    return self.data.query(args['pd-query']).to_dict(), 200
                except Exception as e:
                    return {'error': f"Query failed with message '{e}'", 'example': "pd-query=first_name=='Evan'"}, 401

            else:
                return {'error': "No query specified - either use 'sql-query' or 'pd-query'."}, 401

class FileManager():
    __src: dict = {
        'path': None,
        'remote': False,
        'func': {},
        'credentials': {'user': None, 'pass': None}
    }
    __dst: dict = {
        'path': None,
        'remote': False,
        'files': [],
        'func': {},
        'credentials': {'user': None, 'pass': None}
    }

    def __init__(self, source: str, destination: str, max_age_s: int = None, file_regex: Union[str, List[str]] = '.*',
                 smb_username: str = None, smb_password: str = None):
        self.source = source
        self.destination = destination
        self.max_age_s = max_age_s
        if isinstance(file_regex, list):
            self.file_regex_list = file_regex
        else:
            self.file_regex_list = [file_regex]
        self.set_credentials(smb_username, smb_password)

    def __attach_credentials(self):
        for config in [self.__src, self.__dst]:
            if config['remote']:
                cred = config['credentials']
                config['func']['client'].ClientConfig(username=cred['user'], password=cred['pass'])

    def __update_config_func(self, source: bool, isremote: bool):
        if source:
            func = self.__src['func']
            smb = smb_src
        else:
            func = self.__dst['func']
            smb = smb_dst

        if isremote:
            func['client'] = smb
            func['remove'] = smb.remove
            func['scandir'] = smb.scandir
        else:
            func['client'] = None
            func['remove'] = os.remove
            func['scandir'] = os.scandir

    def __update_config(self, path: str, source: bool):
        if source:
            config = self.__src
        else:
            config = self.__dst
            config['files'] = []

        config['path'] = path
        if path.startswith('\\\\') or path.startswith('//'):
            config['remote'] = True
        else:
            config['remote'] = False

        self.__update_config_func(source, config['remote'])
        self.__attach_credentials()

    @property
    def source(self):
        return self.__src['path']

    @source.setter
    def source(self, path: str):
        self.__update_config(path, True)

    @property
    def destination(self):
        return self.__dst['path']

    @destination.setter
    def destination(self, path: str):
        self.__update_config(path, False)

    def set_credentials(self, username: str = None, password: str = None, for_source: bool = True, for_destination: bool = True):
        cred = {'user': username, 'pass': password}

        if for_source:
            self.__src['credentials'] = cred
        if for_destination:
            self.__dst['credentials'] = cred
        
        self.__attach_credentials()
    
    def killme(self):
        print(smb_src.ClientConfig.username)
        print(smb_dst.ClientConfig.username)

    def transfer_files(self):
        filelist = self.__src['func']['scandir'](self.__src['path'])
        for file in [{'name': file.name, 'mtime': file.stat().st_mtime} for file in filelist if file.is_file()]:
            # Check if the file (with modify timestamp) is known
            if file not in self.__dst['files']:
                # Check if the file is older than max age - skip it if so
                if self.max_age_s is not None:
                    file_age_s = (datetime.utcnow() - datetime.utcfromtimestamp(file['mtime'])).total_seconds()
                    if file_age_s > self.max_age_s:
                        log.debug(f"Ignoring file '{file['name']}' because it is '{file_age_s}' seconds old (limit is '{self.max_age_s}')")
                        self.__dst['files'].append(file)
                        continue
                
                # Remove any old file-reference
                self.__dst['files'] = [d_file for d_file in self.__dst['files'] if d_file['name'] != file['name']]
                
                # move file
                self.__dst['files'].append(file)
            

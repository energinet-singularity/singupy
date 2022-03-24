from flask import Flask
from flask_restful import Resource, Api, reqparse
import pandas as pd
import re
import logging
from threading import Thread
from pandasql import sqldf

# Initialize log
log = logging.getLogger(__name__)


class DataFrameAPI():
    def __init__(self, data: pd.DataFrame, host: str = '0.0.0.0', port: int = 80,
                 query_regex: str = r'^SELECT [^;]*;$', dataname: str = 'dataframe'):
        # Load dataframe and setup flask api environment
        self.update_data(data, dataname)
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

    def __get_df(self):
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
                    return {'error': f"Query failed with message '{e}'", 'example': "pd-query=first_name=='Evan'"}, 401

            elif args['pd-query'] is not None:
                log.debug(f"PD Query: {args['pd-query']}")
                try:
                    return self.data.query(args['pd-query']).to_dict(), 200
                except Exception as e:
                    return {'error': f"Query failed with message '{e}'", 'example': "pd-query=first_name=='Evan'"}, 401

            else:
                return {'error': "No query specified - either use 'sql-query' or 'pd-query'."}, 401

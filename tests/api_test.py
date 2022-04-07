import pytest
import logging
from singupy import api
import requests
import pandas as pd
import json

log = logging.getLogger(__name__)

# Constants for tests
PORT = 5010
ENDPOINT = 'dataframe'


# ----- SQLRestAPI -----
def GetDummy():
    return {"RESP": "GET"}


def PostDummy(query: str):
    if 'SELECT' in query:
        return {"REST": "POST", "QUERY": query}
    else:
        raise ValueError('I pity the fool!')


@pytest.fixture
def SQLRestAPI_resource():
    # Use fixture to make sure web service is taken down after testing
    my_api = api.SQLRestAPI(port=PORT, endpoint=ENDPOINT, getcall=GetDummy, postcall=PostDummy, start=False)
    yield my_api

    # Clean up after test (make sure web gets taken down)
    if my_api.thread.is_alive():
        my_api.stop()


def test_SQLRestAPI(SQLRestAPI_resource):
    # Setup web - don't start it yet
    web = SQLRestAPI_resource
    assert web.ready is False
    assert web.port == PORT
    assert web.endpoint == ENDPOINT

    # Change parameters and verify they changed
    web.endpoint = "dummy"
    web.port = PORT + 10
    assert web.port == PORT + 10
    assert web.endpoint == "dummy"

    # Start webservice and verify trying to change parameters raises an error
    web.start()
    assert web.ready is True
    with pytest.raises(Exception):
        web.endpoint = "dummy"
    with pytest.raises(Exception):
        web.port = PORT+10

    # Validate GET
    assert requests.get(f'http://localhost:{web.port}/{web.endpoint}').json() == json.dumps(GetDummy())

    # Validate POST
    query = "SELECT * FROM A-TEAM;"
    assert requests.post(f'http://localhost:{web.port}/{web.endpoint}',
                         json={"sql-query": query}).json() == json.dumps(PostDummy(query))

    # Validate bad query does not kill web, but returns error
    query = "INSERT INTO A-TEAM (name) VALUES ('Karsten');"
    assert requests.post(f'http://localhost:{web.port}/{web.endpoint}', json={"sql-query": query}).status_code == 400

    # Validate missing query does not kill web, but returns error
    query = ""
    assert requests.post(f'http://localhost:{web.port}/{web.endpoint}', json={"sql-query": query}).status_code == 400

    # Validate incorrect key does not kill web, but returns error
    query = "SELECT * FROM A-TEAM;"
    assert requests.post(f'http://localhost:{web.port}/{web.endpoint}',
                         json={"sql-query": query, "database": "A-TEAM"}).status_code == 400

    # Validate bad endpoint does not kill web, but returns error
    query = "SELECT * FROM A-TEAM;"
    assert requests.post(f'http://localhost:{web.port}/{web.endpoint}xx', json={"sql-query": query}).status_code == 404

    web.stop()
    assert web.ready is False


# ----- DataFrameAPI -----
@pytest.fixture
def DataFrameAPI_resource():
    # Use fixture to make sure web service is taken down after testing
    my_api = api.DataFrameAPI(port=PORT, endpoint=ENDPOINT)
    yield my_api

    # Clean up after test (make sure web gets taken down)
    if my_api.web.thread.is_alive():
        my_api.web.stop()


def test_DataFrameAPI(DataFrameAPI_resource, caplog):
    # Setup of test-data
    minidata = {"name": ["tom", "jerry"], "age": [80, 82]}
    mini_df = pd.DataFrame(minidata)

    # Test creation of api with empty dataset
    test_api = api.DataFrameAPI(dataframe=pd.DataFrame(), dbname='NoData', enable_web=False)
    assert test_api['NoData'].empty

    test_api = DataFrameAPI_resource

    # Test Dataframe can be set and reset using all valid methods
    test_api['MiniData'] = pd.DataFrame()
    assert test_api['MiniData'].empty

    test_api['MiniData'] = mini_df
    assert test_api['MiniData'].equals(mini_df)

    test_api['MiniData'] = pd.DataFrame()
    assert test_api['MiniData'].empty

    # Verify dataset can be removed and result in keyerror
    test_api['MiniData'] = None

    with pytest.raises(Exception):
        _ = test_api['MiniData']

    # Test Metadata function
    test_api['MiniData'] = mini_df
    test_api['NewData'] = mini_df
    test_api['NoData'] = pd.DataFrame()
    assert test_api.metadata()['query_regex'] == test_api.query_regex
    assert len(test_api.metadata()['dataframes']) == 3
    assert 'MiniData' in test_api.metadata()['dataframes']
    assert 'NewData' in test_api.metadata()['dataframes']
    assert 'NoData' in test_api.metadata()['dataframes']

    # Test __len__ and __iter__ response
    assert len(test_api) == 3
    for df in test_api:
        assert isinstance(df, str)
        assert isinstance(test_api[df], pd.DataFrame)

    # Test Query function (incl. query regex)
    assert 'error' in test_api.query("SELECT * FROM NoData;")
    assert test_api.query("SELECT name FROM MiniData;") == {'name': mini_df.loc[:, "name"].to_dict()}
    assert test_api.query("SELECT name FROM MiniData;") == {'name': mini_df.loc[:, "name"].to_dict()}

    # Test web service is working
    response = requests.get(f'http://localhost:{test_api.web.port}/{test_api.web.endpoint}')
    assert response.status_code == 200
    assert response.json() == json.dumps(test_api.metadata())

    response = requests.post(f'http://localhost:{test_api.web.port}/{test_api.web.endpoint}',
                             json={"sql-query": "SELECT * FROM MiniData;"})
    assert response.status_code == 200
    assert response.json() == json.dumps(test_api.query("SELECT * FROM MiniData;"))

    minidata['speed'] = [10, 15]
    test_api['MiniData'] = pd.DataFrame(minidata)
    response = requests.post(f'http://localhost:{test_api.web.port}/{test_api.web.endpoint}',
                             json={"sql-query": "SELECT * FROM MiniData;"})
    assert response.status_code == 200
    assert response.json() == json.dumps(test_api.query("SELECT * FROM MiniData;"))

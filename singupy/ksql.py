"""
kSQL helper module using requests package.
"""
from __future__ import annotations
from typing import List
import logging
import re
import requests

log = logging.getLogger(__name__)


class config:
    name: str = None
    type: str = None
    create_request: str = None
    create_actual: str = None
    create_built: str = None
    children: List[config] = []

    def __init__(self, create_string: str = '', is_actual: bool = False):
        if create_string == '':
            raise ValueError("'create_string' cannot be an empty string'")

        match = re.search(r'^CREATE (?P<TYPE>\S+) (?P<NAME>\S+) .*;$')
        assert match, f"Create-string '{create_string}' does not fit required form 'CREATE <TYPE> <NAME> ..;'"
        self.type = match.group('TYPE').upper()
        self.name = match.group('NAME')
        if is_actual:
            self.create_actual = create_string
        else:
            self.create_request = create_string
        assert self.type in ['STREAM', 'TABLE'], f"Unknown type '{self.type}', should be either 'TABLE' or 'STREAM'"

    def add_child(self, child: config = None, create_string: str = None, is_acual: bool = False):
        if child is not None and create_string is None:
            self.children.append(child)
        elif create_string is not None and child is None:
            self.children.append(config(create_string, is_acual))
        elif create_string is None and child is None:
            raise ValueError("'child' or 'create_string' must be set.")
        else:
            raise ValueError("Both 'child' and 'create_string' cannot be set.")


class manager:
    broker: str = None
    configs: list(config) = []

    def __init__(self, broker: str, configuration: list(config), port: int = 8088):
        match = re.search(r'^(?P<http>https?:\/\/)?(?P<host>[^:]*)(?P<port>:\d{3,7})?$', broker)
        if not match:
            raise ValueError(f"Could not interpret broker from '{broker}'")
        if not (isinstance(configuration, list) and all(isinstance(c, config) for c in configuration)):
            raise ValueError(f"A valid list of configurations was not supplied")

        if match.group('port') is not None:
            self.broker = f"{match.group('host')}{match.group('port')}"
        else:
            self.broker = f"{match.group('host')}:{port}"
        log.debug(f"Set broker to '{self.broker}'")

        self.configs = configuration

    def validate(self):
        if not test_connection(self.broker):
            raise ConnectionError(f"Connection to '{self.broker}' cannot be established.")

        for item in self.configs:
            assert_configuration(self.broker, item)


def dict_dive(dictionary: dict, keylist: list, default_return=None):
    # This should be moved to a generic place instead of in the ksql module
    assert isinstance(dictionary, dict), "Invalid dictionary"
    assert isinstance(keylist, dict), "Invalid list of keys"

    child = dictionary.get(keylist[0], None)

    if isinstance(child, dict) and len(keylist) > 1:
        return dict_dive(child, keylist[1:], default_return)

    if len(keylist) == 1 and child is not None:
        return child

    return default_return


# -- High level functionality related to kSQL --
def test_connection(host: str) -> bool:
    try:
        response = requests.get(f'http://{host}/info')
    except Exception:
        log.error(f"Received error when trying to connect to '{host}'.")
        return False

    log.debug(f"Got following response from '{host}': {response.text}")

    if response.status_code != 200:
        log.error(f"Got status code '{response.status_code}' when trying to get info from ksql server '{host}'.")
        return False

    try:
        server_status = response.json()['KsqlServerInfo']['serverStatus']
        if server_status == 'ERROR':
            log.error(f"Got serverStatus '{server_status}' when querying info from ksql server '{host}'.")
            return False
    except Exception:
        log.error(f"Received incorrect formatted reponse from '{host}'.")
        return False

    return True


def post_query(host: str, query: str, properties: dict = {}) -> list(dict):
    log.debug(f"Sending POST to '{host}', query: {query}")
    if properties != {}:
        log.debug(f"Stream properties: {properties}")

    try:
        response = requests.post(f'http://{host}/ksql', json={"ksql": query, "streamsProperties": properties})
    except Exception as e:
        log.exception(e)
        raise(f"Got error when using POST on ksql '{host}'.")

    return response.json()


def get_topics(host: str) -> list:
    return dict_dive(post_query(host, "LIST TOPICS;")[0], ['topics'], [])


# -- Management of configurations --
def __get_create_statement(host: str, configuration: config) -> str:
    return dict_dive(post_query(host, f"DESCRIBE {configuration.name};")[0], ['sourceDescription', 'statement'])


def create_configuration(host: str, configuration: config):
    response = post_query(configuration.create_request)
    status = dict_dive(response[0], ['commandStatus', 'status '], 'ERROR')
    if status != 'SUCCESS':
        # This function should be expanded to handle 'QUEUED', 'PARSING', 'EXECUTING' and perhaps 'TERMINATED' status as well
        raise ValueError(f"Create of '{configuration.type}' with name '{configuration.name}'"
                         " resulted in '{status}' response - expected 'SUCCESS'.")

    configuration.create_built = __get_create_statement(host, configuration)

    if configuration.create_built != configuration.create_request:
        log.warning('The requested configuration does not match the built configuration 1:1.')
        log.debug(f"Requested string: {configuration.create_request}")
        log.debug(f"Built string: {configuration.create_built}")

    for child in configuration.children:
        create_configuration(host, child)


def delete_configuration(host: str, configuration: config):
    for child in configuration.children:
        delete_configuration(host, child)

    status = dict_dive(post_query(f"DROP {configuration.type} {configuration.type};")[0],
                       ['commandStatus', 'status '], 'INVALID')
    if status != 'SUCCESS':
        # This function should be expanded to handle 'QUEUED', 'PARSING', 'EXECUTING' and perhaps 'TERMINATED' status as well
        raise ValueError(f"Drop of '{configuration.type}' with name '{configuration.name}'"
                         " resulted in '{status}' response - expected 'SUCCESS'.")

    configuration.create_built = None
    configuration.create_actual = None


def assert_configuration(host: str, configuration: config):
    for child in configuration.children:
        assert_configuration(host, child)

    log.info(f"Asserting '{configuration.type}' with id '{configuration.name}' has been configured correctly.")
    configuration.create_actual = __get_create_statement(host, configuration)

    if configuration.create_actual is None:
        # Configuration is missing - create it.
        create_configuration(host, configuration)
    elif configuration.create_actual in [configuration.create_request, configuration.create_built]:
        # Configuration is as expected - do nothing
        pass
    else:
        # Configuration does not match (probably changed) - delete and create
        delete_configuration(host, configuration)
        create_configuration(host, configuration)

import pandas as pd
import logging

log = logging.getLogger(__name__)


def dataframe_columns(dataframe: pd.DataFrame, expected_columns: list, allow_extra_columns: bool = False):
    """
    Verify if columns in dataframe contains expected colums.
    Parameters
    ----------
    dataframe : pd.Dataframe
        Pandas dataframe.
    expected_columns : list
        List of expected columns.
    allow_extra_columns : bool
        Set True if columns in addition to the expected columns are accepted.
        (Default = False)
    Raises
    ------
    ValueError
        If dataframe does not contain expected colulmns
    """
    dataframe_columns = list(dataframe.columns)

    # If extra columns are allowed in dataframe, check if expected columns are present in dataframe
    if allow_extra_columns:
        if all(item in dataframe_columns for item in expected_columns):
            log.info('Dataframe contains expected columns.')
        else:
            raise ValueError(f"The columns {list(set(expected_columns)-set(dataframe_columns))} are missing in the dataframe")

    # If only expected columns are allowed in dataframe, check if only expected columns are in dataframe
    else:
        if sorted(dataframe_columns) == sorted(expected_columns):
            log.info('Dataframe contains only expected columns.')
        else:
            raise ValueError(f"The columns: '{dataframe_columns}' in dataframe does not match expected columns: " +
                             f"'{expected_columns}'.")

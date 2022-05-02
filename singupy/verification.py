import pandas as pd
import logging

log = logging.getLogger(__name__)


def dataframe_columns(dataframe: pd.DataFrame, expected_columns: list, allow_extra_columns: bool = False,
                      fixed_order: bool = False):
    """
    Verify if columns in dataframe contains expected colums, and order if the 'fixed_order' bool is True.

    Parameters
    ----------
    dataframe : pd.Dataframe
        Pandas dataframe.
    expected_columns : list
        List of expected columns.
    allow_extra_columns : bool
        Set True if columns in addition to the expected columns are accepted.
        (Default = False)
    fixed_order : bool
        Set True if columns must be in the same order as the list.
        (Default = False)
    Raises
    ------
    ValueError
        If list contains items not found in dataframe column names
        or if list column names exist that are not in list (while allow_extra_columns is False)
        or if the expected order is incorrect and fixed_order is True.
    """
    # Note: If this function gets more advanced, contemplate using deepdiff module in stead.

    dataframe_columns = list(dataframe.columns)

    log.debug(f"DataFrame Columns: {dataframe_columns}")
    log.debug(f"Expected Columns: {expected_columns}")

    # Create a list of column positions in the dataframe
    try:
        pos_list = [col_no - dataframe_columns.index(col_name) for col_no, col_name in enumerate(expected_columns)]
    except Exception:
        raise ValueError("One or more expected columns were not found in data dataframe.") from None

    # Check that dataframe columns and expected columns contain same elements
    if allow_extra_columns is False and set(dataframe_columns) != set(expected_columns):
        raise ValueError("Unexpected columns were found in the dataframe.")

    # Verify order is correct if this is a requirement
    if fixed_order is True:
        if (allow_extra_columns is False and not all(pos == 0 for pos in pos_list)) or \
          allow_extra_columns is True and sorted(pos_list, reverse=True) != pos_list:
            raise ValueError("Order of columns is incorrect.")

import pytest
import logging
import pandas as pd
from singupy.verification import dataframe_columns

log = logging.getLogger(__name__)


def test_dataframe_columns():
    testframe = pd.DataFrame({"col1": [0, 1, 2], "col2": [4, 5, 6]})

    # Test verification works for testframe with identical column list
    dataframe_columns(testframe, ["col1", "col2"])

    # Test verification works for testframe with partial column list
    dataframe_columns(testframe, ["col1"], True)

    # Check raise error in case partial list, but 1:1 compare
    with pytest.raises(ValueError):
        dataframe_columns(testframe, ["col1"], False)

    # Check raise error in case missing col in 1:1 compare
    with pytest.raises(ValueError):
        dataframe_columns(testframe, ["col1", "col3"], False)

    # Check raise error in case missing col in partial compare
    with pytest.raises(ValueError):
        dataframe_columns(testframe, ["col1", "col3"], True)

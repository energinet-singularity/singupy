import pytest
import logging
from singupy.conversion import kv_to_letter

log = logging.getLogger(__name__)


def test_kv_to_letter():
    # Check a list of most used kV
    io_dict = {400: 'C',
               220: 'D',
               150: 'E',
               132: 'E',
               60: 'F',
               50: 'G',
               33: 'H',
               20: 'J',
               10: 'K'}

    for kv in io_dict.keys():
        assert kv_to_letter(kv) == io_dict[kv]

    # Check string with numerical works as well
    assert kv_to_letter("380") == 'C'

    # Check raise error in case bad value is sent
    with pytest.raises(ValueError):
        kv_to_letter("fejl")

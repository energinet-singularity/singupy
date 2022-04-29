def kv_to_letter(kv: int) -> str:
    """Converts voltage level to voltage letter representation.
    Parameters
    ----------
    kv : int
        Voltage level in kV.
    Returns
    -------
    str
        Voltage letter.
    Example
    -------
        >>> convert_kv_to_letter(400)
        C
    """
    try:
        kv = int(kv)
    except Exception:
        raise ValueError(f'"{kv}" is {type(kv)}, and not a valid numerical value.') from None

    ranges = {(380, 420): 'C',
              (220, 380): 'D',
              (110, 220): 'E',
              (60, 110): 'F',
              (45, 60): 'G',
              (30, 45): 'H',
              (20, 30): 'J',
              (10, 20): 'K',
              (6, 10): 'L',
              (1, 6): 'M'}

    for (lower, upper) in ranges.keys():
        if lower <= kv < upper:
            return ranges[(lower, upper)]

    if kv >= 420:
        return 'B'
    elif kv < 1:
        return 'N'
    else:
        raise ValueError(f'The value "{kv}" does not match a valid voltage region.')

from td import *
from typing import Optional, Union
def cast_cell(cell: td.Cell) -> Optional[Union[str, float, int]]:
    """ Try to cast cell value to int or float, return string if not possible """
    value = cell.val.strip()
    if value == '':
        return None
    try:
        int(value)
        return int(value)
    except ValueError:
        try:
            float(value)
            return float(value)
        except ValueError:
            return value


from td import *
from typing import Optional, Union
def get_cell_cast(
    t: td.tableDat,
    row: Union[int, str], 
    col: Union[int, str]
) -> Optional[Union[str, float, int]]:
    maybe_cell = t[row,col]
    if maybe_cell:
        return cast_cell(maybe_cell)





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


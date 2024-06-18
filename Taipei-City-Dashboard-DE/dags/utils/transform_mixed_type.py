

def mapping_category_ignore_number(string, cate):
    '''
    Map the string to the category, ignore the number in the string.
    If the string is not in the category, return the original string.
    
    Args:
    ----------
    string: str. The string to be mapped.
    cate: dict. The mapping category.

    Example
    ----------
    mapping_category_ignore_number('1', {'1': 'A', '2': 'B'})
    mapping_category_ignore_number('2', {'1': 'A', '2': 'B'})
    mapping_category_ignore_number('3', {'1': 'A', '2': 'B'})
    '''
    try:
        return cate[string]
    except KeyError:
        return string


def given_string_to_none(raw_str: str, given_str: str, mode: str='start'):
    '''
    Convert given string to None if it matches the given string, otherwise keep the original string.
    This funciton can handle data type issue.
    
    Args:
    ----------
    raw_str: str. The string to be checked.
    given_str: str. The string to be checked.
    mode: str. Default is 'start'. The mode of checking.
    'start' means checking if the input string starts with the given string.
    'end' means checking if the input string ends with the given string.
    'full' means checking if the input string is the same as the given string.
    
    Example
    ----------
    given_string_to_none('-99', '-99')
    given_string_to_none('-990.00', '-99')
    given_string_to_none('-90.00', '-99')
    given_string_to_none('-990.00', '-99', mode='end')
    given_string_to_none('-990.00', '-99', mode='test')
    '''

    if mode == 'start':
        try:
            is_target = raw_str.startswith(given_str)
        except Exception:
            is_target = False
    elif mode == 'end':
        try:
            is_target = raw_str.endswith(given_str)
        except Exception:
            is_target = False
    elif mode == 'full':
        try:
            is_target = raw_str == given_str
        except Exception:
            is_target = False
    else:
        raise ValueError("mode should be one of 'start', 'end' or 'full'")

    if is_target:
        return None
    return raw_str

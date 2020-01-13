'''
Copyright (c) 2020 Cisco and/or its affiliates.

A copy of the License (MIT License) can be found in the LICENSE.TXT
file of this software.

Author: Jared T. Smith <jarmith@cisco.com>
Created: Jan 10, 2020
updated

'''

def split_string_list(string_list):
    """
    Parameters:
    string_list -- Comma separated string

    Return:
    List containing tokenized portions of the string
    """
    return [x.strip() for x in string_list.split(',')]
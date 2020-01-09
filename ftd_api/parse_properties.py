'''
Copyright (c) 2020 Cisco and/or its affiliates.

A copy of the License (MIT License) can be found in the LICENSE.TXT
file of this software.

Author: Jared T. Smith <jarmith@cisco.com>
Created: Jan 3, 2020
'''

import logging


def file_to_dict(properties_file):
    """
    This method will take a properties file (key=value one per line), load
    it, and return a dictionary with the contents.

    Parameters:

    properties_file -- Path to the properties file

    Returns:

    Dictionary with the contents
    """
    return_dict = {}
    with open(properties_file, 'r') as file_handle:
        for line in file_handle:
            # This will allow handling of end of line comments and set line to
            # '' for whitespace and lines that just have comments.
            line = line.split('#')[0].strip()
            if line and line != '':
                # if we don't have an equals sign (or more than one) ignore and
                # warn
                line_parts = line.split('=')
                if len(line_parts) == 2:
                    # add to map we have a key and value
                    return_dict[line_parts[0]] = line_parts[1]
                else:
                    logging.warn(f"Can't parse properties file line: {line}")
    return return_dict

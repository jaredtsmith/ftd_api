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
            # removing leading and trailing whitespace before parse
            line = line.strip()
            # Skip lines that start with a comment 
            if line.startswith('#'):
                continue
            # There could be a couple of cases we'll support:
            """
            address=host.cisco.com
            address=host.cisco.com #This is a host 
            password=ABCD123#
            """
            # So there are cases where:
            # - No comment exists
            # - Comment follows the value after a space
            # - Value contains a # (no space before it) - In this case we want to keep the # in the value for things like a password
            hash_location = line.find('#')
            if hash_location != -1 and line[hash_location - 1] == ' ':
                # found a hash need to differentiate second and third cases
                # check if the previous character is a space if so truncate after the hash
                # we know it doesn't start with a hash so we should be able to safetly do -1
                # truncate after the hash
                line = line[0:hash_location-1]
            if line and line != '':
                # if we don't have an equals sign (or more than one) ignore and
                # warn
                line_parts = line.split('=')
                if len(line_parts) == 2:
                    # add to map we have a key and value
                    # strip the key and value to be safe from extra padding
                    return_dict[line_parts[0].strip()] = line_parts[1].strip()
                else:
                    logging.warn(f"Can't parse properties file line: {line}")
    return return_dict

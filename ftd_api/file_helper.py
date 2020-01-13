'''
Copyright (c) 2020 Cisco and/or its affiliates.

A copy of the License (MIT License) can be found in the LICENSE.TXT
file of this software.

Author: Jared T. Smith <jarmith@cisco.com>
Created: Jan 10, 2020
updated

'''
def print_string_to_file(filename, string_contents):
    """
    This is a helper method to write the contents of a string into a file.
    Parameters:

    filename -- The name of the file to write the string into
    string_contents -- The string that will be written
    """
    with open(filename, 'w') as file_handle:
        file_handle.write(string_contents)

def read_string_from_file(filename):
    """
    This is a helper method to write the contents of a string into a file.
    Parameters:

    filename -- The name of the file to write the string into
    string_contents -- The string that will be written
    """
    with open(filename, 'r') as file_handle:
        return file_handle.read()
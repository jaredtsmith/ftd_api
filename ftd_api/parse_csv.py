'''
Copyright (c) 2020 Cisco and/or its affiliates.

A copy of the License (MIT License) can be found in the LICENSE.TXT
file of this software.

Author: Jared T. Smith <jarmith@cisco.com>
Created: Dec 18, 2019
updated

'''

import csv
import json
import re
import os
import logging

NONE_CSV_VALUE = '-=NONE/NULL=-'


def get_value_at_index(my_list, index_list):
    """This method will take a base list and traverse
    the contained multi-dimensional array.

    Parameters:

    my_list -- This is the base list object
    index_list -- This is a list of nested indexes in a multi-dimensional array for
                  example:  [2][3][4]

    If it cannot reach the requested index None will be returned
    If it can reach the index the element at that index will be returned
    """
    if type(my_list) != list:
        raise Exception('my_list is not a list: '+str(type(my_list)))

    if type(index_list) != list:
        raise Exception('index_list is not a list: '+str(type(index_list)))

    current_list = my_list
    # Keep stepping into the multi-dimensional array a level deeper
    for index in index_list:
        try:
            nested_object = current_list[index]
            current_list = nested_object
        except IndexError:
            return None
    return current_list


def set_value_at_list_index(my_list, index_list, value):
    """
    The purpose of this method is to set a value into a multi-dimensional array

    This method takes three parameters:

    my_list -- The list to modify (cannot be null)
    index_list -- Ordered list of array indexes to build out nested array structures e.g. [2][3][4]
    value -- The value to insert at the index

    If the list isn't as long required to get to that element it will pad the list with None values
    If  there are existing nested lists it will build upon those
    """
    if type(my_list) != list:
        raise Exception('my_list is not a list: '+str(type(my_list)))

    if type(index_list) != list:
        raise Exception('index_list is not a list: '+str(type(index_list)))

    # current_list is the pointer to the current location in the nested list
    current_list = my_list
    num_array_dimensions = len(index_list)
    count = 0
    for index in index_list:
        # Populate the list with None values to build it out to the correct size
        for i in range(0, int(index)+1):
            # attempts to index to the array element if it fails it appends an
            # element on the list so we can index there.  The goal is to index to
            # the point where we need to get to the next list
            try:
                current_list[i]
            except IndexError:
                current_list.append(None)
        # If we are before the last index make sure the nested list is created
        if count < num_array_dimensions-1:
            # Fetch existing element at index we need to drill into
            existing_list = current_list[index]
            # If it is none replace with a list so we can work on the next dimension
            if existing_list is None:
                current_list[index] = []
                current_list = current_list[index]
            else:
                current_list = existing_list
        count += 1
    # At the last index assign the value
    current_list[index_list[-1]] = value


def update_list_in_dict(dict_to_set, variable, index_list, variable_value):
    """
    This method will insert/update a list in a dictionary and set the value at a given
    index.  Any values that have not yet been set in the list will be padded with None

    The variable in this case is:
    dict_to_set[variable]

    Where it will index to the appropriate nested index and set the value

    This method takes 4 parameters:

    dict_to_set -- A dictionary to find the variable in
    variable -- The variable in the dict (string name) where the list should be inserted/updated
    index_list -- This is the list of array indexes could be one or many [2][3][4]
    variable_value -- The actual value to set at the index
    """
    new_list = None
    if variable in dict_to_set:
        # If it exists get the list
        new_list = dict_to_set[variable]
        if type(new_list) != list:
            raise Exception('new_list is not a list: '+str(type(new_list)))
    else:
        # If not create it
        new_list = []
        dict_to_set[variable] = new_list
    # List has been created now set the value at the index in the list
    set_value_at_list_index(new_list, index_list, variable_value)


def set_variable_in_dict(dict_to_set, variable_name, variable_value):
    """
    This method takes a dictionary and a compound variable name as shown below as well
    as a value to set under that variable.  The algorithm here is to go one level at a
    time and then recurse to keep the logic simple.

    Arguments:

    dict_to_set --  Dictionary to set the variable_name into
    variable_name -- Variable (key) to set in the dictionary
    variable_value --  Value to set under the key



    Allowing for the following structures:

    - variable_name[0]  as a list
    - variable_name.nestedVariable
    - variable_name.nestedVariable[0], variable_name.nestedVariable[1]
    - variable_name.nestedVariable[0].othervar ...
    - variable_name[2][3].nestedVariableB
    """
    # split token on "." to find the parts to build out the dict
    token_list = variable_name.split('.')
    # This regex will split the first token into two parts:
    # - The variable_name name (without array indexing)
    # - The array indexes [2][3][4]
    match = re.search(r'([\w|\d]+)(\[.*\])', token_list[0])
    parsed_variable_name = None
    index_list = None
    if match is not None:
        # This is the case where we found a match and we have array indexes
        parsed_variable_name = match.group(1)
        index_list = []
        # LOOP THROUGH all GROUPS
        indexes = match.group(2)
        # Now parse all indexes could be nested arrays like [2][1]
        # We are parsing out the digits
        index_list = re.findall(r'\[(\d+)\]', indexes)
        # Coerce all indexes to integers
        index_list = [int(x) for x in index_list]
    else:
        # No list first token is the variable_name but no index
        parsed_variable_name = token_list[0]
    if len(token_list) == 1:
        # In this scenario there is only a single variable_name so we just set it in the dict
        if match is not None:
            update_list_in_dict(
                dict_to_set, parsed_variable_name, index_list, variable_value)
        else:
            # single variable_name not a list
            dict_to_set[token_list[0]] = variable_value
    else:
        # length is greater than one  process and recurse
        # two cases:
        #     - variable_name.variable_name.*
        #     - variable_name[0].variable_name.*

        # create a dict to insert at the list element
        new_dict = None
        existing_dict = None
        # Look to see if dict pre-exists
        if parsed_variable_name in dict_to_set:
            # The purpose os this block is to see if the dictionary already
            # exists and if so build upon that
            variable_data = dict_to_set[parsed_variable_name]
            if match is not None:
                # if we have nested array indexes traverse to get the final value
                existing_dict = get_value_at_index(variable_data, index_list)
            else:
                existing_dict = variable_data

            if existing_dict:
                # This is the case where it was allocated earlier
                new_dict = existing_dict
            else:
                # Alternate case where we need to create the nested dict
                new_dict = {}
        else:
            # Must not pre-exist create a new one
            new_dict = {}

        # Now we set the dictionary back into the structure this handles the case where it is new
        # worst case this will be redundant
        if match is not None:
            # list case
            # variable_name[x] case
            update_list_in_dict(
                dict_to_set, parsed_variable_name, index_list, new_dict)
        else:
            # non list case just create a dict under the variable_name name and recurse
            # create variable_name in top level and nested dict
            dict_to_set[parsed_variable_name] = new_dict

        # recurse to next level under new dict we just inserted
        # For the variable name we remove the first token and pass the remainder to allow it to
        # recurse to the next level
        set_variable_in_dict(new_dict, variable_name.split(
            '.', maxsplit=1)[1], variable_value)


def bool_helper(bool_string):
    """
    Needed a helper that could take a string version of a bool and convert it to
    the actual bool value
    """
    if bool_string.lower() == 'true':
        return True
    else:
        return False


def parse_csv_to_dict(csv_file):
    """This method will take a CSV file containing:
    - First row has field names
    Note:  If the field type is other than string please encode it as "fieldname(int)" where the data type
    is in parenthesis.  Technically string is default and doesn't need to be specified but if you'd like to put (str)
    - Other rows will have to be in the same order of field names containing the related values

    Parameters:
    csv_file -- The path to the file

    It will set those values into a dictionary and return that dictionary.  The field names in the first
    row can have hierarchical complexity with lists and nested objects (variable.nestedvariable...)

    This will return a list of dictionary objects with the python dictionary equivalent of the CSV file
    """
    first_row = True
    field_names = None
    object_list = []
    with open(csv_file, encoding='utf-8-sig') as csvfile:
        # Note windows encodes a funny character at the beginning of the first line
        # The encoding option above gets rid of that funny encoding character
        csvreader = csv.reader(csvfile)
        type_conversion_dict = {}
        for row in csvreader:
            # Row is a line in a CSV file a list of field values
            # First row items are the column names
            if first_row:
                field_names = [x.strip() for x in row]  # nuke whitespace
                count = 0
                for field in field_names:
                    # Looking for embedded data type in the field names for proper type conversion
                    match = re.search(r'(.*)\((.*)\)', field)
                    if match:
                        variable = match.group(1)
                        typeconvert = match.group(2)
                        if typeconvert == 'int':
                            type_conversion_dict[variable] = int
                        elif typeconvert == 'str':
                            type_conversion_dict[variable] = str
                        elif typeconvert == 'bool':
                            type_conversion_dict[variable] = bool_helper
                        else:
                            raise NotImplementedError(
                                'Type: '+typeconvert+' is not supported.')
                        field_names[count] = variable  # sanitize out the type
                    count += 1
                first_row = False
            else:
                object_dict = {}  # Container to hold the fields
                index = 0
                for field_name in field_names:
                    try:
                        val = row[index].strip()
                        if field_name in type_conversion_dict:
                            val = type_conversion_dict[field_name](val)
                    except IndexError:
                        # sub case where the row is a short row missing some of the values
                        # could be a short row stop processing this row
                        break
                    if val is not None and val == NONE_CSV_VALUE:
                        val = None
                    if val is not None:
                        # Only set non-null values
                        set_variable_in_dict(object_dict, field_name, val)
                    index += 1
                # append this instance to a list
                object_list.append(object_dict)
    return object_list


def parse_csv_to_json(csv_file):
    """
    See parse_csv_to_dict this will do the same thing as that however it will convert the dictionary
    returned into a formatted JSON document instead of Python dictionary format.

    Parameters:

    csv_file -- A file containing CSV content (first row are the field names)
    """
    object_list = parse_csv_to_dict(csv_file)
    return json.dumps(object_list, indent=3, sort_keys=True)


def parse_csv_to_jsonfile(csv_file, json_file):
    """
    Same as the above however this will write out the json content to a target file

    Parameters:
    csv_file -- Input CSV file
    json_file -- Output JSON file
    """
    if os.path.isfile(csv_file):
        json_doc = parse_csv_to_json(csv_file)

        with open(json_file, 'w') as jsonoutfile:
            jsonoutfile.write(json_doc)
    else:
        raise Exception('Input file not found')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Convert JSON files to CSV')
    parser.add_argument('--csvin', help='CSV file that will be read in')
    parser.add_argument('--jsonout', help='JSON output file')
    args = parser.parse_args()
    if args.csvin is not None and args.jsonout is not None:
        csv_file = args.csvin
        json_file = args.jsonout
        if not os.path.isfile(csv_file):
            logging.critical('CSV file does not exist')
            exit(-1)
        parse_csv_to_jsonfile(csv_file, json_file)
    else:
        parser.error('Missing required arguments')
        parser.print_usage()

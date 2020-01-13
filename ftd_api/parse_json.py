'''
Copyright (c) 2020 Cisco and/or its affiliates.

A copy of the License (MIT License) can be found in the LICENSE.TXT
file of this software.

Author: Jared T. Smith <jarmith@cisco.com>
Created: Dec 19, 2019
updated

'''

import csv
import json
import ftd_api.parse_csv as parse_csv
from ftd_api.file_helper import read_string_from_file
from ftd_api.file_helper import print_string_to_file
import os

NONE_CSV_VALUE = '-=NONE/NULL=-'

def pretty_print_json_file(json_file):
    """
    This method will take a JSON file and will convert it to pretty logging.info format

    Parameters:

    json_file -- The JSON file to pretty logging.info

    """
    json_data = json.loads(read_string_from_file(json_file))
    print_string_to_file(json_file, json.dumps(json_data, indent=3, sort_keys=True))
    
def pretty_print_json_string(json_string):
    """
    This method takes as input a json string and converts it to a pretty printed json string
    
    Return:
    
    Pretty formatted JSON string
    """
    parsed_json = json.loads(json_string)
    return json.dumps(parsed_json, indent=3, sort_keys=True)

def get_keys_from_dict(my_dict, path_set, current_path=None, path_to_value_dict=None):
    """
    The intention of this method is to take a dict parse from JSON where
    the only structures in the dict are:

    Parameters:
    - primitive values
    - lists
    - dicts

    It takes the following parameters:
    my_dict -- This is the top level dictionary
    path_set -- This is a set that it will append the complete paths it discovers
    current_path -- This should be internally set it is used for recursion where
                    there is a need to track the path to the leaf node from a root
                    element in the dict.
    path_to_value_dict -- If provided this will collect final paths and put them in a
                          map to the value under that path.  Basically it will flatten
                          the original dict into a one level dict with hierarchical keys

    The real goal of this method is to produce a flattened key:value map where the key
    is the full path to a value and the value is the end value.  This is used for
    conversion between dictionary and CSV formats.
    """
    if current_path is None:
        # Start with empty string
        current_path = ''

    for key in my_dict.keys():
        if type(my_dict[key]) == list:
            recursion_path = current_path + key
            _get_keys_from_list(my_dict[key], path_set, current_path=recursion_path, path_to_value_dict=path_to_value_dict)
            # recurse list
        elif type(my_dict[key]) == dict:
            recursion_path = current_path + key + '.'
            get_keys_from_dict(my_dict[key], path_set, current_path=recursion_path, path_to_value_dict=path_to_value_dict)
        else:
            # assume primitive value (dead end)
            path_set.update(set([current_path+key]))
            if path_to_value_dict is not None:
                path_to_value_dict[current_path+key] = my_dict[key]

def _get_keys_from_list(my_list, path_set, current_path=None, path_to_value_dict=None):
    """
    This is a helper method for get_keys_from_dict that will walk down a list potentially recursing
    to discover the paths to each end value.  It will build upon what was passed into it.

    Parameters:

    my_list -- This is the list to walk down
    path_set -- This is the list of complete leaf node paths to walk
    current_path -- This is the path to the base of the list so far (leave empty if starting here)
    path_to_value_dict -- This is a dictionary (optional) of full path : end value
    """
    count = 0
    if current_path == None:
        current_path = ''
    for item in my_list:
        if type(item) == list:
            recursion_path = current_path + '['+str(count)+']'
            #recurse this will append array index as above
            _get_keys_from_list(item, path_set, current_path=recursion_path, path_to_value_dict=path_to_value_dict)
        elif type(item) == dict:
            #append separator and recurse
            recursion_path = current_path + '['+str(count)+'].'
            get_keys_from_dict(item, path_set, current_path=recursion_path, path_to_value_dict=path_to_value_dict)
        else:
            #assume primitive value (deadend) append to set
            path_set.update(set([current_path+'['+str(count)+']']))
            if path_to_value_dict is not None:
                path_to_value_dict[current_path+'['+str(count)+']'] = item
        count += 1


def _create_fieldname_to_type_map(flat_dict_list):
    """
    This method will create a map of file names to the respective data types
    this is used so we can put type hints in the resultant CSV

    For now this will only populate integer fields

    Parameters:

    flat_dict_list(in) -- This is a list of dictionaries that are already flattened into
                      full path:value
    """
    fieldname_to_type = {}
    for flat_dict in flat_dict_list:
        for key, value in flat_dict.items():
        # we will only keep a type if all instances are identical
        # otherwise leave it to the default string
            if key in fieldname_to_type:
                existing_field_type = fieldname_to_type[key]
                if existing_field_type != 'BAD' and existing_field_type != type(value): # MARK the mapping BAD
                    # previously found type doesn't match newly found type mark bad so
                    # we don't cast it into a value that won't work (leave as a string)
                    fieldname_to_type[key] == 'BAD' # otherwise it matches
            elif type(value) == int: #doing it like this in case we add more types later
            # add a new mapping
                fieldname_to_type[key] = 'int'
            elif type(value) == bool:
                fieldname_to_type[key] = 'bool'

    return fieldname_to_type


def _fixup_key_list_with_types(key_list, fieldname_to_type):
    """
    This method will annotate the field names in the key_list with the type for example:
    fieldname(int)

    This is used to make them easier to decode by giving a type hint especially for integer
    types.

    Parameters:

    key_list(in/out) -- This is the list of non-typed keys (array updated inline)
    fieldname_to_type(in) -- This is the map of full field name with path to type where the type string will be encoded
                             in the key name.
    """
    if len(fieldname_to_type) > 0: #fix up key_list with type encoding
        count = 0
        for key in key_list:
            if key in fieldname_to_type and fieldname_to_type[key] != 'BAD':
                newname = key + '(' + fieldname_to_type[key] + ')'
                key_list[count] = newname
            count += 1

def decorate_dict_list_for_bulk(dict_list):
    count = 0
    wrapper_dict = {
        'type': 'identitywrapper',
        'action': 'EDIT',
        'data': None
    }
    for object_dict in dict_list:
        dict_copy = wrapper_dict.copy()
        dict_copy['data'] = object_dict
        dict_list[count] = dict_copy
        count += 1

def fixup_none_value(value):
    if value is None:
        return NONE_CSV_VALUE
    else:
        return value


def flatten_dict_list(dict_list, path_set=None):
    """
    This method will take a list of dictionaries and will return a list of flattened dictionaries
    where there will only be a single key/value with no hierarchy.

    Parameters:
    dict_list -- input list of dictionaries (with hierarchy)
    path_set -- Optional arg which will collect unique paths (out)

    Return will be the converted flattened list
    """
    flat_dict_list = []
    if path_set is None:
        # this is for use cases when people don't care about the path set and just want the
        # flat dict
        path_set = set()
    for object_dict in dict_list: # These are the top level dictionaries that need to be processed we will do one pass to
        # discover the keys on the first row to go into the CSV
        # Note:  We must process all dicts to get the full set of keys
        # This key_value_flat_dict will store the list of key value dicts that will be the rows in the csv after the header row
        key_value_flat_dict = {}
        get_keys_from_dict(object_dict, path_set, path_to_value_dict=key_value_flat_dict)
        flat_dict_list.append(key_value_flat_dict)
    return flat_dict_list

def dict_list_to_csv(dict_list, csv_file_out):
    """
    This method will take a list of python dictionaries and will convert them to a encoded CSV file.
    This will typically make the most sense when a single file has a list of one type of object so the
    CSV columns make more sense.

    Parameters:

    dict_list(in) - This is the list of dictionary objects to process
    csv_file_out - This is the name of the file to write the results to
    """
    if type(dict_list) == list: #path_set is the set of all full paths to values
        path_set = set()
        #flat dicts have the attribute names flattened as a single key the hierarchy is encoded in the name with "." and [] for arrays
        flat_dict_list = flatten_dict_list(dict_list, path_set)

        #Sort keys so CSV will have keys in sorted order to make it more readable
        key_list = list(path_set)
        key_list.sort()
        # Now we have established an ordered list for the keys we need to create a lookup dict that tells the index in the CSV
        key_index_dict = {}
        count = 0
        for key in key_list:
            key_index_dict[key] = count
            count += 1

        # Try to determine data type for each field so we can encode that in the field name in the CSV
        # we will loop through the flat dict to determine this
        fieldname_to_type = _create_fieldname_to_type_map(flat_dict_list)
        _fixup_key_list_with_types(key_list, fieldname_to_type)
        with open(csv_file_out, 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(key_list)
            for object_flat_dict in flat_dict_list:
                row = []
                # we need to loop through the key value pairs in the dict
                for key_value_pairs in object_flat_dict.items():
                    parse_csv.set_value_at_list_index(row, [key_index_dict[key_value_pairs[0]]], fixup_none_value(key_value_pairs[1]))
                count = 0
                # Make sure rows items that aren't included in the dict get marked as None
                for item in row:
                    if item is None:
                        row[count] = fixup_none_value(item)
                    count += 1
                csvwriter.writerow(row)
    else:
            raise ValueError('Error: expected a list')

def parse_json_to_csv(json_file_in, csv_file_out):
    """
    This method will take in a JSON file parse it and will generate a CSV file with the
    same content.

    Parameters:
    json_file_in -- Input file containing list of JSON objects
    csv_file_out -- Output file for CSV content
    """
    with open(json_file_in, encoding='utf-8-sig') as jsonfile:
        dict_list = json.load(jsonfile)
        dict_list_to_csv(dict_list, csv_file_out)

def save_dictlist_as_file(dict_list, output_file):
    """
    This method will take a dict list and will write it out
    in json format into the output_file

    Parameters:

    dict_list -- This is the input dict_list
    output_file -- This is the name of the file (fully qualified)
    to write the data to.
    """
    with open(output_file, "w") as output_handle:
        output_handle.write(json.dumps(dict_list))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Convert JSON files to CSV')
    parser.add_argument('--csvout', help='CSV file that will be written out')
    parser.add_argument('--jsonin', help='JSON input file')
    args = parser.parse_args()
    if args.csvout is not None and args.jsonin is not None:
        json_file = args.jsonin
        if not os.path.isfile(json_file):
            print('ERROR: JSON file does not exist')
            exit(-1)
        csv_file = args.csvout
        parse_json_to_csv(json_file, csv_file)
    else:
        print('Missing required arguments')
        parser.print_usage()


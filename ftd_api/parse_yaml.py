'''
Copyright (c) 2020 Cisco and/or its affiliates.

A copy of the License (MIT License) can be found in the LICENSE.TXT
file of this software.

Author: Jared T. Smith <jarmith@cisco.com>
Created: Jan 10, 2020
updated

'''
import yaml

def write_dict_to_yaml_file(yaml_file, obj_dict):
    """
    This method writes out a python structure in YAML format to a file
    Parameters:
    yaml_file -- File to write the data to
    obj_dict -- the structure to write
    """
    with open(yaml_file, 'w') as file_handle:
        yaml.dump(obj_dict, file_handle)

def read_yaml_to_dict(yaml_file):
    """
    This method loads data from a yaml file and returns the data structure
    Parameters:
    yaml_file -- This is the file to load
    """
    with open(yaml_file, 'r') as file_handle:
        return yaml.load(file_handle, Loader=yaml.FullLoader)

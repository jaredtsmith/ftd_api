#!/usr/bin/env python3
'''
docker_util

This is a wrapper to call the docker image for the import/export utility it will 
handle mapping the local file system.

Copyright (c) 2020 Cisco and/or its affiliates.

A copy of the License (MIT License) can be found in the LICENSE.TXT
file of this software.

Author: Jared T. Smith <jarmith@cisco.com>
Created: March 27, 2020

'''
def create_mount_point(original_file_path, target_path):
    """
    This method will take a source path and a target path and will formulate a 
    file system mount to be passed to docker.

    original_file_path - This is the source path that is on your local filesystem
    target_path - This is the target path that is within the docker VM

    Returns:
    The return value is a tuple consisting of the following:
    (array containing the mount command, target path within the VM)
    """
    original_path = args[file_path_index]
    expanded_file_path = os.path.abspath(original_file_path)

    # Build up the file mount mapping so we can map the file system
    # through the docker container to read or deposit the file.  We will 
    # map both cases to /tmp/a so we have a known location in the docker
    file_mount_mapping_array = None
    if os.path.isdir(expanded_file_path):
        # This should be for the export case where the passed argument is a 
        # directory
        return (['-v', expanded_file_path+':'+target_path], target_path)
    elif os.path.isfile(expanded_file_path):
        # This is for the case where a file is passed which is typically an
        # import scenario
        return (['-v', os.path.dirname(expanded_file_path)+':'+target_path], 
                target_path +'/'+ os.path.split(expanded_file_path)[-1])
    else:
        # Error case invalid path
        return (None, None)

        print('ERROR -l %s file path does not exist', original_path)
        exit -1

if __name__ == '__main__':
    DOCKER_NAME = 'ciscongfw/ftdimportexportcmd'
    import sys
    import os.path
    import subprocess
    container = []
    args = sys.argv
    # truncate first arg it is the script name
    args = args[1:]

    # look for the location arg and fix it up to map the directory through
    count = 0
    file_path_index = -1
    for item in args:
        # look for location flag if found save the index
        if item.strip() == '-l':
            file_path_index = count + 1
            break
        count += 1

    if file_path_index == -1:
        print('ERROR -l file is missing')
        exit(-1)

    original_path = args[file_path_index]
    file_path = os.path.abspath(original_path)

    target_cmd_array_location, target_path = create_mount_point(file_path, '/tmp/a')
    if target_cmd_array_location is None:
        print('ERROR -l %s file path does not exist', original_path)
        exit(-1)
    else:
        args[file_path_index] = target_path

    # look for the configuration file to be passed and map the directory across
    count = 0
    file_path_index = -1
    for item in args:
        # look for location flag if found save the index
        if item.strip() == '-c':
            file_path_index = count + 1
            break
        count += 1

    if file_path_index == -1:
        print('ERROR -c file is missing')
        exit(-1)

    original_path = args[file_path_index]
    file_path = os.path.abspath(original_path)

    target_cmd_array_properties, target_path = create_mount_point(file_path, '/tmp/b')
    if target_cmd_array_properties is None:
        print('ERROR -c %s file path does not exist', original_path)
        exit(-1)
    else:
        args[file_path_index] = target_path

    full_cmd = ['docker', 'run']+target_cmd_array_location+ target_cmd_array_properties+[DOCKER_NAME] + args
    print('Executing command: '+' '.join(full_cmd))
    subprocess.run(full_cmd)

#!/usr/bin/env python3
'''
ftd_bulk_tool

This tool provides a simple abstraction to handle bulk import/export tasks via the Firepower Threat Defese REST API.

Copyright (c) 2020 Cisco and/or its affiliates.

A copy of the License (MIT License) can be found in the LICENSE.TXT
file of this software.

Author: Jared T. Smith <jarmith@cisco.com>
Created: Jan 3, 2020

'''

import sys
import os.path
import ftd_api.parse_properties as parse_properties
from ftd_api.bulk_tool import BulkTool
from ftd_api.string_helper import split_string_list

# Configure Logging
import logging
from ftd_api.logging import configure_logging, enable_debug, disable_debug
from ftd_api.ftd_client import FTDClient



def main():

    configure_logging()
    args = get_args()
    
    try:
        # Establish the FTD connection
        logging.info(f'Establishing connection to FTD: https://{args.address}:{args.port}')
        try:
            
            client = FTDClient(address=args.address,
                               port=args.port,
                               username=args.username,
                               password=args.password)
            # login to create a session
            client.login()
            bulk_client = BulkTool(client)
        except Exception as err:
            logging.critical(f'Unable to connect to FTD')
            raise

        # Handle Export
        if args.mode == 'EXPORT':
            bulk_export(args, bulk_client)

        # Handle Import
        elif args.mode == 'IMPORT':
            bulk_import(args, bulk_client)

        # Handle Type Listing
        elif args.mode == 'LIST_TYPES':
            type_list = "\n"
            for type in bulk_client.get_object_types():
                type_list = type_list + f'  {type}\n'
            logging.info(f'Possible types are: {type_list}')
        else:
            logging.error(f'Unknown mode provided: {args.mode}')

    except Exception as ex:
        # Looks like this dumps stack even if not in debug mode commenting out for now
        #logging.exception('Fatal error occurred')
        if args.debug:
            raise
        else:
            if hasattr(ex, 'message'):
                message = ex.message
            else:
                message = str(ex)
            fatal(message, 1)
    logging.info('Done')

def get_args ():
    import argparse

    # Let's start with the config file if it is specified.
    config_file_parser = argparse.ArgumentParser(
        # don't capture the help flag with this parser
        add_help = False
    )
    config_file_parser.add_argument(
        '-c', '--config_file',
        metavar='FILE_NAME',
        help="A properties file allowing you to specify any of the tool's options. If the option is set in both places, the command-line options will override the configuration file. The format is key=value each on it's own line. '#' comments are supported."
    )
    args, remaining_argv = config_file_parser.parse_known_args()

    # Lets define defaults here so we can override them with the values from the config file if there are
    defaults = {
        'address':'localhost',
        'port':'443',
        'username':'Admin',
        'password':'Admin123',

    }
    if args.config_file is not None:
        config_dict = parse_properties.file_to_dict(args.config_file)
        config_dict['config_file'] = args.config_file
        defaults.update(config_dict)
    parser = argparse.ArgumentParser(
        # Use the header docstring as the description
        description = 'This tool provides a simple abstraction to handle bulk import/export tasks via the Firepower Threat Defese REST API.',
        # Make sure config_file shows up in the help
        parents=[config_file_parser])

    parser.set_defaults(**defaults)
    # Required Command
    parser.add_argument(
        'mode',
        choices=['IMPORT', 'EXPORT', 'LIST_TYPES'],
        help='The various different modes in which the tool runs'
    )

    # Globally applicable Options
    parser.add_argument(
        '-D', '--debug',
        help='Enable debug logging',
        action='store_true'
    )
    parser.add_argument(
        '-a','--address',
        help="FTD hostname or IP. Default: 'localhost'"
    )
    parser.add_argument(
        '-P','--port',
        help='FTD port. Default: 443'
    )
    parser.add_argument(
        '-u','--username',
        help="The username to login with. Default: 'Admin'"
    )
    parser.add_argument(
        '-p','--password',
        help="The password to login with. Default: 'Admin123'"
    )

    # Import and Export Options
    parser.add_argument(
        '-l','--location',
        help='Directory path for EXPORT mode. One or more file paths (comma delimited) for IMPORT mode. Required by IMPORT, and EXPORT modes',
        required=(
            ('IMPORT' in sys.argv) or
            ('EXPORT' in sys.argv)
        )
    )
    parser.add_argument(
        '-f','--format', choices=['CSV', 'JSON', 'YAML'],
        help="Specify the import or output format. Default: 'JSON'",
        default='JSON'
    )

    # Export  Options
    parser.add_argument(
        '--url',
        help='The URL you would like to export data from instead of doing a full export. Only valid for EXPORT mode.'
    )
    parser.add_argument(
        '-e','--pending',
        help="Export only pending changes. Only valid for EXPORT mode. Ignored if 'url' is supplied",
        action='store_true'
    )
    parser.add_argument(
        '-i','--id_list',
        help="Comma separated list of ID values to export. This is essentially a filter by ID on the export. Only valid for EXPORT mode. Ignored if 'url' or 'pending' are supplied"
    )
    parser.add_argument(
        '-n','--name_list',
        help="Comma separated list of names to export.  This is essentially a filter by name on the export. Only valid for EXPORT mode. Ignored if 'url' or 'pending' are supplied"
    )
    parser.add_argument(
        '-t','--type_list',
        help="Comma separated list of types to export. This is essentially a filter by type on the export. Only valid for EXPORT mode. Ignored if 'url' or 'pending' are supplied"
    )
    parser.add_argument(
        '--filter_local',
        help="This instructs the import code to filter by the -t -n -i options before sending the data to the server, this can be used as a work around if server side filtering does not work",
        action='store_true'
    )
    args = parser.parse_args(remaining_argv)

    # Let's do all the up front validation we can based solely on the input
    if args.debug:
        enable_debug()
    else:
        disable_debug()
    if args.mode == 'EXPORT':
        if not os.path.isdir(args.location):
            parser.error(f'Unable to locate provided export directory: {args.location}')

        if args.pending and args.url is not None:
            logging.warn("URL Export does not support exporting only pending changes. The 'pending' option will be ignored.")
        if args.pending and (args.type_list is not None or args.id_list is not None or args.name_list is not None):
            parser.error(f'Filter criteria (id_list, name_list, type_list) are not supported with the pending option please remove the filter criteria')

    elif args.mode == 'IMPORT' and (args.pending or args.url is not None):
        # We do allow type, name, id filters for import they act as exclude filters on the import set
        parser.error('The following options are not valid with the IMPORT command: --url, -e')

        #Location for import is either a single file, or list of files (comma delimited)
        for file in split_string_list(args.location):
            if not os.path.isfile(file):
                parser.error(f'Specified input file(s) could not be located:{args.location}')

    logging.debug('CONFIGURATION:')
    for arg in vars(args):
        logging.debug(f'  {arg}: {getattr(args, arg)}')

    return (args)

def fatal(message, error_code=42):
    if message is None:
        message = ''
    logging.critical(f'FATAL: {message}')
    exit(error_code)

def bulk_export(args, client) :
    if args.url is not None:
        return client.url_export(args.url, args.location, output_format=args.format)
            
    # Pre-define lists as none so they are passed down with the proper default
    id_list = None
    type_list = None
    name_list = None
    
    # PENDING_CHANGE_EXPORT called for
    pending_changes = False
    if args.pending:
        pending_changes = True

    # If filter lists are present convert them to Python lists    
    if args.type_list is not None:
        type_list = split_string_list(args.type_list)
    if args.id_list is not None:
        id_list = split_string_list(args.id_list)
    if args.name_list is not None:
        name_list = split_string_list(args.name_list)

    client.bulk_export(args.location, pending_changes, type_list=type_list, id_list=id_list, name_list=name_list, output_format=args.format)            

def bulk_import(args, client):
    file_list = split_string_list(args.location)

    if args.format not in ('CSV', 'JSON', 'YAML'):
        logging.error('Format must be specified as CSV, JSON or YAML')
        fatal(None, 11)
        
    # Pre-define lists as none so they are passed down with the proper default
    id_list = None
    type_list = None
    name_list = None

    # If filter exclude lists are present convert them to Python lists    
    if args.type_list is not None:
        type_list = split_string_list(args.type_list)
    if args.id_list is not None:
        id_list = split_string_list(args.id_list)
    if args.name_list is not None:
        name_list = split_string_list(args.name_list)

    client.bulk_import(file_list, 
                       input_format=args.format,
                       type_list=type_list,
                       id_list=id_list,
                       name_list=name_list,
                       filter_local=args.filter_local)

if __name__ == '__main__':
    main()

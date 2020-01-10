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

# TODO: We should normalize on an error handling strategy. Are we propagating
# exceptions? Exiting? Logging and return code failure?

import json
import sys
import os.path
import ftd_api.parse_json as parse_json
import ftd_api.parse_csv as parse_csv
import ftd_api.parse_properties as parse_properties
from ftd_api.bulk_tool import BulkTool
from ftd_api.string_helper import split_string_list
from ftd_api.parse_json import pretty_print_json_file
from ftd_api.file_helper import read_string_from_file
from ftd_api.file_helper import print_string_to_file
from ftd_api.parse_yaml import write_dict_to_yaml_file
from ftd_api.parse_yaml import read_yaml_to_dict

# Configure Logging
import logging
from ftd_api.logging import configure_logging, enable_debug, disable_debug


def main():

    configure_logging()
    args = get_args()

    try:
        # Establish the FTD connection
        logging.info(f'Establishing connection to FTD: https://{args.address}:{args.port}')
        try:
            client = BulkTool(
                address=args.address,
                port=args.port,
                username=args.username,
                password=args.password
            )
        except Exception as err:
            logging.critical(f'Unable to connect to FTD')
            raise

        # Handle Export
        if args.mode == 'EXPORT':
            bulk_export(args,client)

        # Handle Import
        elif args.mode == 'IMPORT':
            bulk_import(args, client)

        # Handle Type Listing
        elif args.mode == 'LIST_TYPES':
            type_list = "\n"
            for type in client.get_object_types():
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

    args = parser.parse_args(remaining_argv)

    # Let's do all the up front validation we can based solely on the input
    if args.debug:
        enable_debug()
    else:
        disable_debug()

    if args.mode == 'EXPORT':
        if not os.path.isdir(args.location):
            parser.error('Unable to locate provided export directoy: {args.location}')

        if args.pending and args.url is not None:
            logging.warn("URL Export does not support exporting only pending changes. The 'pending' option will be ignored.")

        if args.pending and (args.type_list is not None or args.id_list is not None or args.name_list is not None):
            logging.warn('Pending change export does not support filtering by id_list, name_list, nor type_list. Filters will be ignored.')


    elif args.mode == 'IMPORT':
        if args.pending or args.id_list is not None or args.name_list is not None or args.type_list is not None or args.url is not None:
            parser.error('The following options are not valid with the IMPORT command: --url, --name_list, --type_list, --id_list')

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

# TODO: Should bulk_export and bulk_import be the public interface of BulkTool?

def bulk_export(args, client) :
    # Base Case
    args.mode = 'FULL_EXPORT'

    # If we have a URL it is a URL export
    if args.url is not None:
        args.mode = 'URL_EXPORT'
        url_export(args, client)

    # if it is not a URL export lets continue
    else:
        location_export_zip = os.path.normpath(args.location + '/myexport.zip')
        type_list = None

        # PENDING_CHANGE_EXPORT called for
        if args.pending:
            args.mode = 'PENDING_CHANGE_EXPORT'

        # If it is a pending change export we do not support filtering
        # If there are filter lists defined it is a PARTIAL EXPORT
        else:
            # If we have a filter list it is a PARTIAL_EXPORT for the UI
            if args.type_list is not None:
                type_list = split_string_list(args.type_list)
                args.mode = 'PARTIAL_EXPORT'
            id_list = None
            if args.id_list is not None:
                id_list = split_string_list(args.id_list)
                args.mode = 'PARTIAL_EXPORT'
            name_list = None
            if args.name_list is not None:
                name_list = split_string_list(args.name_list)
                args.mode = 'PARTIAL_EXPORT'

        # Download export file
        client.do_download_export_file(
            export_file_name=location_export_zip,
            id_list=id_list,
            type_list=type_list,
            name_list=name_list,
            export_type=args.mode
        )
        if args.format == 'CSV':
            logging.info('Exporting in CSV format')
            client.convert_export_file_to_csv(
                location_export_zip, args.location)
            logging.info('CSV files can be found in: '+str(args.location))
        elif args.format == 'JSON':
            logging.info('Exporting in JSON format')
            json_file = client.extract_config_file_from_export(
                location_export_zip, args.location)
            pretty_print_json_file(json_file)
            logging.info('JSON files can be found in: '+str(json_file))
        elif args.format == 'YAML':
            logging.info('Exporting in YAML format')
            json_file = client.extract_config_file_from_export(
                location_export_zip, args.location)
            object_list = json.loads(read_string_from_file(json_file))
            yaml_file = args.location+'/export.yaml'
            write_dict_to_yaml_file(yaml_file, object_list)
            logging.info('YAML file can be found in: '+str(yaml_file))

def url_export(args, client):
    object_list = client.do_get_with_paging(args.url)

    if args.format == 'JSON':
        logging.info('Exporting in JSON format')
        print_string_to_file(args.location, json.dumps(
            object_list, indent=3, sort_keys=True))
        logging.info('JSON files can be found in: '+str(args.location))

    elif args.format == 'CSV':
        logging.info('Exporting in CSV format')
        parse_json.dict_list_to_csv(object_list, args.location)
        logging.info('CSV files can be found in: '+str(args.location))

    elif args.format == 'YAML':
        logging.info('Exporting in YAML format')
        yaml_file = args.location+'/export.yaml'
        write_dict_to_yaml_file(yaml_file, object_list)
        logging.info('YAML files can be found in: '+str(yaml_file))

def bulk_import(args,client):
    location_list = split_string_list(args.location)

    if args.format not in ('CSV', 'JSON', 'YAML'):
        logging.error('Format must be specified as CSV, JSON or YAML')
        fatal(None, 11)

    if args.format == 'CSV':
        logging.info('Importing in CSV mode')
        object_list = []
        # need to loop  through files and convert to JSON and merge into a single list
        for location in location_list:
            object_list.extend(parse_csv.parse_csv_to_dict(location))
        if client.do_upload_import_dict_list(object_list):
            logging.info('Successfully completed import')
        else:
            logging.error('Unable to complete import')
    elif args.format == 'JSON':
        logging.info('Importing in JSON mode')
        #JSON case just merge the JSON docs
        object_list = []
        for location in location_list:
            object_list.extend(
                json.loads(read_string_from_file(location))
            )

        if client.do_upload_import_dict_list(object_list):
            logging.info('Successfully completed import')
        else:
            logging.error('Unable to complete import')
    elif args.format == 'YAML':
        logging.info('Importing in YAML mode')
        #JSON case just merge the JSON docs
        object_list = []
        for location in location_list:
            object_list.extend(read_yaml_to_dict(location))

        if client.do_upload_import_dict_list(object_list):
            logging.info('Successfully completed import')
        else:
            logging.error('Unable to complete import')

if __name__ == '__main__':
    main()

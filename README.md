# ftd_api

This repository is dedicated to useful tooling for the Firepower Threat Defense on-box REST API

Please note that this API is only accessible when the device is not managed by an FMC.

## Installation

### From Pypi

`pip install ftd_api`

## Usage

Right now we are only "exposing" the bulk tool. Keep a lookout in this space for more good stuff coming.

### Bulk Tool

If you have installed the package the bulk tool `ftd_bulk_tool` should be in your path already.

    usage: ftd_bulk_tool [-h] [-c FILE_NAME] [-D] [-a ADDRESS] [-P PORT]
                        [-u USERNAME] [-p PASSWORD] [-l LOCATION]
                        [-f {CSV,JSON,YAML}] [--url URL] [-e] [-i ID_LIST]
                        [-n NAME_LIST] [-t TYPE_LIST]
                        {IMPORT,EXPORT,LIST_TYPES}

    This tool provides a simple abstraction to handle bulk import/export tasks via
    the Firepower Threat Defese REST API.

    positional arguments:
    {IMPORT,EXPORT,LIST_TYPES}
                            The various different modes in which the tool runs

    optional arguments:
    -h, --help            show this help message and exit
    -c FILE_NAME, --config_file FILE_NAME
                            A properties file allowing you to specify any of the
                            tool's options. If the option is set in both places,
                            the command-line options will override the
                            configuration file. The format is key=value each on
                            it's own line. '#' comments are supported.
    -D, --debug             Enable debug logging
    -a ADDRESS, --address ADDRESS
                            FTD hostname or IP. Default: 'localhost'
    -P PORT, --port PORT  FTD port. Default: 443
    -u USERNAME, --username USERNAME
                            The username to login with. Default: 'Admin'
    -p PASSWORD, --password PASSWORD
                            The password to login with. Default: 'Admin123'
    -l LOCATION, --location LOCATION
                            Directory path for EXPORT mode. One or more file paths
                            (comma delimited) for IMPORT mode. Required by IMPORT,
                            and EXPORT modes
    -f {CSV,JSON,YAML}, --format {CSV,JSON,YAML}
                            Specify the import or output format. Default: 'JSON'
    --url URL               The URL you would like to export data from instead of
                            doing a full export. Only valid for EXPORT mode.
    -e, --pending           Export only pending changes. Only valid for EXPORT
                            mode. Ignored if 'url' is supplied
    -i ID_LIST, --id_list ID_LIST
                            A Comma-separated list of ID values to export or remove
                            from an import. This is essentially a filter by id
                            on the export or an exclusion filter on import. Valid
                            for IMPORT and EXPORT mode. Ignored if 'url' or 'pending'
                            are supplied.
    -n NAME_LIST, --name_list NAME_LIST
                            A Comma-separated list of names to export or remove
                            from an import. This is essentially a filter by name
                            on the export or an exclusion filter on import. Valid
                            for IMPORT and EXPORT modes. Ignored if 'url' or 'pending'
                            are supplied.
    -t TYPE_LIST, --type_list TYPE_LIST
                            A Comma-separated list of types to export or remove
                            from an import. This is essentially a filter by type
                            on the export or an exclusion filter on import. Valid
                            for IMPORT and EXPORT modes. Ignored if 'url' or 'pending'
                            are supplied.

## Contributing

### Development Environment

For those of you wishing to contribute: Fork this repo, clone your fork, then execute the following commands:

    cd ftd_api
    python3 setup.py sdist
    pip3 install -e .

This will build the source distribution and then install it onto your development system using symlinks (as opposed to installing a copy of it) so that as you modify the code it will take effect immediately. Note that this will work just the way you want it to in a [virtualenv](https://virtualenvwrapper.readthedocs.io/en/latest/)

### Running Tests

Please add unit tests using standard [unittest](https://docs.python.org/3.8/library/unittest.html) library and put them in the top level `tests` folder. To run the tests from the top level directory just run `pytest`. Alteratively, you can call unittest directly `python -m unittest tests/*.py`, but pytest is definitely prettier ;).

Note that pytest is not an explicit dependency of this package. Thus, you may want to install it: `pip install pytest`

## License

MIT License - See LICENSE.TXT for full text

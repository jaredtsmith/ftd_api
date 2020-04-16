# ftd_api

This repository is dedicated to useful tooling for the Firepower Threat Defense on-box REST API

Please note that this API is only accessible when an FMC does not manage the device.

## Installation

### From Pypi

`pip install ftd_api`

## Usage

Right now, we are only "exposing" the bulk tool. Keep a lookout in this space for more good stuff coming.

### Bulk Tool

If you have installed the package, the bulk tool `ftd_bulk_tool` should be in your path already.

```text
    usage: ftd_bulk_tool.py [-h] [-c FILE_NAME] [-D] [-a ADDRESS] [-P PORT]
                        [-u USERNAME] [-p PASSWORD] [-l LOCATION]
                        [-f {CSV,JSON,YAML}] [--url URL] [-e] [-i ID_LIST]
                        [-n NAME_LIST] [-t TYPE_LIST] [--filter_local]
                        {IMPORT,EXPORT,LIST_TYPES}

This tool provides a simple abstraction to handle bulk import/export tasks via
the Firepower Threat Defense REST API.

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
  -D, --debug           Enable debug logging
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
  --url URL             The URL you would like to export data from instead of
                        doing a full export. Only valid for EXPORT mode.
  -e, --pending         Export only pending changes. Only valid for EXPORT
                        mode. Ignored if 'url' is supplied
  -i ID_LIST, --id_list ID_LIST
                        Comma separated list of ID values to export. This is
                        essentially a filter by ID on the export. Only valid
                        for EXPORT mode. Ignored if 'url' or 'pending' are
                        supplied
  -n NAME_LIST, --name_list NAME_LIST
                        Comma separated list of names to export. This is
                        essentially a filter by name on the export. Only valid
                        for EXPORT mode. Ignored if 'url' or 'pending' are
                        supplied
  -t TYPE_LIST, --type_list TYPE_LIST
                        Comma separated list of types to export. This is
                        essentially a filter by type on the export. Only valid
                        for EXPORT mode. Ignored if 'url' or 'pending' are
                        supplied
  --filter_local        This instructs the import code to filter by the -t -n
                        -i options before sending the data to the server, this
                        can be used as a work around if server side filtering
                        does not work
```

#### Using a docker container

If using a bash shell, do the following:

Download the following file:

https://github.com/jaredtsmith/ftd_api/blob/master/docker/general/docker_util.sh

Add the following line to ~/.profile

```bash
source ~/docker_util.sh
```

Adjust the path for where you put the file on your system.  As long as you have the docker executable present, this creates a function 'ftd_bulk_tool' which runs the tool from a docker without installing the tool locally.

#### Install the tool in your local python path

```bash
pip install ftd_api
```

This installs the library in your machine and adds it to your python path.  If you would like to see the current version look here:
https://pypi.org/project/ftd-api/

#### How to pass connectivity information for your end device

We recommend creating a properties file with the connectivity info for your device typically I'll drop these in my home directory, and it would look something like this:

660.prop

```txt
address=myftd.com
port=443
username=admin
password=Admin123
```

Or to pass the same on the command line, you would add the following arguments:

```bash
-a myftd.com -P 443 -u admin -p Admin123
```

For frequent use, the properties file is faster!

#### Export Examples

Export the full configuration:

```bash
ftd_bulk_tool -c ~/660.prop -l /tmp/export EXPORT
```

The above command exports in JSON format by default see the -f argument to change the format.  The "-c" arg specifies the properties file with connectivity information, the "-l" specifies the directory to export to and the command is "EXPORT".

To export a specific type like "networkobject" you would run the command as follows:

```bash
ftd_bulk_tool -c ~/660.prop -l /tmp/export -t networkobject EXPORT
```

To add additional types, you can pass a comma-separated list just don't put spaces around the comma.

#### Import details

During import there are some object types you may want to exclude:

- internalcertificate - This object type can cause web server restart, so the tool runs more gracefully if this is excluded.
- webuicertificate - This object type triggers a web server restart, so exclude this from your import.
- user - The device thinks this is a password change and invalidates the session, so it is best to exclude the user object.
- managementip - This can impact connectivity to the device while running the script.

There are two ways the tool can exclude objects, one is client-side, and the other is server-side; we've found it more reliable to exclude upfront on the client-side, and you'll generally have fewer issues.  That is activated with the --filter_local option, and when filtering locally, you can filter out objects that cannot be filtered server-side like:

- metadata - This is a block at the top that of the import JSON file that causes cross-version import errors.  Just exclude this, and you'll be more likely to succeed.

Additionally, there can be version-specific compatibility issues, for example:

From 6.5.0 --> 6.6.0+

Exclude the following object type:

- datasslciphersetting - This had an enumeration change which will cause a parse error.

So to import a 6.5.0 configuration into a 6.6.0 box you would run the following command:

```bash
ftd_bulk_tool -c ~/660.prop -l /tmp/export/full_config.txt -t internalcertificate,user,metadata,managementip,webuic
ertificate,datasslciphersetting --filter_local IMPORT
```

Note:  Add -D for debug to see what the HTTP transactions look like under the covers.

In the case of import, the "-t" acts to exclude the list of types as opposed to export where it acts for inclusion.

## Contributing

### Development Environment

For those of you wishing to contribute: Fork this repo, clone your fork, then execute the following commands:

    cd ftd_api
    python3 setup.py sdist
    pip3 install -e .

This builds the source distribution and then installs it onto your development system using symlinks (as opposed to installing a copy of it) so that as you modify the code, it takes effect immediately. Note that this works just the way you want it to in a [virtualenv](https://virtualenvwrapper.readthedocs.io/en/latest/)

### Running Tests

Please add unit tests using standard [unittest](https://docs.python.org/3.8/library/unittest.html) library and put them in the top level `tests` folder. To run the tests from the top-level directory, just run `pytest`. Alteratively, you can call unittest directly `python -m unittest tests/*.py`, but pytest is definitely prettier ;).

Note that pytest is not an explicit dependency of this package. Thus, you may want to install it: `pip install pytest`

## License

MIT License - See LICENSE.TXT for full text

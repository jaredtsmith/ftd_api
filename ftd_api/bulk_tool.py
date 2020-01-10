'''
Copyright (c) 2020 Cisco and/or its affiliates.

A copy of the License (MIT License) can be found in the LICENSE.TXT
file of this software.

Author: Jared T. Smith <jarmith@cisco.com>
Created: Dec 10, 2020
updated

'''
from ftd_api.ftd_client import FTDClient
from ftd_api import parse_json
import requests
import time
import json
import random
import logging
import os.path
import zipfile


# TODO: We should probably just sub-class FTDClient instead of storing it as an
# attribute? Additionally we should move the generally useful functions to the
# core FTDClient class
# RESPONSE:  I'm thinking things need to get shuffled around more as we will have non-bulk use cases and it is 
# probably desirable longer term to share a client between bulk calls and other calls?  Not entirely sure what that looks like yet though.
class BulkTool:

    def __init__(self, address='192.168.1.1', port=443, username="admin", password="Admin123", version='latest'):
        """
        Parameters:

        address -- The server address to connect to
        port -- The port to connect to
        username -- The username to log into
        password -- The password to authenticate with
        version -- The URL version to apply by default we will use latest
        """
        # Instantiate an FTD client
        self.client = FTDClient(address=address, port=port, username=username, password=password, version=version)
        # Let's just auto login we will not use custom since this is a one at a time call and there will not be anything long lived
        # enough to use a custom token
        self.client.login()
        self.version = version

    def _create_auth_headers(self):
        """
        Helper method to fetch standard authorization headers for HTTP calls
        """
        auth_headers = {**self.client.get_headers()}
        auth_headers['Authorization'] = 'Bearer ' + self.client.get_access_token()
        return auth_headers

    def _get_base_url(self):
        """
        Helper to fetch base URL
        """
        return 'https://'+self.client.get_address_and_port_string()

    def _do_get_export_job_status(self, job_history_uuid):
        """
        Method to fetch export job status (helper method shouldn't be directly used)

        Parameters:
        job_history_uuid -- The job history uuid as returned from the export request

        Note:  The status response contains the name of the file which can be used
        to download the file
        """
        auth_headers = self._create_auth_headers()
        url = self._get_base_url()+'/api/fdm/'+self.version+'/jobs/configexportstatus/%s' % job_history_uuid
        result = requests.get(url, headers=auth_headers, verify=False)
        if result.status_code == 200:
            return result.json()
        else:
            raise Exception('Unable to get export job status code: '+str(result.status_code))


    def _get_import_status(self, job_history_id):
        """
        Helper method to fetch import job status

        Parameters:
        job_history_id - jobHistoryUuid value from the import job

        Return will be the JSON status document
        """
        auth_headers = self._create_auth_headers()
        url = self._get_base_url()+'/api/fdm/'+self.version+'/jobs/configimportstatus/'+str(job_history_id)
        return requests.get(url, headers=auth_headers, verify=False)

    def _do_import_file(self, file_name):
        """
        This method will do the actual import of the configuration file

        Parameters:

        file_name -- The file name to import (as returned by the upload method not fully qualified)
        """
        auth_headers = self._create_auth_headers()
        body = {
            "autoDeploy": False,
            "allowPendingChange": True,
            "diskFileName": file_name,
            "type": "scheduleconfigimport"
        }
        url = self._get_base_url()+'/api/fdm/'+self.version+'/action/configimport'
        response = requests.post(url, headers=auth_headers, verify=False, data=json.dumps(body))
        if response.status_code == 200:
            #success case
            response_json = response.json()
            # Now that we have successfully scheduled it let's check for status on the job
            while True:
                status = self._get_import_status(response_json['jobHistoryUuid'])
                if status.status_code == 200 and status.json()['status'] != 'IN_PROGRESS':
                    return status.json()
                elif status.status_code == 200 and status.json()['status'] == 'IN_PROGRESS':
                    # Pause to avoid going too fast in the case that it is still
                    # in progress
                    time.sleep(1)
                    continue
                elif status.status_code != 503:
                    # 503 indicates backend busy allow that and try again
                    raise Exception('Error getting import job status: '+str(status.status_code)+" "+str(status))

        else:
            raise Exception('Triggering import failed with response code: '+str(response.status_code)+" "+str(response))


    def _do_get(self, url, limit=None, offset=None):
        """
        This method will get data from the passed in URL and will return it in raw form

        Parameters:

        url -- The URL to fetch
        limit -- The number of records to fetch
        offset -- The offset to start fetching items from the list

        The return value is the returned data document
        """
        auth_headers = self._create_auth_headers()
        full_url = url
        append_ampersand = False
        if limit is not None or offset is not None:
            full_url += '?'
        if limit is not None:
            full_url += 'limit='+str(limit)
            append_ampersand = True
        if offset is not None:
            if append_ampersand:
                full_url += '&'
            full_url += 'offset='+str(offset)
        return requests.get(full_url, headers=auth_headers, verify=False).json()

    def _do_get_download_file(self, export_file_name, save_file_name):
        """
        Method to fetch export file by the name provided in the status call where it will
        save under the save_file_name on the filesystem.

        Parameters:
        export_file_name -- The name of the file as returned from the status api
        save_file_name -- This is the name to save the export file under
        """
        auth_headers = self._create_auth_headers()
        url = self._get_base_url()+'/api/fdm/'+self.version+'/action/downloadconfigfile/%s' % export_file_name
        response =  requests.get(url, headers=auth_headers, verify=False, stream=True)
        if response.status_code == 200:
            # we are good
            with open(save_file_name, 'wb') as filehandle:
                for chunk in response:
                    filehandle.write(chunk)
        else:
            raise Exception('Error downloading config file code: '+response.status_code)

    def do_download_export_file(self, export_file_name='/tmp/export.zip',  id_list=None, type_list=None, name_list=None, export_type='FULL_EXPORT'):
        """
        This method will export the current configuration

        Parameters:

        export_file_name -- File name to write the data out to
        id_list -- List of ID values to export
        type_list -- List of types to export (as defined in type field in JSON)
        name_list -- List of names to export (as defined in name field in JSON)

        id_list, type_list and name_list may be mixed and matched they will be applied in with OR

        No return value for success but an exception will be raised in case of failure.

        """
        auth_headers = self._create_auth_headers()

        body = {
            'doNotEncrypt': True,
            'configExportType': export_type,
            'deployedObjectsOnly': False,
            'type': 'scheduleconfigexport'
            }

        # Additional validation for entity_id_list usage
        if id_list is not None or type_list is not None or name_list is not None:
            # Create string to pass to the backend with filter criteria
            entity_id_list = []
            if id_list:
                entity_id_list.extend(id_list)
            if type_list:
                for objtype in type_list:
                    entity_id_list.append('type='+objtype)
            if name_list:
                for objname in name_list:
                    entity_id_list.append('name='+objname)
            body['entityIds'] = entity_id_list

        url = self._get_base_url()+'/api/fdm/'+self.version+'/action/configexport'
        response = requests.post(url, headers=auth_headers, verify=False, data=json.dumps(body))

        if response.status_code == 200:
            # Success get job status
            job_history_uuid = response.json()['jobHistoryUuid']
            job_status_response = None

            # Spin until job is done
            while True:
                if job_status_response is not None:
                    #sleep two seconds so we don't spin too fast
                    time.sleep(2)
                job_status_response = self._do_get_export_job_status(job_history_uuid)
                if job_status_response['status'] != 'IN_PROGRESS' and job_status_response['status'] != 'QUEUED':
                    break
            if job_status_response['status'] == 'SUCCESS':
                #worked snag the name and download the file
                return self._do_get_download_file(job_status_response['diskFileName'], save_file_name=export_file_name)
            else:
                raise Exception('Job terminated with unexpected status: '+job_status_response['status'])
        else:
            raise Exception('Failed to schedule export job code. Response status code: '+str(response.status_code))


    def do_upload_import_dict_list(self, dict_list, upload_file_name_without_path='importfile.txt'):
        """
        This method will take an import file and upload it to the connected device.

        Parameters:

        dict_list -- The list of dictionary objects
        upload_file_name_without_path -- Optional custom name to specify for file uploads

        Returns the job that was created.
        """
        auth_headers = self._create_auth_headers()
        # Create some big random numbers to act as the multi-part mime separator
        randtoken = random.randint(1000000, 500000000)
        randtoken2 = random.randint(1000000, 500000000)
        multipart_separator = (str(randtoken)+str(randtoken2))
        auth_headers['Content-Type'] = 'multipart/form-data; boundary='+multipart_separator
        # Next form the body of the request
        body = '--'+multipart_separator + '\r\n'
        body += 'Content-Disposition: form-data; name="fileToUpload"; filename="%s"\r\n' % upload_file_name_without_path
        body += 'Content-Type: text/plain\r\n\r\n'

        # File goes here
        body += json.dumps(dict_list)+'\r\n'
        body += '\r\n--'+multipart_separator + '--\r\n'

        url = self._get_base_url()+'/api/fdm/'+self.version+'/action/uploadconfigfile'
        response = requests.post(url, headers=auth_headers, verify=False, data=body)
        response_json = response.json()
        logging.debug(response_json)
        if response.status_code == 200:
            # success case trigger import to take place
            status_response = self._do_import_file(response_json['diskFileName'])
            logging.debug(status_response)
            if status_response['status'] == 'SUCCESS':
                return True
            else:
                raise Exception('Error importing config status: '+status_response['status']+' message: '+status_response['statusMessage'])
        else:
            raise Exception('Error uploading import file response code: '+str(response.status_code)+" "+str(response))

    def do_upload_import_file(self, file_name):
        """
        This method will take an import file and upload it to the connected device.

        Parameters:

        file_name -- import file

        Returns the job that was created.
        """
        if not os.path.isfile(file_name):
            raise Exception('Import file does not exist')
        else:
            file_name_without_path = os.path.split(file_name)[1]
        with open(file_name) as upload_filehandle:
            return self.do_upload_import_dict_list(json.loads(upload_filehandle.read()), upload_file_name_without_path=file_name_without_path)

    def extract_config_file_from_export(self, export_zip_file, dest_directory):
        """
        This method will extract the configuration file from the zip file

        Parameters:

        export_zip_file -- This is the input zip file
        dest_directory -- This is the directory to extract the contents into

        Return value is the full path to the extracted config file
        """
        with zipfile.ZipFile(export_zip_file, 'r') as zip_ref:
            zip_ref.extractall(dest_directory) #test for file name
        config_file_name = dest_directory + '/' + 'full_config.txt'
        if not os.path.isfile(config_file_name):
            config_file_name = dest_directory + '/' + 'pending_change_config.txt'
            if not os.path.isfile(config_file_name):
                config_file_name = dest_directory + '/' + 'partial_config.txt'
                if not os.path.isfile(config_file_name):
                    raise Exception('Unable to find config export txt file')
        return os.path.normpath(config_file_name)

    def convert_export_file_to_csv(self, export_zip_file, dest_directory):
        """
        This method will take an input zip file and will explode it into a csv file
        per type of object

        Parameters:
        export_zip_file -- This is the fully qualified path to the export zip file
        dest_directory -- This is the destination directory to create the CSV files in (recommend an empty directory)

        Note:  The raw full_config.txt file will be exploded in the dest_directory
        """
        type_to_object_list_dict = {}
        config_file_name = self.extract_config_file_from_export(export_zip_file, dest_directory)
        with open(config_file_name) as full_config_json_handle:
            full_export_doc = full_config_json_handle.read()
            full_export_json = json.loads(full_export_doc)
            #loop through json documents separating by type
            for myobject in full_export_json:
                if 'data' in myobject:
                    # it is a normal object check for type
                    if 'type' in myobject['data']:
                        if myobject['data']['type'] in type_to_object_list_dict:
                            type_list = type_to_object_list_dict[myobject['data']['type']]
                            type_list.append(myobject)
                        else:
                            type_to_object_list_dict[myobject['data']['type']] = [myobject]

        for key_type, value_obj_list in type_to_object_list_dict.items():
            parse_json.dict_list_to_csv(value_obj_list, dest_directory + '/' + key_type+'.csv')


    # TODO: Move this to the client class and extract the call to
    # decorate_dict_list_for_bulk?
    def do_get_with_paging(self, url, limit=None, filter_system_defined=True):
        """
        This method will read in all pages of data and return that as a list

        Parameters:

        url -- The URL to GET
        limit -- The optional limit of records per page

        Return value is the list of items retrieved.  The assumption is that
        whatever is returned has a paging wrapper and an "items" list of results.
        """
        offset = 0
        item_count = 0
        result_list = []
        while True:
            result = self._do_get(url, limit=limit, offset=offset)
            paging = result['paging']
            items = result['items']
            item_count += len(items)
            offset += len(items)
            result_list.extend(items)
            if item_count == paging['count'] or len(items) == 0:
                break
        if filter_system_defined:
            remove_list = []
            for myobject in result_list:
                if 'isSystemDefined' in myobject and myobject['isSystemDefined'] == True:
                    remove_list.append(myobject)
            for remove_item in remove_list:
                result_list.remove(remove_item)

            parse_json.decorate_dict_list_for_bulk(result_list)
        return result_list

    # TODO: Move this to the client class?
    def get_openapi_spec(self):
        """
        This method will return the parsed JSON structure of the openapi specification
        It will be fetched from the server that this client is connected to
        """
        auth_headers = self._create_auth_headers()
        url = self._get_base_url()+'/apispec/ngfw.json'
        response =  requests.get(url, headers=auth_headers, verify=False)
        if response.status_code == 200:
            swagger_json = json.loads(response.text)
            return swagger_json
        else:
            logging.error('Unable to retrieve OpenAPI spec')


    def _get_referenced_model_set(self, openapi_dict):
        """
        This will fetch all models that are referenced with a 200 return code
        from the OpenAPI spec dict

        Parameters:
        openapi_dict -- This is the dictionary containing the openapi spec parsed document

        Return is  a set of referenced models (referenced from an enabled URL)
        """

        # creating a list of all path structures doing this to re-use
        # some of the other JSON code where we can flatten dictionaries
        path_list = []
        for key, value in openapi_dict['paths'].items():
            path_list.append({key:value})

        # flatten hierarchy to key value pairs
        flat_list = parse_json.flatten_dict_list(path_list)
        referenced_model_list = []
        # Loop through all objects and look for $ref as that is the reference to the model
        # we will only include paths with 200 for the positive path as that should cover
        # the major request and response models
        for flat_obj in flat_list:
            for key in flat_obj:
                if key.find('$ref') != -1 and key.find('200') != -1:
                    referenced_model_list.append(flat_obj[key])

        # Value should look something like:  "#/definitions/ReferenceModel"
        # we need to parse off the last part after the "/" coercing to lower case to match
        # the type specification
        referenced_model_set = set([x.lower().split('/')[-1] for x in referenced_model_list])
        return referenced_model_set

    def _get_wrapper_to_model_dict(self, openapi_dict):
        """
        This method takes an input openapi spec dict and returns a dict with key as
        a wrapper class name and the value being a list of referenced class names.

        Where all class names are in lower case.

        Parameters:
        openapi_dict -- parsed openapi structure

        Returns:
        Dict as mentioned above
        """
        path_list = []
        for key, value in openapi_dict['definitions'].items():
            if key.lower().find('wrapper') != -1:
                path_list.append({key:value})

        flat_list = parse_json.flatten_dict_list(path_list)

        # at this point we have a list of flat dicts for all wrappers
        # we need to loop through and look for all $ref fields and snag the values
        wrapper_obj_to_ref_dict = {}
        for flat_obj in flat_list:
            ref_list = []
            for key, value in flat_obj.items():
                if key.find('$ref') != -1:
                    # split model name off of the value since we found a reference
                    ref_list.append(flat_obj[key].lower().split('/')[-1])
            # if we found references add it to the dict
            if len(ref_list) > 0:
                # Getting the key here is a bit funky it is encoded in the keys so we just pick
                # the first key and parse it off the front
                wrapper_obj_to_ref_dict[list(flat_obj)[0].split('.')[0].lower()] = ref_list
        return wrapper_obj_to_ref_dict

    def get_object_types(self):
        """This method will take the openapi specification and will determine all object
        types which can be queried via the export API.  This is a rough approximation
        attempting to filter out some of the object types which are not referenced by
        rest APIs or are wrapper classes.
        """
        openapi_dict = self.get_openapi_spec()

        # This method will look at the definitions and pulls out all wrappers
        # finding the list of referenced classes that they point to
        wrapper_obj_to_ref_dict = self._get_wrapper_to_model_dict(openapi_dict)

        # This is the set of URL referenced models which will  be
        # wrapper classes we need to expand that with the things the wrapper
        # references and then strip out the wrappers.
        referenced_model_set = self._get_referenced_model_set(openapi_dict)
        missing_models = []
        for referenced_model in referenced_model_set:
            if referenced_model in wrapper_obj_to_ref_dict:
                missing_models.extend(wrapper_obj_to_ref_dict[referenced_model])

        referenced_model_set.update(set(missing_models))

        # now strip out the wrappers
        referenced_model_list = [x for x in referenced_model_set if x.find('wrapper') == -1]
        referenced_model_list.sort()
        return referenced_model_list

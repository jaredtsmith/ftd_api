'''
Copyright (c) 2020 Cisco and/or its affiliates.

A copy of the License (MIT License) can be found in the LICENSE.TXT
file of this software.

Author: Jared T. Smith <jarmith@cisco.com>
Created: Dec 10, 2020
updated

'''
from ftd_api import parse_json
from ftd_api import parse_csv
from ftd_api.parse_json import pretty_print_json_file
from ftd_api.file_helper import read_string_from_file
from ftd_api.parse_yaml import write_dict_to_yaml_file
from ftd_api.parse_yaml import read_yaml_to_dict
from ftd_api.file_helper import print_string_to_file
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

    def __init__(self, client):
        """
        Parameters:

        client -- An instance of an FTDClient object from the ftd_client file
        """
        # Instantiate an FTD client
        self.client = client
        
    def _do_get_export_job_status(self, job_history_uuid):
        """
        Method to fetch export job status (helper method shouldn't be directly used)

        Parameters:
        job_history_uuid -- The job history uuid as returned from the export request

        Note:  The status response contains the name of the file which can be used
        to download the file
        """
        result = self.client.do_get_raw_with_base_url(f'/jobs/configexportstatus/{job_history_uuid}')
        if result.status_code == 200:
            return result.json()
        else:
            raise Exception('Unable to get export job status code: '+str(result.status_code))


    def _get_import_status(self, job_history_id):
        """
        Helper method to fetch import job status

        Parameters:
        job_history_id - jobHistoryUuid value from the import job

        Return will be an HTTP response document
        """
        return self.client.do_get_raw_with_base_url(f'/jobs/configimportstatus/{str(job_history_id)}')

    def _do_import_file(self, file_name, entity_filter_list=None):
        """
        This method will do the actual import of the configuration file

        Parameters:

        file_name -- The file name to import (as returned by the upload method not fully qualified)
        entity_filter_list -- See _create_entity_filter
        """
        body = {
            "autoDeploy": False,
            "allowPendingChange": True,
            "diskFileName": file_name,
            "type": "scheduleconfigimport"
        }
        if entity_filter_list:
            body['excludeEntities'] = entity_filter_list
        response = self.client.do_post_raw_with_base_url('/action/configimport', 
                                                         json.dumps(body))
        if response.status_code == 200:
            #success case
            response_json = response.json()
            # Now that we have successfully scheduled it let's check for status on the job
            while True:
                status = self._get_import_status(response_json['jobHistoryUuid'])
                if status.status_code == 200 and status.json()['status'] != 'IN_PROGRESS':
                    # 200 and not in progress is a terminal state
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
                    # Only remaining case is status == 503 indicating that we need to wait
                    # and try again we need to sleep in this case
                    time.sleep(1)

        else:
            raise Exception('Triggering import failed with response code: '+str(response.status_code)+" "+str(response))



    def _do_get_download_file(self, export_file_name, save_file_name):
        """
        Method to fetch export file by the name provided in the status call where it will
        save under the save_file_name on the filesystem.

        Parameters:
        export_file_name -- The name of the file as returned from the status api or the jobHistoryUuid value
        save_file_name -- This is the name to save the export file under
        """
        response = self.client.do_get_raw_with_base_url(f'/action/downloadconfigfile/{export_file_name}', 
                                                        extra_request_opts={'stream':True})
        if response.status_code == 200:
            # we are good
            with open(save_file_name, 'wb') as filehandle:
                for chunk in response:
                    filehandle.write(chunk)
        else:
            raise Exception('Error downloading config file code: '+response.status_code)


    def _create_entity_filter(self, id_list, type_list, name_list):
        """
        This creates a filter list structure as is used in both the import
        and export flows.
        
        This will return a list of elements like:
        "type=<type name>"
        "name=<object name>"
        "<id>"
        
        Parameters:
        id_list -- This is the list of ID values you would like to filter
        type_list -- This is the list of types you would like to filter
        name_list -- This is the list of names you would like to filter
        """
        entity_filter_list = None
        # Create string to pass to the back-end with filter criteria
        if id_list is not None or type_list is not None or name_list is not None:
            entity_filter_list = []
            if id_list:
                entity_filter_list.extend(id_list)
            if type_list:
                for objtype in type_list:
                    entity_filter_list.append('type=' + objtype)
            
            if name_list:
                for objname in name_list:
                    entity_filter_list.append('name=' + objname)
        
        return entity_filter_list

    def _do_download_export_file(self, export_file_name='/tmp/export.zip',  
                                 id_list=None, type_list=None, name_list=None, 
                                 export_type='FULL_EXPORT'):
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
        body = {
            'doNotEncrypt': True,
            'configExportType': export_type,
            'deployedObjectsOnly': False,
            'type': 'scheduleconfigexport'
            }

        # Additional validation for entity_filter_list usage
        entity_filter_list = self._create_entity_filter(id_list, type_list, name_list)
        if entity_filter_list:
            body['entityIds'] = entity_filter_list

        response = self.client.do_post_raw_with_base_url('/action/configexport', 
                                                         json.dumps(body))

        if response.status_code == 200:
            # Success get job status
            job_history_uuid = response.json()['jobHistoryUuid']
            job_status_response = None

            # Spin until job is done
            while True:
                if job_status_response is not None:
                    # Sleep two seconds so we don't spin too fast
                    time.sleep(2)
                job_status_response = self._do_get_export_job_status(job_history_uuid)
                if job_status_response['status'] != 'IN_PROGRESS' and job_status_response['status'] != 'QUEUED':
                    break
            if job_status_response['status'] == 'SUCCESS':
                # It worked retrieve the name and download the file
                return self._do_get_download_file(job_history_uuid, save_file_name=export_file_name)
            else:
                raise Exception('Job terminated with unexpected status: '+job_status_response['status'])
        else:
            raise Exception('Failed to schedule export job code. Response status code: '+str(response.status_code))


    def _do_upload_import_dict_list(self, 
                                    dict_list, 
                                    upload_file_name_without_path='importfile.txt', 
                                    entity_filter_list=None):
        """
        This method will take an import file and upload it to the connected device.

        Parameters:

        dict_list -- The list of dictionary objects
        upload_file_name_without_path -- Optional custom name to specify for file uploads
        entity_filter_list -- See _create_entity_filter

        Returns the job that was created.
        """
        # Create some big random numbers to act as the multi-part mime separator
        randtoken = random.randint(1000000, 500000000)
        randtoken2 = random.randint(1000000, 500000000)
        multipart_separator = (str(randtoken)+str(randtoken2))
        additional_headers = {}
        additional_headers['Content-Type'] = 'multipart/form-data; boundary='+multipart_separator
        # Next form the body of the request
        body = '--'+multipart_separator + '\r\n'
        body += 'Content-Disposition: form-data; name="fileToUpload"; filename="%s"\r\n' % upload_file_name_without_path
        body += 'Content-Type: text/plain\r\n\r\n'

        # File goes here
        body += json.dumps(dict_list)+'\r\n'
        body += '\r\n--'+multipart_separator + '--\r\n'

        response = self.client.do_post_raw_with_base_url('/action/uploadconfigfile',
                                                         body,
                                                         additional_headers=additional_headers)
        response_json = response.json()
        logging.debug(response_json)
        if response.status_code == 200:
            # success case trigger import to take place
            status_response = self._do_import_file(response_json['diskFileName'], entity_filter_list=entity_filter_list)
            logging.debug(status_response)
            if status_response['status'] == 'SUCCESS':
                return True
            else:
                raise Exception('Error importing config status: '+status_response['status']+' message: '+status_response['statusMessage'])
        else:
            raise Exception('Error uploading import file response code: '+str(response.status_code)+" "+str(response))

    def _do_upload_import_file(self, file_name):
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
            return self._do_upload_import_dict_list(json.loads(upload_filehandle.read()), upload_file_name_without_path=file_name_without_path)

    def _extract_config_file_from_export(self, export_zip_file, dest_directory, export_type=None):
        """
        This method will extract the configuration file from the zip file

        Parameters:

        export_zip_file -- This is the input zip file
        dest_directory -- This is the directory to extract the contents into
        export_type -- Optional specifies the type of export being done (FULL_EXPORT, PENDING_CHANGE_EXPORT or PARTIAL_EXPORT)

        Return value is the full path to the extracted config file
        """
        with zipfile.ZipFile(export_zip_file, 'r') as zip_ref:
            zip_ref.extractall(dest_directory) #test for file name
        
        # Possible types: FULL_EXPORT, PENDING_CHANGE_EXPORT and PARTIAL_EXPORT
        if export_type is not None:
            # File name logic can be more intelligent if the type is provided
            if export_type == 'FULL_EXPORT':
                config_file_name = dest_directory + '/' + 'full_config.txt'
            elif export_type == 'PENDING_CHANGE_EXPORT':
                config_file_name = dest_directory + '/' + 'pending_change_config.txt'
            elif export_type == 'PARTIAL_EXPORT':
                config_file_name = dest_directory + '/' + 'partial_config.txt'
            if not os.path.isfile(config_file_name):
                raise Exception(f'Unable to find config export txt file: {config_file_name}')
            else:
                return os.path.normpath(config_file_name)
        else:    
            # No type is provided search for the file
            config_file_name = dest_directory + '/' + 'full_config.txt'
            if not os.path.isfile(config_file_name):
                config_file_name = dest_directory + '/' + 'pending_change_config.txt'
                if not os.path.isfile(config_file_name):
                    config_file_name = dest_directory + '/' + 'partial_config.txt'
                    if not os.path.isfile(config_file_name):
                        raise Exception('Unable to find config export txt file')
            return os.path.normpath(config_file_name)

    def _convert_export_file_to_csv(self, export_zip_file, dest_directory, export_type=None):
        """
        This method will take an input zip file and will explode it into a csv file
        per type of object

        Parameters:
        export_zip_file -- This is the fully qualified path to the export zip file
        dest_directory -- This is the destination directory to create the CSV files in (recommend an empty directory)
        export_type -- Optional specifies the type of export being done (FULL_EXPORT, PENDING_CHANGE_EXPORT or PARTIAL_EXPORT)

        Note:  The raw full_config.txt file will be exploded in the dest_directory
        """
        type_to_object_list_dict = {}
        config_file_name = self._extract_config_file_from_export(export_zip_file, dest_directory, export_type=export_type)
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
        openapi_dict = self.client.get_openapi_spec()

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
    
    def url_export(self, url, destination_directory, output_format='JSON'):
        """
        This method will retrieve the JSON at a URL and will write out a file to the 
        passed in destination directory in the requested output format.
        
        Parameters:
        
        url -- The URL to request the data
        destination_directory -- The destination directory to write the data to
        output_format - enum (JSON | CSV | YAML)
        
        The path to the directory will be returned for the JSON and the path for the file returned for CSV and YAML
        """
        object_list = self.client.do_get_multi_page(url)
        parse_json.decorate_dict_list_for_bulk(object_list)
    
        return_path = None
        if output_format == 'JSON':
            logging.info('Exporting in JSON format')
            file_path = f'{destination_directory}/export.json'
            file_path = os.path.normpath(file_path)
            print_string_to_file(file_path, json.dumps(
                object_list, indent=3, sort_keys=True))
            return_path = destination_directory
            logging.info(f'JSON export can be found in: {file_path}')
    
        elif output_format == 'CSV':
            logging.info('Exporting in CSV format')
            parse_json.dict_list_to_csv(object_list, destination_directory)
            return_path = destination_directory
            logging.info(f'CSV files can be found in: {destination_directory}')
    
        elif output_format == 'YAML':
            logging.info('Exporting in YAML format')
            yaml_file = destination_directory+'/export.yaml'
            yaml_file = os.path.normpath(yaml_file)
            write_dict_to_yaml_file(yaml_file, object_list)
            return_path = yaml_file
            logging.info(f'YAML files can be found in: {yaml_file}')
        return return_path
    
    def bulk_export(self, destination_directory, pending_changes=False, type_list=None, id_list=None, name_list=None, output_format='JSON') :
        """
        This method will handle FULL_EXPORT, PENDING_CHANGE_EXPORT and PARTIAL_EXPORT however
        it will not handle URL export that will have its own special method.  PENDING_CHANGE_EXPORT
        will only include the pending objects it will not include any of the previously deployed
        objects and it will allow for filtering of those objects.
        
        Parameters:  
        
        destination_directory -- This is the destination directory to write the file to
        pending_changes -- Boolean (True | False) indicating if only pending changes should be considered
        type_list -- Python list of type names
        id_list -- Python list of id strings
        name_list -- Python list of names 
        output_format -- enum JSON, CSV, YAML
        
        This will return the directory or file path if there is only a single file output
        (directory for CSV, file for JSON/YAML)
        """
        # Base Case
        mode = 'FULL_EXPORT'
           
        # PENDING_CHANGE_EXPORT called for
        if pending_changes:
            mode = 'PENDING_CHANGE_EXPORT'
            if type_list is not None or id_list is not None or name_list is not None:
                raise Exception('PENDING_CHANGE_EXPORT cannot be used with entityIds filter list')
        else:
            # Note: Pending changes can support filters so the case for partial export is
            # when pending is not flagged but there is a filter 
            if type_list is not None or id_list is not None or name_list is not None:
                mode = 'PARTIAL_EXPORT'

        location_export_zip = os.path.normpath(destination_directory + '/myexport.zip')

        # Download export file
        self._do_download_export_file(
            export_file_name=location_export_zip,
            id_list=id_list,
            type_list=type_list,
            name_list=name_list,
            export_type=mode
        )

        result_path = None
        if output_format == 'CSV':
            logging.info('Exporting in CSV format')
            self._convert_export_file_to_csv(
                location_export_zip, destination_directory, export_type=mode)
            result_path = destination_directory
            logging.info('CSV files can be found in: '+str(destination_directory))
            
        elif output_format == 'JSON':
            logging.info('Exporting in JSON format')
            json_file = self._extract_config_file_from_export(
                location_export_zip, destination_directory, export_type=mode)
            pretty_print_json_file(json_file)
            result_path = json_file
            logging.info('JSON files can be found in: '+str(json_file))
            
        elif output_format == 'YAML':
            logging.info('Exporting in YAML format')
            json_file = self._extract_config_file_from_export(
                location_export_zip, destination_directory, export_type=mode)
            object_list = json.loads(read_string_from_file(json_file))
            yaml_file = destination_directory+'/export.yaml'
            write_dict_to_yaml_file(yaml_file, object_list)
            result_path = yaml_file
            logging.info('YAML file can be found in: '+str(yaml_file))
            
        return result_path
    
    def bulk_import(self, file_list, input_format='JSON', 
                    id_list=None, type_list=None, name_list=None):
        """
        This method will import a list of files in the given format
        
        Parameters:
        
        file_list -- A Python list of files to import
        input_format -- enum (JSON | CSV | YAML)
        id_list -- IDs to exclude from the import package
        type_list -- Types to exclude from the import package
        name_list -- Names to exclude from the import package
        
        This will return a bool indicating success
        """
        return_result = False
        
        entity_filter_list = self._create_entity_filter(id_list=id_list, type_list=type_list, name_list=name_list)
        if input_format == 'CSV':
            logging.info('Importing in CSV mode')
            object_list = []
            # need to loop  through files and convert to JSON and merge into a single list
            for inputfile in file_list:
                object_list.extend(parse_csv.parse_csv_to_dict(inputfile))
            if self._do_upload_import_dict_list(object_list, entity_filter_list=entity_filter_list):
                logging.info('Successfully completed import')
                return_result = True
            else:
                logging.error('Unable to complete import')
        elif input_format == 'JSON':
            logging.info('Importing in JSON mode')
            #JSON case just merge the JSON docs
            object_list = []
            for input_file in file_list:
                object_list.extend(
                    json.loads(read_string_from_file(input_file))
                )

            if self._do_upload_import_dict_list(object_list, entity_filter_list=entity_filter_list):
                logging.info('Successfully completed import')
                return_result = True
            else:
                logging.error('Unable to complete import')
        elif input_format == 'YAML':
            logging.info('Importing in YAML mode')
            #JSON case just merge the JSON docs
            object_list = []
            for input_file in file_list:
                object_list.extend(read_yaml_to_dict(input_file))
    
            if self._do_upload_import_dict_list(object_list, entity_filter_list=entity_filter_list):
                logging.info('Successfully completed import')
                return_result = True
            else:
                logging.error('Unable to complete import')  
        return return_result

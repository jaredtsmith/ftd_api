'''
Copyright (c) 2020 Cisco and/or its affiliates.

A copy of the License (MIT License) can be found in the LICENSE.TXT
file of this software.

Author: Jared T. Smith <jarmith@cisco.com>
Created: Dec 8, 2017
updated

'''
import requests
import json
import warnings
import logging
import time
from ftd_api.parse_json import pretty_print_json_string

class FTDClient:
    '''
    This is a basic FTD REST client that will assist in generating a login token
    '''

    # Default headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    def get_headers(self):
        return self.headers

    def get_access_token(self):
        return self.access_token

    def get_address(self):
        return self.server_address

    def get_port(self):
        return self.server_port

    def get_address_and_port_string(self):
        return str(self.server_address)+':'+str(self.server_port)
    
    def _create_auth_headers(self):
        """
        Helper method to fetch standard authorization headers for HTTP calls
        """
        auth_headers = {**self.get_headers()}
        auth_headers['Authorization'] = 'Bearer ' + self.get_access_token()
        return auth_headers

    def _get_base_url(self):
        """
        Helper to fetch base URL
        """
        return 'https://'+self.get_address_and_port_string()
    
    def do_post_raw(self, additional_url, body, additional_headers=None, extra_request_opts=None):
        """
        This method will do a post request and will return the response object
        
        Parameters:
        
        additional_url -- The URL after the ip and port 
        body -- The body to post
        additional_headers -- Other headers to append 
        extra_request_opts -- These are extra key value args to be passed into the requests post call
        
        This method will return the HTTP response object
        """
        all_headers = self._create_auth_headers()
        if additional_headers is not None:
            all_headers.update(additional_headers)

        url = self._get_base_url() + additional_url
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug(f'POST URL: {url}')
            if 'Content-Type' in all_headers and all_headers['Content-Type'].find('json') != -1:
                # Only log this for JSON document types
                logging.debug(f'POST body: {pretty_print_json_string(body)}')
        if extra_request_opts:
            response_payload = requests.post(url, headers=all_headers, verify=False, data=body, **extra_request_opts)
        else:
            response_payload = requests.post(url, headers=all_headers, verify=False, data=body)
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            if 'Content-Type' in response_payload.headers and response_payload.headers['Content-Type'].find('application/json') != -1:
                logging.debug(f'Response Payload: {str(pretty_print_json_string(response_payload.text))}')
        return response_payload
        
    def do_post_raw_with_base_url(self, additional_url, body, additional_headers=None, extra_request_opts=None):
        """
        This method will do a post request and will return the response object
        
        Parameters:
        
        additional_url -- The URL after the base FTD-API url /api/fdm/latest/ 
        body -- The body to post
        additional_headers -- Other headers to append 
        extra_request_opts -- These are extra key value args to be passed into the requests post call
        
        This method will return the HTTP response object
        """
        return self.do_post_raw(f'/api/fdm/{self.version}{additional_url}', 
                                body, 
                                additional_headers=additional_headers, 
                                extra_request_opts=extra_request_opts)
        
    def do_get_raw(self, additional_url, additional_headers=None, extra_request_opts=None):
        """
        This method does a generic get and takes the entire URI as an argument
        
        Parameters:
        
        additional_url -- This is the URL starting after the hostname and port
        additional_headers -- This is any additional header values that need to be passed
        extra_request_opts -- These are extra args that will be passed through to the requests get call
        
        This method will return a raw response object (not JSON)
        """
        all_headers = self._create_auth_headers()
        url = self._get_base_url() + additional_url
        if additional_headers is not None:
            all_headers.update(additional_headers)
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            logging.debug(f'GET URL: {url}')
        if extra_request_opts is not None:
            response_payload = requests.get(url, headers=all_headers, verify=False, **extra_request_opts)
        else:
            response_payload = requests.get(url, headers=all_headers, verify=False)
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            if 'Content-Type' in response_payload.headers and response_payload.headers['Content-Type'].find('application/json') != -1:
                logging.debug(f'Response Payload: {str(pretty_print_json_string(response_payload.text))}')
        return response_payload
    
    def do_get_raw_with_base_url(self, additional_url, additional_headers=None, extra_request_opts=None):
        """
        This method does a generic get and takes a URI after the base FTD API
        for example additional_urls is starting after /api/fdm/latest
        
        Parameters:
        
        additional_url -- The URI starting after the FTD-API base (/api/fdm/latest)
        additional_headers -- Additional headers that can be added
        extra_request_opts -- These are extra args that will be passed through to the requests get call
        
        This method will return a raw response object (not JSON)
        """
        return self.do_get_raw(f'/api/fdm/{self.version}{additional_url}', additional_headers=additional_headers, extra_request_opts=extra_request_opts)
       
    def do_get_single_page(self, additional_url, additional_headers=None, limit=None, offset=None):
        """
        This method will do a GET and assumes the response is a paged JSON document
        
        Parameters:

        additional_url -- This is the URI after the base FTD URI
        additional_headers -- Additional headers to append
        limit -- The number of records to fetch
        offset -- The offset to start fetching items from the list

        The return value is a parsed JSON document
        """
        append_ampersand = False
        if limit is not None or offset is not None:
            additional_url += '?'
        if limit is not None:
            additional_url += f'limit={str(limit)}'
            append_ampersand = True
        if offset is not None:
            if append_ampersand:
                additional_url += '&'
            additional_url += f'offset={str(offset)}'
        return self.do_get_raw_with_base_url(additional_url, additional_headers).json()
    
    def do_get_multi_page(self, additional_url, additional_headers=None, limit=None, filter_system_defined=True):
        """
        This method will read in all pages of data and return that as a list of 
        parsed JSON documents.

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
            result = self.do_get_single_page(additional_url,
                                    additional_headers=additional_headers, 
                                    limit=limit, 
                                    offset=offset)
            paging = result['paging']
            items = result['items']
            item_count += len(items)
            offset += len(items)
            result_list.extend(items)
            if item_count == paging['count'] or len(items) == 0:
                break
        if filter_system_defined:
            result_list = [x for x in result_list if 'isSystemDefined' not in x or x['isSystemDefined'] == False]
        return result_list

    def get_openapi_spec(self):
        """
        This method will return the parsed JSON structure of the openapi specification
        It will be fetched from the server that this client is connected to
        """
        response = self.do_get_raw('/apispec/ngfw.json')
        if response.status_code == 200:
            swagger_json = json.loads(response.text)
            return swagger_json
        else:
            logging.error('Unable to retrieve OpenAPI spec')

    def __init__(self, address='192.168.1.1', port=443, username="admin", password="Admin123", version='latest'):
        """
        Constructor used to initialize the bravado_client

        address: IP or hostname of the device to connect to
        port: Port number to connect to
        username: username to use (default 'admin')
        password: password to use (default 'Admin123')
        """
        # stash connectivity info for login call
        self.server_address = address
        self.server_port = port
        self.username = username
        self.password = password

        # access_token is used to save the current access token this could be either a normal login token or a custom
        # login token
        self.access_token = None
        # original_access_token is where we cache the normal 30 minute token obtained with admin credentials
        self.original_access_token = None
        # original_custom_token is where we store the custom token
        self.original_custom_token = None

        # WARNINGS
        requests.packages.urllib3.disable_warnings()
        # swagger doesn't like 'also_return_response' sent from FDM
        warnings.filterwarnings(
            'ignore', 'config also_return_response is not a recognized config key')

        # The following version is the API version that will be used
        if version == 'latest':
            self.version = str(version)
        else:
            self.version = 'v'+str(version)

    def login(self):
        """
        This is the normal login which will give you a ~30 minute session with no refresh.  Should be fine for short lived work.
        Do not use for sessions that need to last longer than 30 minutes.
        """
        # create auth payload
        payload = '{{"grant_type": "password", "username": "{}", "password": "{}"}}'.format(
            self.username, self.password)
        auth_headers = {**FTDClient.headers}
        r = requests.post("https://{}:{}/api/fdm/{}/fdm/token".format(self.server_address, self.server_port, self.version),
                          data=payload, verify=False, headers=auth_headers)
        if r.status_code == 400:
            raise Exception("Error logging in: {}".format(r.content))
        try:
            # This token will act as the
            self.access_token = r.json()['access_token']
            # cache the original token in case we do a custom login
            self.original_access_token = self.access_token
        except:
            logging.error(
                f'Unable to log into server: https://{self.server_address}:{self.server_port}')
            raise

    def login_custom(self, admin_client=None, session_length=86400):
        '''
        This is a custom login where you will by default get a 1 day session and can customize and create an even longer session
        session_length: number of seconds for the session to last (default 1 day of seconds)

        admin_client: administrative client to take a token from to obtain the custom token

        Return value is the JSON return value from the login transaction (can typically be ignored as an exception will be raised if unsuccessful)

        '''
        # This is where we will assign the admin token that will be used to obtain the
        # custom token (this is a normal 30 minute login token)
        admin_access_token = None

        if not admin_client:
            # login with a normal session first
            self.login()
            # take local token
            admin_access_token = self.access_token
        else:
            # take token out of admin_client
            admin_access_token = admin_client.original_access_token

        payload = '{{"grant_type": "custom_token", "access_token": "{}", "desired_expires_in": {}, "desired_refresh_expires_in":{}, "desired_subject":"python_client{}", "desired_refresh_count":3}}'.format(
            admin_access_token, session_length, (session_length*2), int(time.time()))

        # Note:  If using this with production code you should probably disable the following log for
        # security reasons.
        logging.debug('Custom payload: %s' % payload)
        auth_headers = {**FTDClient.headers}
        r = requests.post("https://{}:{}/api/fdm/{}/fdm/token".format(self.server_address, self.server_port, self.version),
                          data=payload, verify=False, headers=auth_headers)

        if r.status_code == 400:
            raise Exception("Error logging in: {}".format(r.content))

        try:
            self.access_token = r.json()['access_token']
            self.original_custom_token = self.access_token
        except:
            logging.error('Unable to find access token in JSON: %s' % r.json())
            raise

    def logout(self, preserve_tokens=False):
        '''
        Used for explicit session logout of a normal session token
        '''
        logout_payload = {'grant_type':      'revoke_token',
                          'access_token':    self.original_access_token,
                          'token_to_revoke': self.original_access_token}
        r = requests.post("https://{}:{}/api/fdm/{}/fdm/token".format(self.server_address, self.server_port, self.version),
                          data=json.dumps(logout_payload), verify=False, headers=FTDClient.headers)
        if r.status_code != 200:
            raise Exception('Logout failed: '+str(r.json()))
        if not preserve_tokens:
            self.access_token = None
            self.original_access_token = None
        logging.info("Performed normal token logout.")

    def logout_custom(self, admin_client=None, preserve_tokens=False):
        """
        Used for explicit session logout of a custom session token

        admin_client: Is the client with the administrative token to be used for revoking if not
        in the current client.  If an admin client is not passed the current client will be used.
        preserve_tokens: This is a flag to leave the tokens and not null them out for negative testing
        """

        if admin_client:
            admin_token_for_revoke = admin_client.original_access_token
        else:
            admin_token_for_revoke = self.original_access_token

        logout_payload = {'grant_type':      'revoke_token',
                          'access_token':    admin_token_for_revoke,
                          'token_to_revoke': self.original_custom_token}
        r = requests.post("https://{}:{}/api/fdm/{}/fdm/token".format(self.server_address, self.server_port, self.version),
                          data=json.dumps(logout_payload), verify=False, headers=FTDClient.headers)
        if r.status_code != 200:
            raise Exception('Logout failed: '+str(r.json()))
        if not preserve_tokens:
            self.access_token = None
            self.original_custom_token = None
        logging.info("Performed custom token logout.")

    def __enter__(self):
        """Magic function used to start a 'with' construct - in this case, logs in"""
        self.login()
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback):
        """Magic function used to end a 'with' construct - in this case, logs out"""
        if exception_type:
            logging.error("ERROR: {} ({}) -- {}".format(exception_type,
                                                        exception_value, exception_traceback))
        else:
            self.logout()

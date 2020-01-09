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
import tempfile
import logging
import os.path
import time


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

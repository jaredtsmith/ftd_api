'''
Copyright (c) 2020 Cisco and/or its affiliates.

A copy of the License (MIT License) can be found in the LICENSE.TXT
file of this software.

Author: Ted Bedwell
Created: July, 2019
'''

import logging
import coloredlogs


def configure_logging():
    '''
    Global logging initialization.
    '''

    # Woo Color
    coloredlogs.install(
        level='DEBUG', fmt='%(asctime)s %(levelname)s %(message)s')

    # Supress requests logging
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def enable_debug():
    '''
    Increase logging level to debug
    '''
    while not coloredlogs.is_verbose():
        coloredlogs.increase_verbosity()


def disable_debug():
    '''
    Decrease logging level below debug
    '''
    while coloredlogs.is_verbose():
        coloredlogs.decrease_verbosity()

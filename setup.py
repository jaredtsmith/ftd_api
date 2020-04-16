'''
Copyright (c) 2020 Cisco and/or its affiliates.

A copy of the License (MIT License) can be found in the LICENSE.TXT
file of this software.

Author: Ted Bedwell
Created: January 7, 2020
'''

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ftd_api",
    version="0.0.8",
    author="Jared T. Smith",
    author_email="jarsmith@cisco.com",
    description="Useful tooling for the Firepower Threat Defense on-box REST API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jaredtsmith/ftd_api",
    packages=setuptools.find_packages(),
    scripts=['scripts/ftd_bulk_tool', 'scripts/ftd_bulk_tool.py'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    keywords='cisco firepower ftd ngfw rest api',
    install_requires=[
        'pyaml>=19.12.0',
        'requests>=2.22.0',
        'coloredlogs>=10.0'
    ],
    project_urls={
        'Source': 'https://github.com/jaredtsmith/ftd_api',
        'FTD API Reference': 'https://developer.cisco.com/site/ftd_api-reference/',
        'Firepower DEVNET Portal': 'https://developer.cisco.com/firepower/',
        'Firepower Product Information': 'https://www.cisco.com/c/en/us/products/security/firewalls/index.html',
    }
)

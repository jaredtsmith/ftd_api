#!/usr/bin/bash
# docker_util.sh
#
#This tool provides a simple abstraction to handle bulk import/export tasks via the Firepower Threat Defese REST API.
#
#Copyright (c) 2020 Cisco and/or its affiliates.
#
#A copy of the License (MIT License) can be found in the LICENSE.TXT
#file of this software.
#
#Author: Jared T. Smith <jarmith@cisco.com>
#Created: March 30, 2020
ftd_bulk_tool(){
    DOCKER_LOCATION=`which docker`
    DOCKER_LOCATION="\"$DOCKER_LOCATION\""
    first_half_command=("$DOCKER_LOCATION" "run")
    second_half_command=()
    echo "first_half_command is: ${first_half_command[@]}"

    # Loop through passed in args and fix up paths passed through 
    # to mount those file systems into docker
    for var in "$@"
    do
        if [ "$var" == "-l" ]
        then
            SAVEL=true
            second_half_command+=("$var")
        elif [ "$SAVEL" = true ]
        then
            location="$var"
            SAVEL=false
            first_half_command+=("-v ")
            if [ ! -z "$OS" -a $OS='Windows_NT' ]
            then
                #Fixup path for cygwin/gitbash
                var=`cygpath -m $var|sed 's,/,\\\\,g'`
                first_half_command+=("\"$var:/tmp/a\"")
                second_half_command+=("\"//tmp//a\"")
            else
                first_half_command+=("\"$var:/tmp/a\"")
                second_half_command+=("\"/tmp/a\"")
            fi
        elif [ "$var" == "-c" ]
        then
            SAVEC=true
            second_half_command+=("$var")
        elif [ "$SAVEC" = true ]
        then
            location=`dirname "$var"`
            file=`basename "$var"`
            SAVEC=false
            first_half_command+=("-v ")
            if [ ! -z "$OS" -a $OS='Windows_NT' ]
            then
                #Fixup path for cygwin/gitbash
                location=`cygpath -m $location|sed 's,/,\\\\,g'`
                first_half_command+=("\"$location:/tmp/b\"")
                second_half_command+=("\"//tmp//b//$file\"")
            else
                first_half_command+=("\"$location:/tmp/b\"")
                second_half_command+=("\"/tmp/b/$file\"")
            fi
        else
            second_half_command+=("$var")
        fi
    done
    # Update the docker image so it doesn't get stale
    DOCKER_IMAGE_UPDATE_CMD="$DOCKER_LOCATION pull ciscongfw/ftdimportexportcmd"
    # Create call into docker
    FULL_first_half_command="${first_half_command[@]} "ciscongfw/ftdimportexportcmd" ${second_half_command[@]}"
    echo "Update Image: $DOCKER_IMAGE_UPDATE_CMD"
    eval "$DOCKER_IMAGE_UPDATE_CMD"
    echo "Call Bulk Tool: $FULL_first_half_command"
    eval "$FULL_first_half_command"
}

ftd_bulk_tool $@

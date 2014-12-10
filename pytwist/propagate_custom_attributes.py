# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# ex: set tabstop=4 :
# Please do not change the two lines above. See PEP 8, PEP 263.
"""
The MIT License (MIT)

Copyright (c) 2014 Dimiter Todorov

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

Script Details:
Propagate Custom Attributes From a base static device group to all children until reaching:
A dynamic group.
A static group with no device group children.

"""

#Import some basic python modules
import os
import sys
import getopt
from itertools import islice, chain

import time

#Import the OptionParser to allow for CLI options
from optparse import OptionParser

# HPSA - Depending on Windows/Unix select the directories containing the pytwist libraries.
if (sys.platform == 'win32'):
    pytwist_dir = (os.environ['SystemDrive'] + '\\Program Files\\Opsware\\smopylibs2')
    pylibs_dir = (os.environ['SystemDrive'] + '\\Program Files\\Opsware\\agent\\pylibs')
else:
    pytwist_dir = '/opt/opsware/pylibs2'
    pylibs_dir = '/opt/opsware/agent/pylibs2'

# Add the pytwist/pylibs directories to the path and import necessary modules.
sys.path.append(pylibs_dir)
sys.path.append(pytwist_dir)
from pytwist import *
from pytwist.com.opsware.search import Filter
from pytwist.com.opsware.fido import OperationConstants
from pytwist.com.opsware.device import DeviceGroupRef
from pytwist.com.opsware.job import JobRef,JobNotification,JobSchedule,JobInfoVO
from pytwist.com.opsware.script import ServerScriptRef, ServerScriptJobArgs

#Initialize the twist
ts = twistserver.TwistServer()

def batch(iterable, size):
    sourceiter = iter(iterable)
    while True:
        batchiter = islice(sourceiter, size)
        yield chain([batchiter.next()], batchiter)


# Main Script
if (__name__ == '__main__'):
    parser = OptionParser(description=__doc__, version="0.0.1",
                          usage=' Optional: [-u username -p password]')
    parser.add_option("-f", "--filter", action="store", dest="filter", metavar="filter", default="(ServerVO.hostName CONTAINS CTSPIKDCEMMON)",
                      help="Filter")
    parser.add_option("-u", "--user", action="store", dest="username", metavar="username", default="",
                      help="User Name")
    parser.add_option("-p", "--password", action="store", dest="password", metavar="password", default="",
                      help="Password")
    parser.add_option("-b", "--batch_size", action="store", dest="batch_size", metavar="batch_size", default=25,
                      help="Batch Size")
    parser.add_option("-d", "--debug", action="store", dest="debug", metavar="debug", default=0,
                      help="Debug?")


    try:
        (opts, args) = parser.parse_args(sys.argv[1:])
        if not opts.filter:
            parser.error("Filter")
    except getopt.GetoptError:
        parser.print_help()
        sys.exit(2)

    if opts.username and opts.password:
        ts.authenticate(opts.username,opts.password)
    elif os.environ.has_key('SA_USER') and os.environ.has_key('SA_PWD'):
        ts.authenticate(os.environ['SA_USER'],os.environ['SA_PWD'])
    else:
        print "Username and Password not provided. Script may fail unless running in OGSH. \nSpecify with -u username -p password"

    try:
        server_service=ts.server.ServerService
        server_script_service=ts.script.ServerScriptService
        device_group_service=ts.device.DeviceGroupService
        auth_service=ts.fido.AuthorizationService
    except:
        print "Error initializing services to HPSA"
        sys.exit(2)

    platform_filter="device_platform_name CONTAINS Win"


    server_filter = Filter()
    print opts.filter
    server_filter.expression="(%s)&(%s)" % (opts.filter,platform_filter)
    print server_filter.expression
    server_refs=server_service.findServerRefs(server_filter)

    for batch_iter in batch(server_refs,int(opts.batch_size)):

        server_array=[]
        for srv in batch_iter:
            server_array.append(srv)
        filtered_refs=auth_service.filterSingleTypeResourceList(OperationConstants.WRITE_DEVICE, server_array)
        if int(opts.debug)!=1:
            job_ref=server_service.startScanPatchPolicyCompliance(filtered_refs)
            print job_ref
            print filtered_refs
        else:
            print filtered_refs






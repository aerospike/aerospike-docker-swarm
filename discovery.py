#!/usr/bin/env python

# Copyright 2017 Aerospike All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import argparse
import socket
import subprocess
import sys
import time
from collections import Counter


ips = []

args = None

def parseArgs():
	global args
	parser = argparse.ArgumentParser()

	parser.add_argument( "--fqdn"
			, "--servicename"
			, dest="servicename"
			, help="The FQDN to resolve")
	parser.add_argument("-p"
			, "--port"
			, dest="port"
			, default=3002
			, help="The asinfo port")
	parser.add_argument("-i"
			, "--interval"
			, dest="interval"
			, default=60
			, type=float
			, help="The DNS polling interval in s. Defaults to 60")
	parser.add_argument("-v"
			, "--verbose"
			, dest="verbose"
			, action="store_true"
			, help="Print status changes")
	
	args = parser.parse_args()

def runCMD(cmd):
	#sys_cmd = "/usr/bin/asinfo -h %s -v \"tip=host=%s;port=$s\""%(host,target,port)
	proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	sys.stdout.write("\n")
	result = proc.stdout.read()
	if args.verbose:
		print "Running command: %s"%cmd
		print result
	return result

def addNode(IP, cluster):
	for node in cluster:
		command = "/usr/bin/asinfo -h %s -v \"tip:host=%s;port=%s\""%(node,IP,args.port)
		runCMD(command)

def removeNode(IP,cluster):
	for node in cluster:
		tipclear = "/usr/bin/asinfo -h %s -v \"tip-clear:host-port-list=%s;%s\""%(node,IP,args.port)
		runCMD(tipclear)
		alumniReset = "/usr/bin/asinfo -h %s  -v 'services-alumni-reset'"%node
		runCMD(alumniReset)
		

# monitor DNS

parseArgs()
lastKnownIPs = []
while True:
	try:
		ips = socket.gethostbyname_ex(args.servicename)[2]
	except:
		# connection/resolve error: fast retry
		time.sleep(1)
	# if no DNS change, sleep
	if Counter(ips) == Counter(lastKnownIPs):
		time.sleep(args.interval)
		continue;
	# if complete DNS change, tip everyone
	if len([ val for val in ips if val in lastKnownIPs]) == 0:
		addNode(ips[0],ips)
	else:
		# Clear removed nodes
		for oldHost in lastKnownIPs:
			if oldHost not in ips:
				removeNode(oldHost,ips)
		# Add new nodes
		for newHost in ips:
			if newHost not in lastKnownIPs:
				addNode(newHost,lastKnownIPs)
	lastKnownIPs = ips
	if args.verbose:
		print "%s %s : %s"%(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), args.servicename, lastKnownIPs)
	

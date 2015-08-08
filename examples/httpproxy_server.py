#!/usr/bin/env python
# -*- coding: utf-8 -*-

#########################################################################
# Copyright/License Notice (BSD License)                                #
#########################################################################
#########################################################################
# Copyright (c) 2010-2012, Daniel Knaggs - 2E0DPK/M6DPK                 #
# All rights reserved.                                                  #
#                                                                       #
# Redistribution and use in source and binary forms, with or without    #
# modification, are permitted provided that the following conditions    #
# are met: -                                                            #
#                                                                       #
#   * Redistributions of source code must retain the above copyright    #
#     notice, this list of conditions and the following disclaimer.     #
#                                                                       #
#   * Redistributions in binary form must reproduce the above copyright #
#     notice, this list of conditions and the following disclaimer in   #
#     the documentation and/or other materials provided with the        #
#     distribution.                                                     #
#                                                                       #
#   * Neither the name of the author nor the names of its contributors  #
#     may be used to endorse or promote products derived from this      #
#     software without specific prior written permission.               #
#                                                                       #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS   #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT     #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR #
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT  #
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, #
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT      #
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, #
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY #
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT   #
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE #
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  #
#########################################################################

from danlog import DanLog
from ddp import *
import os
import sys
from xml.dom import minidom


###########
# Globals #
###########
conn = None

log = DanLog("HTTPProxyServer")


#############
# Constants #
#############
ALLOW_UNSIGNED_PACKETS = False

BACKEND_DATAMODE = "PSK500R"
BACKEND_HOSTNAME = "localhost"
BACKEND_PORT = 7362

DEBUG_MODE = False
DISABLE_CRYPTO = False

PROXY_CALLSIGN = "CHANGEME"

SPECIFICATION = 0

UPSTREAM_PROXY_IP = ""
UPSTREAM_PROXY_PORT = 0
USE_TCP = 0

XML_SETTINGS_FILE = "httpproxyserver-settings.xml"


###############
# Subroutines #
###############
def cBool(value):
	if str(value).lower() == "false" or str(value) == "0":
		return False
		
	elif str(value).lower() == "true" or str(value) == "1":
		return True
		
	else:
		return False

def exitProgram():
	sys.exit(0)

def ifNoneReturnZero(strinput):
	if strinput is None:
		return 0
	
	else:
		return strinput

def iif(testval, trueval, falseval):
	if testval:
		return trueval
	
	else:
		return falseval

def main():
	log.info("""
#########################################################################
# Copyright/License Notice (BSD License)                                #
#########################################################################
#########################################################################
# Copyright (c) 2010-2012, Daniel Knaggs - 2E0DPK/M6DPK                 #
# All rights reserved.                                                  #
#                                                                       #
# Redistribution and use in source and binary forms, with or without    #
# modification, are permitted provided that the following conditions    #
# are met: -                                                            #
#                                                                       #
#   * Redistributions of source code must retain the above copyright    #
#     notice, this list of conditions and the following disclaimer.     #
#                                                                       #
#   * Redistributions in binary form must reproduce the above copyright #
#     notice, this list of conditions and the following disclaimer in   #
#     the documentation and/or other materials provided with the        #
#     distribution.                                                     #
#                                                                       #
#   * Neither the name of the author nor the names of its contributors  #
#     may be used to endorse or promote products derived from this      #
#     software without specific prior written permission.               #
#                                                                       #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS   #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT     #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR #
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT  #
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, #
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT      #
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, #
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY #
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT   #
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE #
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  #
#########################################################################
""")
	log.info("")
	log.info("HTTP Proxy - Server")
	log.info("===================")
	log.info("Checking settings...")
	
	if os.path.exists(XML_SETTINGS_FILE) == False:
		log.warn("The XML settings file doesn't exist, create one...")
		
		xmlProxySettingsWrite()
		
		
		log.info("The XML settings file has been created using the default settings.  Please edit it and restart the proxy server once you're happy with the settings.")
		
		exitProgram()
		
	else:
		log.info("Reading XML settings...")
		
		xmlProxySettingsRead()
		
		# This will ensure it will have any new settings in
		if os.path.exists(XML_SETTINGS_FILE + ".bak"):
			os.unlink(XML_SETTINGS_FILE + ".bak")
			
		os.rename(XML_SETTINGS_FILE, XML_SETTINGS_FILE + ".bak")
		xmlProxySettingsWrite()
	
	
	log.info("Checking the config...")
	
	if PROXY_CALLSIGN == "" or PROXY_CALLSIGN == "CHANGEME":
		log.error("The proxy server callsign is invalid.  Please edit the config XML file.")
		exitProgram()
		
	
	log.info("Setting up DDP...")
	ddp = DDP(hostname = BACKEND_HOSTNAME, port = BACKEND_PORT, data_mode = BACKEND_DATAMODE, timeout = 120., ack_timeout = 60., tx_hangtime = 1.25, data_length = 4096, specification = SPECIFICATION, disable_ec = False, disable_crypto = DISABLE_CRYPTO, allow_unsigned_packets = ALLOW_UNSIGNED_PACKETS, application = "DDP Example: HTTP Proxy", ignore_broadcast_packets = True, debug_mode = DEBUG_MODE)
	
	ddp.setCallsign(PROXY_CALLSIGN)
	
	
	log.info("Waiting for a packet...")
	
	while True:
		try:
			data = ddp.receiveDataFromAny(PROXY_CALLSIGN)
			
			if data is not None:
				# Check the flags
				d = data[0]
				packet = data[1]
				
				# Pass on the packet to the upstream proxy server
				try:
					log.info("Passing packet to upstream proxy on %s:%d..." % (UPSTREAM_PROXY_IP, UPSTREAM_PROXY_PORT))
					
					skt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					skt.connect((UPSTREAM_PROXY_IP, UPSTREAM_PROXY_PORT))
					
					buf = ""
					
					log.info("Buffering data...")
					
					skt.settimeout(1)
					skt.sendall(d + "\n\n")
					
					while True:
						try:
							data = skt.recv(4096)
							
							if data:
								buf += data
								
							else:
								break
							
						except Exception, ex:
							log.fatal(ex)
							break
							
					skt.close()
					
					
					# Send back the result
					log.info("Sending the packet from the proxy back to client...")
					ddp.transmitData(PROXY_CALLSIGN, "", packet[ddp.SECTION_SOURCE], buf, USE_TCP, 1)
					
				except Exception, ex:
					print ex
					
		except KeyboardInterrupt:
			break
			
		except Exception, ex:
			log.fatal(ex)
	
	
	log.info("Cleaning up...")
	ddp.dispose()
	ddp = None
	
	log.info("Exiting...")
	exitProgram()
	
def xmlProxySettingsRead():
	global ALLOW_UNSIGNED_PACKETS, BACKEND_DATAMODE, BACKEND_HOSTNAME, BACKEND_PORT, DEBUG_MODE, DISABLE_CRYPTO, PROXY_CALLSIGN, SPECIFICATION, UPSTREAM_PROXY_IP, UPSTREAM_PROXY_PORT, USE_TCP
	
	
	if os.path.exists(XML_SETTINGS_FILE):
		xmldoc = minidom.parse(XML_SETTINGS_FILE)
		
		myvars = xmldoc.getElementsByTagName("Setting")
		
		for var in myvars:
			for key in var.attributes.keys():
				val = str(var.attributes[key].value)
				
				# Now put the correct values to correct key
				if key == "ServerCallsign":
					PROXY_CALLSIGN = val
					
				elif key == "BackendDataMode":
					BACKEND_DATAMODE = val.upper()
					
				elif key == "BackendHostname":
					BACKEND_HOSTNAME = val
					
				elif key == "BackendPort":
					BACKEND_PORT = val.upper()
					
				elif key == "Specification":
					SPECIFICATION = int(val)
					
				elif key == "UseTCP":
					USE_TCP = int(val)
					
				elif key == "AllowUnsignedPackets":
					ALLOW_UNSIGNED_PACKETS = cBool(val)
					
				elif key == "DisableCrypto":
					DISABLE_CRYPTO = cBool(val)
					
				elif key == "DebugMode":
					DEBUG_MODE = cBool(val)
					
				elif key == "UpstreamProxyIP":
					UPSTREAM_PROXY_IP = val
					
				elif key == "UpstreamProxyPort":
					UPSTREAM_PROXY_PORT = int(val)
					
				else:
					log.warn("XML setting attribute \"%s\" isn't known.  Ignoring..." % key)
	
def xmlProxySettingsWrite():
	if os.path.exists(XML_SETTINGS_FILE) == False:
		xmloutput = file(XML_SETTINGS_FILE, "w")
		
		
		xmldoc = minidom.Document()
		
		# Create header
		settings = xmldoc.createElement("HTTPProxyServer")
		xmldoc.appendChild(settings)
		
		# Write each of the details one at a time, makes it easier for someone to alter the file using a text editor
		var = xmldoc.createElement("Setting")
		var.setAttribute("BackendDataMode", str(BACKEND_DATAMODE))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("BackendHostname", str(BACKEND_HOSTNAME))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("BackendPort", str(BACKEND_PORT))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("ServerCallsign", str(PROXY_CALLSIGN))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("Specification", str(SPECIFICATION))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("UseTCP", str(USE_TCP))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("AllowUnsignedPackets", str(ALLOW_UNSIGNED_PACKETS))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("DisableCrypto", str(DISABLE_CRYPTO))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("DebugMode", str(DEBUG_MODE))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("UpstreamProxyIP", str(UPSTREAM_PROXY_IP))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("UpstreamProxyPort", str(UPSTREAM_PROXY_PORT))
		settings.appendChild(var)
		
		
		# Finally, save to the file
		xmloutput.write(xmldoc.toprettyxml())
		xmloutput.close()


##########################
#  Main
##########################
if __name__ == "__main__":
	main()

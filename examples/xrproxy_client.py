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


from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer

from danlog import DanLog
from ddp import *
import os
import pickle
import sys
from xml.dom import minidom


###########
# Globals #
###########
client_callsign = ""

log = DanLog("XRProxyClient")


#############
# Constants #
#############
ALLOW_UNSIGNED_PACKETS = False

BACKEND_DATAMODE = "PSK500R"
BACKEND_HOSTNAME = "localhost"
BACKEND_PORT = 7362

DEBUG_MODE = False
DISABLE_CRYPTO = False

SERVER_PORT = 9779
SPECIFICATION = 0

USE_TCP = 0

XML_SETTINGS_FILE = "xrproxyclient-settings.xml"


###########
# Classes #
###########
class XMLRPCFunctionHandler():
	def __init__(self, ddp):
		self.ddp = ddp
	
	def __getattr__(self, attrname):
		def fun(*args, **kwargs):
			# Send the request off
			tosend = pickle.dumps(args, protocol = 2)
			
			self.ddp.transmitData(client_callsign, "", "XMLRPC", tosend, USE_TCP, 1)
			
			# Await it's return
			data = self.ddp.receiveDataFromAny(client_callsign)
			
			if data is not None:
				# Check the flags
				d = data[0]
				packet = data[1]
				
				return pickle.loads(d)
				
			else:
				return None
		
		return fun

class XMLRPCRequestHandler(SimpleXMLRPCRequestHandler):
	rpc_paths = ("/xmlrpc/",)


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

def main():
	global client_callsign
	
	
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
	log.info("XMLRPC Proxy - Client")
	log.info("=====================")
	log.info("Checking settings...")
	
	if os.path.exists(XML_SETTINGS_FILE) == False:
		log.warn("The XML settings file doesn't exist, create one...")
		
		xmlXRPSettingsWrite()
		
		
		log.info("The XML settings file has been created using the default settings.  Please edit it and restart the XMLRPC proxy client once you're happy with the settings.")
		
		exitProgram()
		
	else:
		log.info("Reading XML settings...")
		
		xmlXRPSettingsRead()
		
		# This will ensure it will have any new settings in
		if os.path.exists(XML_SETTINGS_FILE + ".bak"):
			os.unlink(XML_SETTINGS_FILE + ".bak")
			
		os.rename(XML_SETTINGS_FILE, XML_SETTINGS_FILE + ".bak")
		xmlXRPSettingsWrite()
	
	
	log.info("Setting up DDP...")
	ddp = DDP(hostname = BACKEND_HOSTNAME, port = BACKEND_PORT, data_mode = BACKEND_DATAMODE, timeout = 60., ack_timeout = 30., tx_hangtime = 1.25, data_length = 1024, specification = SPECIFICATION, disable_ec = False, disable_crypto = DISABLE_CRYPTO, allow_unsigned_packets = ALLOW_UNSIGNED_PACKETS, application = "DDP Example: XMLRPC Proxy", ignore_broadcast_packets = True, debug_mode = DEBUG_MODE)
	
	log.info("")
	
	while client_callsign == "":
		print "Please enter your callsign: ",
		
		client_callsign = readInput().strip().upper()
		log.info("")
	
	ddp.setCallsign(client_callsign)
	
	
	log.info("Preparing XMLRPC client...")
	server = SimpleXMLRPCServer(("", SERVER_PORT), requestHandler = XMLRPCRequestHandler, logRequests = False)
	
	
	log.info("Registering functions...")
	server.register_instance(XMLRPCFunctionHandler(ddp))
	
	
	log.info("Starting server...")
	
	try:
		server.serve_forever()
		
	except KeyboardInterrupt:
		pass
		
	except Exception, ex:
		log.fatal(ex)
	
	
	log.info("Cleaning up...")
	ddp.dispose()
	ddp = None
	
	log.info("Exiting...")
	exitProgram()

def readInput():
	return sys.stdin.readline().replace("\r", "").replace("\n", "")

def xmlXRPSettingsRead():
	global ALLOW_UNSIGNED_PACKETS, BACKEND_DATAMODE, BACKEND_HOSTNAME, BACKEND_PORT, DEBUG_MODE, DISABLE_CRYPTO, SERVER_PORT, SPECIFICATION, USE_TCP
	
	
	if os.path.exists(XML_SETTINGS_FILE):
		xmldoc = minidom.parse(XML_SETTINGS_FILE)
		
		myvars = xmldoc.getElementsByTagName("Setting")
		
		for var in myvars:
			for key in var.attributes.keys():
				val = str(var.attributes[key].value)
				
				# Now put the correct values to correct key
				if key == "BackendDataMode":
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
					
				elif key == "ServerPort":
					SERVER_PORT = int(val)
					
				else:
					log.warn("XML setting attribute \"%s\" isn't known.  Ignoring..." % key)

def xmlXRPSettingsWrite():
	if os.path.exists(XML_SETTINGS_FILE) == False:
		xmloutput = file(XML_SETTINGS_FILE, "w")
		
		
		xmldoc = minidom.Document()
		
		# Create header
		settings = xmldoc.createElement("XRPClient")
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
		var.setAttribute("ServerPort", str(SERVER_PORT))
		settings.appendChild(var)
		
		
		# Finally, save to the file
		xmloutput.write(xmldoc.toprettyxml())
		xmloutput.close()


##########################
#  Main
##########################
if __name__ == "__main__":
	main()

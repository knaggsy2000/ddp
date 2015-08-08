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
import signal
import socket
import sys
from xml.dom import minidom


###########
# Globals #
###########
client_callsign = ""

ddp = None

listener_tcp = None
listener_tcp_alive = False
listener_tcp_thread = None
log = DanLog("HTTPProxyClient")

server_callsign = ""


#############
# Constants #
#############
ALLOW_UNSIGNED_PACKETS = False

BACKEND_DATAMODE = "PSK500R"
BACKEND_HOSTNAME = "localhost"
BACKEND_PORT = 7362

DEBUG_MODE = False
DISABLE_CRYPTO = False

LISTEN_PORT = 54321

SPECIFICATION = 0

USE_TCP = 0

XML_SETTINGS_FILE = "httpproxyclient-settings.xml"


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
	global listener_tcp, listener_tcp_alive
	
	
	listener_tcp_alive = False
	
	if listener_tcp is not None:
		listener_tcp.close()
		listener_tcp = None
	
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

def listenerSig(signal, frame):
	waitpid(-1, WNOHANG)

def listenerTCPHandler(client, address):
	while True:
		try:
			data = client.recv(4096)
			addr = ""
			
			if data:
				# Pass the data on to DDP to transmit
				log.info("Passing TCP packets on to DDP...")
				
				if ddp.transmitData(client_callsign, "", server_callsign, str(data), USE_TCP):
					log.info("Receiving data...")
					rx = ddp.receiveData(client_callsign, server_callsign)
					
					if rx is not None:
						rxdata = rx[0]
						
						if rxdata == "":
							rxdata = "HTTP/1.1 404 Not Found\n\n<html>No data was received from DDP.</html>\n\n"
						
						# Send it back to the client
						client.sendall(rxdata)
					
				else:
					log.warn("Failed to pass the packet on to DDP.")
					
					client.sendall("HTTP/1.1 404 Not Found\n\n<html>Failed to transmit the packet via DDP.</html>\n\n")
				
				# Get the connection closed
				break
				
			else:
				break
			
		except Exception, ex:
			log.fatal(ex)
	
	
	log.info("Closed connection from %s:%d." % (address[0], address[1]))
	client.close()

def listenerTCPSub():
	global listener_tcp, listener_tcp_alive
	
	
	while listener_tcp_alive:
		try:
			client, address = listener_tcp.accept()
			
			log.info("Accepted connection from %s:%d." % (address[0], address[1]))
			
			listenerTCPHandler(client, address)
			
		except Exception, ex:
			log.fatal(ex)
		
	if listener_tcp is not None:
		listener_tcp.close()

def main():
	global client_callsign, ddp, listener_tcp, listener_tcp_alive, listener_tcp_thread, server_callsign
	
	
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
	log.info("HTTP Proxy - Client")
	log.info("===================")
	log.info("Checking settings...")
	
	if os.path.exists(XML_SETTINGS_FILE) == False:
		log.warn("The XML settings file doesn't exist, create one...")
		
		xmlProxySettingsWrite()
		
		
		log.info("The XML settings file has been created using the default settings.  Please edit it and restart the proxy client once you're happy with the settings.")
		
		exitProgram()
		
	else:
		log.info("Reading XML settings...")
		
		xmlProxySettingsRead()
		
		# This will ensure it will have any new settings in
		if os.path.exists(XML_SETTINGS_FILE + ".bak"):
			os.unlink(XML_SETTINGS_FILE + ".bak")
			
		os.rename(XML_SETTINGS_FILE, XML_SETTINGS_FILE + ".bak")
		xmlProxySettingsWrite()
	
	
	log.info("Need to configure who we are and where we are talking to...")
	
	print ""
	
	if server_callsign == "":
		print "Please enter the proxy server callsign: ",
		
		server_callsign = readInput().strip().upper()
		print ""
	
	if client_callsign == "":
		print "Please enter your callsign: ",
		
		client_callsign = readInput().strip().upper()
		print ""
	
	
	if server_callsign == "" or client_callsign == "":
		log.error("You didn't specify the callsigns correctly.")
		exitProgram()
	
	
	log.info("Setting up local port for client to proxy to...")
	
	try:
		listener_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		listener_tcp.bind(("127.0.0.1", LISTEN_PORT))
		listener_tcp.listen(0)
		
		signal.signal(signal.SIGCHLD, listenerSig)
		
		
		listener_tcp_alive = True
		
		
		# Start the listener thread
		listener_tcp_thread = threading.Thread(target = listenerTCPSub)
		listener_tcp_thread.setDaemon(1)
		listener_tcp_thread.start()
		
	except socket.error, ex:
		if listener_tcp:
			listener_tcp.close()
			
		log.fatal(ex)
			
	except Exception, ex:
		log.fatal(ex)
	
	
	log.info("Setting up DDP...")
	ddp = DDP(hostname = BACKEND_HOSTNAME, port = BACKEND_PORT, data_mode = BACKEND_DATAMODE, timeout = 120., ack_timeout = 60., tx_hangtime = 1.25, data_length = 4096, specification = SPECIFICATION, disable_ec = False, disable_crypto = DISABLE_CRYPTO, allow_unsigned_packets = ALLOW_UNSIGNED_PACKETS, application = "DDP Example: HTTP Proxy", ignore_broadcast_packets = True, debug_mode = DEBUG_MODE)
	
	ddp.setCallsign(client_callsign)
	
	
	log.info("Waiting for a packet...")
	
	while True:
		try:
			time.sleep(0.1)
			
		except KeyboardInterrupt:
			break
			
		except Exception, ex:
			log.fatal(ex)
	
	
	log.info("Cleaning up...")
	ddp.dispose()
	ddp = None
	
	log.info("Exiting...")
	exitProgram()

def readInput():
	return sys.stdin.readline().replace("\r", "").replace("\n", "")

def xmlProxySettingsRead():
	global ALLOW_UNSIGNED_PACKETS, BACKEND_DATAMODE, BACKEND_HOSTNAME, BACKEND_PORT, DEBUG_MODE, DISABLE_CRYPTO, LISTEN_PORT, SPECIFICATION, USE_TCP
	
	
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
					
				elif key == "ListenPort":
					LISTEN_PORT = int(val)
					
				elif key == "DebugMode":
					DEBUG_MODE = cBool(val)
					
				else:
					log.warn("XML setting attribute \"%s\" isn't known.  Ignoring..." % key)

def xmlProxySettingsWrite():
	if os.path.exists(XML_SETTINGS_FILE) == False:
		xmloutput = file(XML_SETTINGS_FILE, "w")
		
		
		xmldoc = minidom.Document()
		
		# Create header
		settings = xmldoc.createElement("HTTPProxyClient")
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
		var.setAttribute("ListenPort", str(LISTEN_PORT))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("DebugMode", str(DEBUG_MODE))
		settings.appendChild(var)
		
		
		# Finally, save to the file
		xmloutput.write(xmldoc.toprettyxml())
		xmloutput.close()


##########################
#  Main
##########################
if __name__ == "__main__":
	main()

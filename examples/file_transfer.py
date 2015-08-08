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

from datetime import *
from danlog import DanLog
from ddp import *
import os
import sys
import threading
from xml.dom import minidom


#############
# Variables #
#############
client_callsign = ""

ddp = None

log = DanLog("FileTransfer")

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

SPECIFICATION = 0

USE_TCP = 0

XML_SETTINGS_FILE = "filetransfer-settings.xml"


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
	global client_callsign, ddp, rxalive, server_callsign
	
	
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
	log.info("File Transfer")
	log.info("=============")
	log.info("Checking settings...")
	
	if os.path.exists(XML_SETTINGS_FILE) == False:
		log.warn("The XML settings file doesn't exist, create one...")
		
		xmlFTSettingsWrite()
		
		
		log.info("The XML settings file has been created using the default settings.  Please edit it and restart File Transfer once you're happy with the settings.")
		
		exitProgram()
		
	else:
		log.info("Reading XML settings...")
		
		xmlFTSettingsRead()
		
		# This will ensure it will have any new settings in
		if os.path.exists(XML_SETTINGS_FILE + ".bak"):
			os.unlink(XML_SETTINGS_FILE + ".bak")
			
		os.rename(XML_SETTINGS_FILE, XML_SETTINGS_FILE + ".bak")
		xmlFTSettingsWrite()
	
	log.info("Setting up DDP...")
	ddp = DDP(hostname = BACKEND_HOSTNAME, port = BACKEND_PORT, data_mode = BACKEND_DATAMODE, timeout = 60., ack_timeout = 30., tx_hangtime = 1.25, data_length = 512, specification = SPECIFICATION, disable_ec = False, disable_crypto = DISABLE_CRYPTO, allow_unsigned_packets = ALLOW_UNSIGNED_PACKETS, application = "DDP Example: File Transfer", ignore_broadcast_packets = True, debug_mode = DEBUG_MODE)
	
	log.info("")
	
	while client_callsign == "":
		log.info("Please enter your callsign: ", newline = False)
		
		client_callsign = readInput().strip().upper()
		log.info("")
	
	ddp.setCallsign(client_callsign)
	
	
	while server_callsign == "":
		log.info("Please enter the remote callsign: ", newline = False)
		
		server_callsign = readInput().strip().upper()
		log.info("")
	
	
	log.info("Ready.")
	
	while True:
		try:
			log.info("")
			log.info("FT> ", newline = False)
			
			c = readInput().strip()
			log.info("")
			
			if c <> "":
				if c == "rx":
					log.info("Waiting for file...")
					
					data = ddp.receiveDataFromAny(client_callsign)
					
					if data is not None:
						# Check the flags
						d = data[0]
						dd = d.split("\n")
						packet = data[1]
						
						if len(dd) == 4:
							if dd[0] == "FILE_TRANSFER":
								filename = dd[1]
								size = int(dd[2])
								checksum = dd[3]
								
								
								log.info("Receiving file '%s' (%d bytes), checksum %s..." % (filename, size, checksum))
								
								rx = ddp.receiveData(packet[ddp.SECTION_DESTINATION], packet[ddp.SECTION_SOURCE])
								
								if rx is not None:
									rxdata = rx[0]
									
									if len(rxdata) > 0:
										t = datetime.now()
										tmp = str(t.strftime("%d%m%Y%H%M%S"))
										
										
										f = open(tmp + "-" + filename, "wb")
										f.write(rxdata)
										f.flush()
										f.close()
										
										wrote_checksum = ddp.sha1(rxdata)
										
										if wrote_checksum == checksum:
											log.info("File has transferred successfully.")
											
										else:
											log.warn("File has failed to transfer, checksum mismatch (Transmitted: %s - Wrote: %s)." % (checksum, wrote_checksum))
										
									else:
										log.warn("There appears to be nothing in the data from %s." % packet[ddp.SECTION_SOURCE])
									
								else:
									log.warn("Unable to receive the message from %s as nothing was received." % packet[ddp.SECTION_SOURCE])
								
							else:
								log.warn("The packet received isn't valid for this program (%s)." % dd[0])
							
						else:
							log.warn("The start packet is invalid.")
						
					else:
						log.info("No packets have been received.")
					
				elif c == "tx":
					log.info("Enter the filename to send: ", newline = False)
					
					send = readInput().strip()
					log.info("")
					
					# Check the file path
					if os.path.exists(send):
						path, filename = os.path.split(send)
						size = os.path.getsize(send)
						
						log.info("Filename: %s" % filename)
						log.info("Size:     %d bytes" % size)
						
						if size >= 10240:
							log.warn("")
							log.warn("The file is greater than 10Kb, it may take a while to transfer (depending on backend/protocol used).")
						
						log.info("")
						log.info("Do you want to transfer this file? (Y/N): ", newline = False)
					
						answer = readInput().strip().upper()
						log.info("")
						
						if answer == "Y":
							f = open(send, "rb")
							data = f.read()
							
							f.close()
							
							log.info("Please wait, calculating file checksum...")
							checksum = ddp.sha1(data)
							
							log.info("Transmitting file (checksum %s)..." % checksum)
							
							# Transmit the file
							if ddp.transmitData(client_callsign, "", server_callsign, "FILE_TRANSFER\n%s\n%d\n%s" % (filename, size, checksum), USE_TCP):
								if ddp.transmitData(client_callsign, "", server_callsign, data, USE_TCP, 1):
									pass
									
								else:
									log.warn("File has not been transferred.")
								
							else:
								log.warn("Failed to send request.")
						
					else:
						log.warn("'%s' path doesn't exist." % send)
					
				else:
					log.info("Help: Type \"tx\" to transmit a file or \"rx\" to receive a file.")
			
		except KeyboardInterrupt:
			break
			
		except Exception, ex:
			log.fatal(ex)
	
	
	log.info("Cleaning up...")
	ddp.dispose()
	ddp = None
	
	log.info("Exiting...")
	sys.exit(0)

def readInput():
	return sys.stdin.readline().replace("\r", "").replace("\n", "")

def xmlFTSettingsRead():
	global ALLOW_UNSIGNED_PACKETS, BACKEND_DATAMODE, BACKEND_HOSTNAME, BACKEND_PORT, DEBUG_MODE, DISABLE_CRYPTO, SPECIFICATION, USE_TCP
	
	
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
					
				else:
					log.warn("XML setting attribute \"%s\" isn't known.  Ignoring..." % key)

def xmlFTSettingsWrite():
	if os.path.exists(XML_SETTINGS_FILE) == False:
		xmloutput = file(XML_SETTINGS_FILE, "w")
		
		
		xmldoc = minidom.Document()
		
		# Create header
		settings = xmldoc.createElement("IMChat")
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
		
		
		# Finally, save to the file
		xmloutput.write(xmldoc.toprettyxml())
		xmloutput.close()


########
# Main #
########
if __name__ == "__main__":
	main()

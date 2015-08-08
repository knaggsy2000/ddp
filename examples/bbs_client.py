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


#############
# Variables #
#############
client_callsign = ""

log = DanLog("BBSClient")

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

SEPERATOR = "#@#"
SPECIFICATION = 0

USE_TCP = 0

XML_SETTINGS_FILE = "bbsclient-settings.xml"


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
	global client_callsign, server_callsign
	
	
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
	log.info("Bulletin Board System - Client")
	log.info("==============================")
	log.info("Checking settings...")
	
	if os.path.exists(XML_SETTINGS_FILE) == False:
		log.warn("The XML settings file doesn't exist, create one...")
		
		xmlBBSSettingsWrite()
		
		
		log.info("The XML settings file has been created using the default settings.  Please edit it and restart the BBS client once you're happy with the settings.")
		
		exitProgram()
		
	else:
		log.info("Reading XML settings...")
		
		xmlBBSSettingsRead()
		
		# This will ensure it will have any new settings in
		if os.path.exists(XML_SETTINGS_FILE + ".bak"):
			os.unlink(XML_SETTINGS_FILE + ".bak")
			
		os.rename(XML_SETTINGS_FILE, XML_SETTINGS_FILE + ".bak")
		xmlBBSSettingsWrite()
	
	
	log.info("Setting up DDP...")
	ddp = DDP(hostname = BACKEND_HOSTNAME, port = BACKEND_PORT, data_mode = BACKEND_DATAMODE, timeout = 60., ack_timeout = 30., tx_hangtime = 1.25, data_length = 512, specification = SPECIFICATION, disable_ec = False, disable_crypto = DISABLE_CRYPTO, allow_unsigned_packets = ALLOW_UNSIGNED_PACKETS, application = "DDP Example: BBS", ignore_broadcast_packets = True, debug_mode = DEBUG_MODE)
	
	
	log.info("")
	log.info("Type ? for commands.")
	log.info("")
	
	while True:
		try:
			log.info("")
			log.info("BBS# ", newline = False)
			
			c = readInput().strip()
			cs = c.split(" ")
			
			log.info("")
			
			if cs[0] == "?":
				log.info("Help")
				log.info("====")
				log.info("c CALLSIGN    Connects to BBS server named CALLSIGN and retreives the messages")
				log.info("l             List messages on server")
				log.info("p             Post a message on the bulletin board")
				log.info("q             Quit the program")
				log.info("r N           Read message N from the list")
				
			elif cs[0] == "c" or cs[0] == "l":
				if len(cs) == 2:
					server_callsign = cs[1].strip().upper()
				
				
				if server_callsign == "":
					log.info("Please enter the BBS server callsign: ", newline = False)
					
					server_callsign = readInput().strip().upper()
					log.info("")
				
				if client_callsign == "":
					log.info("Please enter your callsign: ", newline = False)
					
					client_callsign = readInput().strip().upper()
					log.info("")
				
				
				if server_callsign <> "" and client_callsign <> "":
					ddp.setCallsign(client_callsign)
					
					
					log.info("")
					log.info("Requesting messages...")
					
					if ddp.transmitData(client_callsign, "", server_callsign, "VIEW MESSAGES", USE_TCP, 0):
						log.info("Receiving data...")
						data = ddp.receiveData(client_callsign, server_callsign)
						
						if data is not None:
							# Display the messages
							msg_id = "ID".rjust(6, " ")
							msg_subject = "Subject".ljust(50, " ")
							msg_from = "From".ljust(10, " ")
							msg_to = "To".ljust(10, " ")
							msg_date = "Date".ljust(19, " ")
							
							log.info("")
							log.info("%s %s %s %s %s" % (msg_id, msg_subject, msg_from, msg_to, msg_date))
							log.info("=" * 99)
							
							
							msgs = data[0].split("\n")
							
							for msg in msgs:
								if len(msg) > 0:
									line = msg.split(SEPERATOR)
									
									msg_id = line[0].rjust(6, " ")
									msg_subject = line[1][:49].ljust(50, " ")
									msg_from = line[2].ljust(10, " ")
									msg_to = line[3].ljust(10, " ")
									msg_date = line[4].ljust(19, " ")
									
									
									log.info("%s %s %s %s %s" % (msg_id, msg_subject, msg_from, msg_to, msg_date))
								
						else:
							log.warn("Nothing received.")
						
					else:
						log.warn("Failed to send request.")
					
				else:
					if server_callsign == "":
						log.warn("No BBS server callsign entered.")
						
					if client_callsign == "":
						log.warn("Your callsign hasn't been entered.")
				
			elif cs[0] == "p":
				to = ""
				subject = ""
				message = ""
				
				if server_callsign == "":
					log.info("Please enter the BBS server callsign: ", newline = False)
					
					server_callsign = readInput().strip().upper()
					log.info("")
				
				if client_callsign == "":
					log.info("Please enter your callsign: ", newline = False)
					
					client_callsign = readInput().strip().upper()
					log.info("")
				
				
				log.info("Please enter the to callsign: ", newline = False)
				
				to = readInput().strip().upper()
				log.info("")
				
				
				log.info("Please enter the subject: ", newline = False)
				
				subject = readInput().strip()
				log.info("")
				
				
				log.info("Please enter the message, just enter a \".\" and it's own line then press ENTER to end: ", newline = False)
				
				message = ""
				
				while True:
					m = readInput().strip()
					
					if m == ".":
						message = message[0:-1]
						break
						
					else:
						message += m + "\n"
				
				log.info("")
				
				
				log.info("")
				log.info("To:      %s" % to)
				log.info("Subject: %s" % subject)
				log.info("Message: %s" % message)
				
				log.info("")
				log.info("Do you want to post this message? (Y/N): ", newline = False)
				
				answer = readInput().strip().upper()
				log.info("")
				
				if answer == "Y":
					log.info("Posting message...")
					
					if ddp.transmitData(client_callsign, "", server_callsign, "POST MESSAGE", USE_TCP):
						tosend = "%s\n%s\n%s\n" % (to, subject, ddp.encodeStreamToBase128(message, 0, True))
						
						if ddp.transmitData(client_callsign, "", server_callsign, tosend, USE_TCP, 1):
							log.info("Message has been sent to the server.")
							
						else:
							log.warn("Message has NOT been sent to the server.")
						
					else:
						log.warn("Failed to send request.")
					
				else:
					log.warn("The message will not be sent.")
				
			elif cs[0] == "r":
				if server_callsign == "":
					log.info("Please enter the BBS server callsign: ", newline = False)
					
					server_callsign = readInput().strip().upper()
					log.info("")
				
				if client_callsign == "":
					log.info("Please enter your callsign: ", newline = False)
					
					client_callsign = readInput().strip().upper()
					log.info("")
					
				
				if server_callsign <> "" and client_callsign <> "":
					if len(cs) <= 1:
						log.warn("No message number defined.")
						
					else:
						if cs[1].isalpha() == False:
							log.info("Requesting message %d..." % int(cs[1]))
							
							if ddp.transmitData(client_callsign, "", server_callsign, "READ MESSAGE %d" % int(cs[1]), USE_TCP):
								log.info("Receiving data...")
								data = ddp.receiveData(client_callsign, server_callsign)
								
								if data is not None:
									if len(data[0]) > 0:
										# Display the requested message
										msgs = data[0].split("\n")
										
										for msg in msgs:
											if len(msg) > 0:
												line = msg.split(SEPERATOR)
												
												if len(line) == 6:
													log.info("ID:      %s" % line[0])
													log.info("From:    %s" % line[3])
													log.info("To:      %s" % line[4])
													log.info("Posted:  %s" % line[5])
													log.info("Subject: %s" % line[1])
													log.info("Message: %s" % ddp.decodeBase128ToStream(line[2], 0, True))
													
												else:
													log.warn("There doesn't appear to be a complete message here.")
										
									else:
										log.warn("Nothing received.")
									
								else:
									log.warn("Nothing received.")
								
							else:
								log.warn("Failed to send request.")
							
						else:
							log.warn("You haven't entered a number for the message number.")
				
			elif cs[0] == "q":
				break
			
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

def xmlBBSSettingsRead():
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

def xmlBBSSettingsWrite():
	if os.path.exists(XML_SETTINGS_FILE) == False:
		xmloutput = file(XML_SETTINGS_FILE, "w")
		
		
		xmldoc = minidom.Document()
		
		# Create header
		settings = xmldoc.createElement("BBSClient")
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

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
from datetime import *
from ddp import *
import os
import sys
from xml.dom import minidom


###########
# Globals #
###########
log = DanLog("FaxReceive")


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

XML_SETTINGS_FILE = "faxreceive-settings.xml"


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
	log.info("Receive Fax")
	log.info("===========")
	log.info("Checking settings...")
	
	if os.path.exists(XML_SETTINGS_FILE) == False:
		log.warn("The XML settings file doesn't exist, create one...")
		
		xmlFAXSettingsWrite()
		
		
		log.info("The XML settings file has been created using the default settings.  Please edit it and restart receive fax once you're happy with the settings.")
		
		exitProgram()
		
	else:
		log.info("Reading XML settings...")
		
		xmlFAXSettingsRead()
		
		# This will ensure it will have any new settings in
		if os.path.exists(XML_SETTINGS_FILE + ".bak"):
			os.unlink(XML_SETTINGS_FILE + ".bak")
			
		os.rename(XML_SETTINGS_FILE, XML_SETTINGS_FILE + ".bak")
		xmlFAXSettingsWrite()
	
	
	log.info("Checking for PNG library...")
	
	pngio = None
	
	if os.path.exists("pypng"):
		sys.path.append("pypng")
		
		
		import png
		
		pngio = png
		
	else:
		log.fatal("PyPNG is not present in the \"pypng\" folder, only the \"png.py\" is needed in the directory.")
		
		exitProgram()
	
	
	log.info("Setting up DDP...")
	ddp = DDP(hostname = BACKEND_HOSTNAME, port = BACKEND_PORT, data_mode = BACKEND_DATAMODE, timeout = 60., ack_timeout = 30., tx_hangtime = 0.25, data_length = 1024, specification = SPECIFICATION, disable_crypto = DISABLE_CRYPTO, disable_ec = False, allow_unsigned_packets = ALLOW_UNSIGNED_PACKETS, application = "DDP Example: Fax", ignore_broadcast_packets = True, debug_mode = DEBUG_MODE)
	
	
	while True:
		try:
			log.info("Receiving fax...")
			
			raw_lines = {}
			
			
			# Main rx loop
			while True:
				data = ddp.receiveDataFromAny("FAX")
				
				if data is not None:
					# Check the flags
					d = data[0]
					packet = data[1]
					
					
					if d == "END":
						# Fax ended, save what we've got already
						log.info("End of fax received.")
						
						break
						
					else:
						line_no = int(ddp.decodeBaseToNumber(d[0:2]))
						
						
						log.info("Fax line number %d received." % line_no)
						
						raw_lines[line_no] = d[2::]
			
			
			# Write the file out
			if len(raw_lines) > 0:
				t = datetime.now()
				rxfile = str(t.strftime("%d%m%Y%H%M%S")) + ".png"
				
				width = 0
				height = 0
				
				# Work out the size of the image from the data
				log.info("Calculating image size...")
				
				for line in raw_lines.keys():
					if len(raw_lines[line]) > width:
						width = len(raw_lines[line])
					
					if line > height:
						height = line
				
				
				
				log.info("Image size appears to be %dx%d." % (width, height))
				
				if width > 0 and height > 0:
					log.info("Filling in any missing rows...")
					
					for x in xrange(1, height + 1):
						if not x in raw_lines.keys():
							raw_lines[x] = [chr(0)] * width
					
					
					log.info("Writing PNG as \"%s\"..." % rxfile)
					
					pngout = pngio.Writer(size = (width, height), bitdepth = 8, greyscale = True, alpha = False)
					
					with open(rxfile, "wb") as rx:
						l = []
						
						for x in xrange(1, height + 1):
							line = raw_lines[x]
							
							for y in line:
								l.append(ord(y))
						
						pngout.write_array(rx, l)
						
						rx.flush()
						rx.close()
						rx = None
						
					pngout = None
					
				else:
					log.warn("Image size appears to be invalid, cannot write file.")
			
		except KeyboardInterrupt:
			break
			
		except Exception, ex:
			log.fatal(ex)
			break
	
	
	log.info("Cleaning up...")
	ddp.dispose()
	ddp = None
	
	log.info("Exiting...")
	exitProgram()

def readInput():
	return sys.stdin.readline().replace("\r", "").replace("\n", "")

def xmlFAXSettingsRead():
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

def xmlFAXSettingsWrite():
	if os.path.exists(XML_SETTINGS_FILE) == False:
		xmloutput = file(XML_SETTINGS_FILE, "w")
		
		
		xmldoc = minidom.Document()
		
		# Create header
		settings = xmldoc.createElement("BBSServer")
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


##########################
#  Main
##########################
if __name__ == "__main__":
	main()

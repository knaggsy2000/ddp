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
import threading
import time
from xml.dom import minidom


###########
# Globals #
###########
log = DanLog("Repeater")


#############
# Constants #
#############
CW_BEACON_TEXT = "CHANGEME"

DEBUG_MODE = False
DISABLE_CRYPTO = False

REPEATER_CALLSIGN = "CHANGEME"

RIG1_BACKEND_DATAMODE = "PSK500R"
RIG2_BACKEND_DATAMODE = "PSK500R"
RIG1_BACKEND_HOSTNAME = "localhost"
RIG2_BACKEND_HOSTNAME = "localhost"
RIG1_BACKEND_PORT = 7362
RIG2_BACKEND_PORT = 7362
RIG1_SPECIFICATION = 0
RIG2_SPECIFICATION = 0
RIG1_USE_TCP = 0
RIG2_USE_TCP = 0

XML_SETTINGS_FILE = "repeater-settings.xml"


###########
# Classes #
###########
class Rig():
	def __init__(self, id, hostname = "localhost", port = 7362, data_mode = "PSK500R", carrier_frequency = 1000, sideband = "USB", retries = 3, data_length = 128, tx_wait = 0.5, rx_wait = 0.1, timeout = 10., ack_timeout = 0.25, tx_hangtime = 0.25, specification = 0, extension_init = None, disable_ec = False, disable_crypto = True, allow_unsigned_packets = True, application = "DDP Example: Repeater", ignore_broadcast_packets = True, repeater_mode = True, debug_mode = False):
		self.DEBUG_MODE = debug_mode
		self.ID = int(id)
		
		self.ddp = DDP(hostname, port, data_mode, carrier_frequency, sideband, retries, data_length, tx_wait, rx_wait, timeout, ack_timeout, tx_hangtime, specification, extension_init, disable_ec, disable_crypto, allow_unsigned_packets, application, ignore_broadcast_packets, repeater_mode, debug_mode)
		self.linked_rig = None
		self.main_thread = None
		self.run_queue = True
		
		
		self.log = DanLog("RIG%d" % self.ID)
		self.log.info("Initialising...")
	
	def dispose(self):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		self.ddp.dispose()
	
	def mainLoop(self):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		while self.run_queue:
			packet = self.receivePacket(120.)
			
			if packet is not None:
				# Reconstruct the packet so it can be transmitted to the linked rig
				lr_ddp = self.linked_rig.ddp
				recon = lr_ddp.constructPacket(packet[lr_ddp.SECTION_SOURCE], REPEATER_CALLSIGN, packet[lr_ddp.SECTION_DESTINATION], packet[lr_ddp.SECTION_FLAGS], self.ddp.decodeData(packet[lr_ddp.SECTION_DATA], packet[lr_ddp.SECTION_FLAGS]), packet[lr_ddp.SECTION_APPLICATION_ID], packet[lr_ddp.SECTION_SIGNATURE])
				
				# Re-transmit the packet
				self.transmitPacket(recon)
	
	def receivePacket(self, timeout = 60.):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		return self.ddp.receivePacket(timeout)
	
	def setCallsign(self, callsign):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		self.ddp.setCallsign(callsign)
	
	def setLinkedRig(self, rig):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		self.linked_rig = rig
	
	def start(self):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		self.run_queue = True
		
		self.main_thread = threading.Thread(target = self.mainLoop)
		self.main_thread.setDaemon(1)
		self.main_thread.start()
	
	def stop(self):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		self.run_queue = False
	
	def transmitPacket(self, packet):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		self.ddp.transmitRawPacket(packet)


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
	log.info("DDP Repeater")
	log.info("============")
	log.info("Checking settings...")
	
	if os.path.exists(XML_SETTINGS_FILE) == False:
		log.warn("The XML settings file doesn't exist, create one...")
		
		xmlRPTSettingsWrite()
		
		
		log.info("The XML settings file has been created using the default settings.  Please edit it and restart the repeater once you're happy with the settings.")
		
		exitProgram()
		
	else:
		log.info("Reading XML settings...")
		
		xmlRPTSettingsRead()
		
		# This will ensure it will have any new settings in
		if os.path.exists(XML_SETTINGS_FILE + ".bak"):
			os.unlink(XML_SETTINGS_FILE + ".bak")
			
		os.rename(XML_SETTINGS_FILE, XML_SETTINGS_FILE + ".bak")
		xmlRPTSettingsWrite()
	
	
	log.info("Checking the config...")
	
	if REPEATER_CALLSIGN == "" or REPEATER_CALLSIGN == "CHANGEME":
		log.error("The repeater callsign is invalid.  Please edit the config XML file.")
		exitProgram()
	
	
	log.info("Setting up rigs...")
	rig1 = Rig(1, hostname = RIG1_BACKEND_HOSTNAME, port = RIG1_BACKEND_PORT, data_mode = RIG1_BACKEND_DATAMODE, timeout = 120., ack_timeout = 60., tx_hangtime = 1.25, data_length = 512, specification = RIG1_SPECIFICATION, disable_ec = False, disable_crypto = True, allow_unsigned_packets = True, application = "DDP Example: Repeater", ignore_broadcast_packets = True, repeater_mode = True, debug_mode = DEBUG_MODE)
	rig2 = Rig(2, hostname = RIG2_BACKEND_HOSTNAME, port = RIG2_BACKEND_PORT, data_mode = RIG2_BACKEND_DATAMODE, timeout = 120., ack_timeout = 60., tx_hangtime = 1.25, data_length = 512, specification = RIG2_SPECIFICATION, disable_ec = False, disable_crypto = True, allow_unsigned_packets = True, application = "DDP Example: Repeater", ignore_broadcast_packets = True, repeater_mode = True, debug_mode = DEBUG_MODE)
	
	rig1.setCallsign(REPEATER_CALLSIGN)
	rig2.setCallsign(REPEATER_CALLSIGN)
	
	rig1.setLinkedRig(rig2)
	rig2.setLinkedRig(rig1)
	
	
	log.info("Starting threads...")
	
	rig1.start()
	rig2.start()
	
	
	log.info("Threads started, repeater should now be active.")
	
	while True:
		try:
			r = readInput()
			
			if r == "inject":
				# Inject a packet into rig1
				flags = Bits()
				flags.set(rig2.ddp.FLAG_SYN, 1)
				flags.set(rig2.ddp.FLAG_COMPRESSION, 0)
				flags.set(rig2.ddp.FLAG_TCP, 0)
				
				packet = rig2.ddp.constructPacket("FROM", REPEATER_CALLSIGN, "TO", flags, "Injected")
				
				rig1.transmitPacket(packet)
			
			
			time.sleep(0.1)
			
		except KeyboardInterrupt:
			break
			
		except Exception, ex:
			log.fatal(ex)
	
	
	log.info("Cleaning up...")
	rig1.dispose()
	rig2.dispose()
	
	rig1 = None
	rig2 = None
	
	log.info("Exiting...")
	exitProgram()

def readInput():
	return sys.stdin.readline().replace("\r", "").replace("\n", "")

def xmlRPTSettingsRead():
	global CW_BEACON_TEXT, DEBUG_MODE, REPEATER_CALLSIGN
	global RIG1_BACKEND_DATAMODE, RIG1_BACKEND_HOSTNAME, RIG1_BACKEND_PORT, RIG1_SPECIFICATION, RIG1_USE_TCP
	global RIG2_BACKEND_DATAMODE, RIG2_BACKEND_HOSTNAME, RIG2_BACKEND_PORT, RIG2_SPECIFICATION, RIG2_USE_TCP
	
	
	if os.path.exists(XML_SETTINGS_FILE):
		xmldoc = minidom.parse(XML_SETTINGS_FILE)
		
		myvars = xmldoc.getElementsByTagName("Setting")
		
		for var in myvars:
			for key in var.attributes.keys():
				val = str(var.attributes[key].value)
				
				# Now put the correct values to correct key
				if key == "RepeaterCallsign":
					REPEATER_CALLSIGN = val
					
				elif key == "CWBeaconText":
					CW_BEACON_TEXT = val.upper()
					
				elif key == "DebugMode":
					DEBUG_MODE = cBool(val)
					
				elif key == "Rig1BackendDataMode":
					RIG1_BACKEND_DATAMODE = val.upper()
					
				elif key == "Rig1BackendHostname":
					RIG1_BACKEND_HOSTNAME = val
					
				elif key == "Rig1BackendPort":
					RIG1_BACKEND_PORT = val.upper()
					
				elif key == "Rig1Specification":
					RIG1_SPECIFICATION = int(val)
					
				elif key == "Rig1UseTCP":
					RIG1_USE_TCP = int(val)
					
				elif key == "Rig2BackendDataMode":
					RIG2_BACKEND_DATAMODE = val.upper()
					
				elif key == "Rig2BackendHostname":
					RIG2_BACKEND_HOSTNAME = val
					
				elif key == "Rig2BackendPort":
					RIG2_BACKEND_PORT = val.upper()
					
				elif key == "Rig2Specification":
					RIG2_SPECIFICATION = int(val)
					
				elif key == "Rig2UseTCP":
					RIG2_USE_TCP = int(val)
					
				else:
					log.warn("XML setting attribute \"%s\" isn't known.  Ignoring..." % key)

def xmlRPTSettingsWrite():
	if os.path.exists(XML_SETTINGS_FILE) == False:
		xmloutput = file(XML_SETTINGS_FILE, "w")
		
		
		xmldoc = minidom.Document()
		
		# Create header
		settings = xmldoc.createElement("Repeater")
		xmldoc.appendChild(settings)
		
		# Write each of the details one at a time, makes it easier for someone to alter the file using a text editor
		var = xmldoc.createElement("Setting")
		var.setAttribute("RepeaterCallsign", str(REPEATER_CALLSIGN))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("CWBeaconText", str(CW_BEACON_TEXT))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("DebugMode", str(DEBUG_MODE))
		settings.appendChild(var)
		
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("Rig1BackendDataMode", str(RIG1_BACKEND_DATAMODE))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("Rig1BackendHostname", str(RIG1_BACKEND_HOSTNAME))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("Rig1BackendPort", str(RIG1_BACKEND_PORT))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("Rig1Specification", str(RIG1_SPECIFICATION))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("Rig1UseTCP", str(RIG1_USE_TCP))
		settings.appendChild(var)
		
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("Rig2BackendDataMode", str(RIG2_BACKEND_DATAMODE))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("Rig2BackendHostname", str(RIG2_BACKEND_HOSTNAME))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("Rig2BackendPort", str(RIG2_BACKEND_PORT))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("Rig2Specification", str(RIG2_SPECIFICATION))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("Rig2UseTCP", str(RIG2_USE_TCP))
		settings.appendChild(var)
		
		
		
		
		# Finally, save to the file
		xmloutput.write(xmldoc.toprettyxml())
		xmloutput.close()


##########################
#  Main
##########################
if __name__ == "__main__":
	main()

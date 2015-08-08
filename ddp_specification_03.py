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


###################################################
# Danny's Digital Packet                          #
# Danny's Data Packet                             #
# Danny's DDP Project                             #
###################################################
# Specification ID:      3                        #
# Specification Name:    SMS (Binary)             #
###################################################


def constructPacket(self, callsign_from, via, callsign_to, flags, data, application_id, signature):
	tx = bytearray()
	
	p1 = bytearray()
	p2 = bytearray()
	
	p1.extend(self.PROTOCOL_HEADER)
	p1.extend(self.SECTION_SEPERATOR)
	p1.extend(self.PROTOCOL_VERSION)
	p1.extend(self.SECTION_SEPERATOR)
	
	p2.extend(callsign_from)
	p2.extend(self.SECTION_SEPERATOR)
	p2.extend(callsign_to)
	p2.extend(self.SECTION_SEPERATOR)
	p2.extend(str(hex(int(str(flags), 2))).replace("0x", ""))
	p2.extend(self.SECTION_SEPERATOR)
	p2.extend(self.encodeData(data, str(flags)))
	
	
	signature = ""
	checksum = self.xorChecksum(str(p2))
	
	tx.extend(str(p1))
	tx.extend(str(p2))
	tx.extend(self.SECTION_SEPERATOR)
	tx.extend(checksum)
	tx.extend(self.SECTION_SEPERATOR)
	tx.extend(self.PROTOCOL_FOOTER)
	
	
	# Now we need apply the extra rules to the packet e.g. scrambling, reed-solomon, etc
	if self.DEBUG_MODE:
		self.log.info("Constructed: %s" % repr(str(tx)))
		self.log.info("Applying rules to packet...")
	
	
	d = str(tx)
	tx2 = bytearray()
	
	if self.fldigi is not None:
		tx2.extend(d)
		
		tx2.extend("\n")
		tx2.extend("^r")
		
	else:
		tx2.extend(d)
	
	
	if self.DEBUG_MODE:
		a = float(len(str(tx)))
		b = float(len(str(tx2)))
		c = ((b - a) / a) * 100.
		
		self.log.info("Original packet size %d bytes, including overhead %d bytes - %.2f%% increase." % (a, b, c))
	
	return str(tx2)

def decodeData(self, data, flags):
	f = str(flags)[::-1]
	
	din = self.decodeBase128ToStream(str(data), 0, True)
	din = self.descramble(din)
	
	return din

def encodeData(self, data, flags):
	din = str(data)
	din = self.scramble(din)
	
	return self.encodeStreamToBase128(din, 0, True)

def init(self):
	self.SECTION_HEADER = 0
	self.SECTION_VERSION = 1
	self.SECTION_SOURCE = 2
	self.SECTION_DESTINATION = 3
	self.SECTION_FLAGS = 4
	self.SECTION_DATA = 5
	self.SECTION_CHECKSUM = 6
	self.SECTION_FOOTER = 7
	
	self.MAX_SECTIONS = 8
	
	
	self.log.info("Running in SMS (hex encoded) mode.")

def isCompressionAllowed(self):
	return False

def parsePacket(self, packet):
	return packet

def splitPacket(self, packet):
	return str(packet).split(self.SECTION_SEPERATOR)

def verifyPacket(self, packet):
	plen = len(packet)
	
	
	# Check the number of sections
	if plen == self.MAX_SECTIONS:
		# Check the header
		if packet[self.SECTION_HEADER] == self.PROTOCOL_HEADER:
			# Check the version number (must be exact versions for now)
			if packet[self.SECTION_VERSION] == self.PROTOCOL_VERSION:
				# Check the checksum
				verify = packet[self.SECTION_SOURCE] + self.SECTION_SEPERATOR + packet[self.SECTION_DESTINATION] + self.SECTION_SEPERATOR + packet[self.SECTION_FLAGS] + self.SECTION_SEPERATOR + packet[self.SECTION_DATA]
				checksum = self.xorChecksum(verify)
				
				
				# Convert the flags to old-style
				packet[self.SECTION_FLAGS] = bin(int(packet[self.SECTION_FLAGS], 16)).replace("0b", "").rjust(16, "0")
				
				
				if checksum == packet[self.SECTION_CHECKSUM]:
					
					# Application ID
					if self.REPEATER_MODE:
						# Set the application ID to the one we are verifying
						self.APPLICATION_ID = packet[self.SECTION_APPLICATION_ID]
					
					return True
					
				else:
					if self.DEBUG_MODE:
						self.log.warn("Checksum mismatch (%s != %s)." % (checksum, packet[self.SECTION_CHECKSUM]))
				
			else:
				if self.DEBUG_MODE:
					self.log.warn("Version number mismatch (%s != %s)." % (self.PROTOCOL_VERSION, packet[self.SECTION_VERSION]))
			
		else:
			if self.DEBUG_MODE:
				self.log.warn("Invalid header (%s != %s)." % (self.PROTOCOL_HEADER, packet[self.SECTION_HEADER]))
		
	else:
		if self.DEBUG_MODE:
			self.log.warn("Wrong number of sections (%d != %d)." % (plen, self.MAX_SECTIONS))
	
	return False

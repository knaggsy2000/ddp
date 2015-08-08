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
# Specification ID:      1                        #
# Specification Name:    8-bit                    #
###################################################


from ddp import DanRSA

import os


def constructPacket(self, callsign_from, via, callsign_to, flags, data, application_id, signature):
	tx = bytearray()
	
	p1 = bytearray()
	p2 = bytearray()
	
	p1.extend(self.PROTOCOL_HEADER)
	p1.extend(self.PROTOCOL_VERSION)
	p2.extend(callsign_from.ljust(10, "\x00"))
	p2.extend(via.ljust(10, "\x00"))
	p2.extend(callsign_to.ljust(10, "\x00"))
	p2.extend(self.encodeNumberToBase(int(str(flags), 2)).rjust(2, "\x00"))
	p2.extend(self.encodeNumberToBase(int(application_id, 16)).rjust(20, "\x00"))
	p2.extend(self.encodeNumberToBase(int(self.generatePacketID(), 16)).rjust(20, "\x00"))
	p2.extend(self.encodeData(data, str(flags)))
	
	if self.CRYPTO_AVAILABLE and signature == "":
		if self.DEBUG_MODE:
			self.log.info("Signature generation is required.")
		
		signature = self.crypto.signMessage(str(p2))
	
	p2.extend(signature.ljust(64, "\x00"))
	
	
	# Build the packet
	tx.extend(str(p1))
	tx.extend(str(p2))
	tx.extend(self.encodeNumberToBase(int(self.sha1(str(p2)), 16)).rjust(20, "\x00"))
	tx.extend(self.PROTOCOL_FOOTER)
	
	
	# Now we need apply the extra rules to the packet e.g. scrambling, reed-solomon, etc
	if self.DEBUG_MODE:
		self.log.info("Constructed: %s" % repr(str(tx)))
		self.log.info("Applying rules to packet...")
	
	
	d = str(tx)
	tx2 = bytearray()
	
	if self.fldigi is not None:
		# Can't send 8-bit character set to fldigi, so we'll have to hex-encode it instead
		tx2.extend(self.PROTOCOL_HEADER)
		tx2.extend(self.encodeStreamToBase128(self.scramble(d), 0, True))
		tx2.extend(self.PROTOCOL_FOOTER)
		
		tx2.extend("\n")
		tx2.extend("^r")
		
	else:
		tx2.extend(self.PROTOCOL_PREAMPLE)
		tx2.extend(self.PROTOCOL_HEADER)
		
		if self.EC_AVAILABLE:
			d = self.encodeReedSolomon(d)
			d = self.interleave(d)
		
		tx2.extend(self.scramble(d))
		tx2.extend(self.PROTOCOL_FOOTER)
		tx2.extend(self.PROTOCOL_PREAMPLE)
	
	
	if self.DEBUG_MODE:
		a = float(len(str(tx)))
		b = float(len(str(tx2)))
		c = ((b - a) / a) * 100.
		
		self.log.info("Original packet size %d bytes, including overhead %d bytes - %.2f%% increase." % (a, b, c))
	
	return str(tx2)

def decodeData(self, data, flags):
	f = str(flags)[::-1]
	
	din = str(data)
	
	
	if int(f[self.FLAG_COMPRESSION]) == 1:
		return self.decompressStream(din)
		
	else:
		return din

def encodeData(self, data, flags):
	din = None
	f = str(flags)[::-1]
	
	if int(f[self.FLAG_COMPRESSION]) == 1:
		din = self.compressStream(str(data))
		
	else:
		din = str(data)
	
	
	return din

def init(self):
	if self.BACKEND == "FLDIGI":
		self.log.warn("Using the 8-bit specification with fldigi is not recommended due to additional overhead.  Use the 7-bit specification instead with a robust digital mode like PSK500R.")
	
	self.log.info("Running in 8-bit binary mode.")

def isCompressionAllowed(self):
	return True

def parsePacket(self, packet):
	data = None
	
	if self.fldigi is not None:
		data = self.decodeBase128ToStream(str(packet).replace(self.PROTOCOL_HEADER, "").replace(self.PROTOCOL_FOOTER, ""), 0, True)
		data = self.descramble(data)
		
	elif self.serial is not None or self.fdmdv is not None:
		data = str(packet).replace(self.PROTOCOL_HEADER, "").replace(self.PROTOCOL_FOOTER, "")
		data = self.descramble(data)
		
		if self.EC_AVAILABLE:
			data = self.deinterleave(data)
			data = self.decodeReedSolomon(data)
	
	
	# Find the packet within the "packet"
	x = data.rfind(self.PROTOCOL_HEADER)
	
	if x <> -1:
		y = data.rfind(self.PROTOCOL_FOOTER, x + len(self.PROTOCOL_HEADER))
		
		if y <> -1:
			y += len(self.PROTOCOL_FOOTER)
			
			return str(data[x:y])
			
		else:
			if self.DEBUG_MODE:
				self.log.warn("Packet received is incomplete, this should not happen (1).")
			
			return None
		
	else:
		if self.DEBUG_MODE:
			self.log.warn("Packet received is incomplete, this should not happen (2).")
		
		return None

def splitPacket(self, packet):
	if self.DEBUG_MODE:
		self.log.info("Running...")
	
	
	plen = len(packet)
	
	if plen >= 80:
		# We need to validate the checksum here while we've got the raw packet
		checksum = bytearray()
		
		checksum.extend(packet[10:20]) # Source callsign
		checksum.extend(packet[20:30]) # Via
		checksum.extend(packet[30:40]) # Destination callsign
		checksum.extend(packet[40:42]) # Flags
		checksum.extend(packet[42:62]) # Application ID
		checksum.extend(packet[62:82]) # Packet ID
		checksum.extend(packet[82:plen - 26]) # Data (excluding the checksum of course)
		
		if self.encodeNumberToBase(int(self.sha1(str(checksum)), 16)).rjust(20, "\x00") == packet[plen - 26:plen - 6]:
			# OK, build a "old-style" list to keep compatibility
			ret = []
			ret.append(packet[0:6]) # Header
			ret.append(packet[6:10]) # Version
			ret.append(packet[10:20].replace("\x00", "")) # Source callsign
			ret.append(packet[20:30].replace("\x00", "")) # Via
			ret.append(packet[30:40].replace("\x00", "")) # Destination callsign
			ret.append(bin(self.decodeBaseToNumber(packet[40:42])).replace("0b", "").rjust(16, "0")) # Flags
			ret.append(str(hex(self.decodeBaseToNumber(packet[42:62]))).replace("0x", "").replace("L", "")) # Application ID
			ret.append(str(hex(self.decodeBaseToNumber(packet[62:82]))).replace("0x", "").replace("L", "")) # Packet ID
			ret.append(packet[82:plen - 90]) # Data
			ret.append(packet[plen - 90:plen - 26]) # Signature
			ret.append(self.sha1(str(self.decodeBaseToNumber(packet[plen - 26:plen - 6])))) # Checksum
			ret.append(packet[plen - 6:plen]) # Footer
			
			
			if self.CRYPTO_AVAILABLE:
				# Check the callsign signature
				verify = bytearray()
				verify.extend(packet[10:20]) # Source callsign
				verify.extend(packet[20:30]) # Via
				verify.extend(packet[30:40]) # Destination callsign
				verify.extend(packet[40:42]) # Flags
				verify.extend(packet[42:62]) # Application ID
				verify.extend(packet[62:82]) # Packet ID
				verify.extend(packet[82:plen - 90]) # Data
				
				
				if len(str(ret[self.SECTION_SIGNATURE]).replace("\x00", "")) > 0:
					client_key = os.path.join(self.CRYPTO_REMOTE_DIRECTORY, "%s.key" % self.sha1(ret[self.SECTION_SOURCE]))
					
					if os.path.exists(client_key):
						if self.DEBUG_MODE:
							self.log.info("Verifying the packet using the public key for %s..." % ret[self.SECTION_SOURCE])
						
						
						test = DanRSA(client_key, None, None)
						result = test.verifyMessage(str(verify), ret[self.SECTION_SIGNATURE])
						test = None
						
						if result:
							if self.DEBUG_MODE:
								self.log.info("The signature has validated using the public key for %s." % ret[self.SECTION_SOURCE])
							
						else:
							if self.DEBUG_MODE:
								self.log.warn("The signature did NOT validate using the public key for %s." % ret[self.SECTION_SOURCE])
						
						return ret
						
					else:
						if self.DEBUG_MODE:
							self.log.warn("We do not have the public key for %s (%s.key), cannot verify the packet." % (ret[self.SECTION_SOURCE], self.sha1(ret[self.SECTION_SOURCE])))
						
						
						if self.CRYPTO_ALLOW_UNSIGNED_PACKETS:
							return ret
							
						else:
							return None
					
				else:
					if self.DEBUG_MODE:
						self.log.warn("Packet contained no signature.")
					
					
					if self.CRYPTO_ALLOW_UNSIGNED_PACKETS:
						return ret
						
					else:
						return None
				
			else:
				if self.DEBUG_MODE:
					self.log.warn("Crypto isn't available so we can't validate the signature.")
				
				
				if self.CRYPTO_ALLOW_UNSIGNED_PACKETS:
					return ret
					
				else:
					return None
			
		else:
			if self.DEBUG_MODE:
				self.log.warn("Packet checksum mismatch.")
			
			return None
		
	else:
		if self.DEBUG_MODE:
			self.log.warn("Packet length mismatch (%d != %d)." % (plen, 68))
		
		return None

def verifyPacket(self, packet):
	plen = len(packet)
	
	# Packet length
	if plen == self.MAX_SECTIONS:
		# Check the header
		if packet[self.SECTION_HEADER] == self.PROTOCOL_HEADER:
			# Check the version number (must be exact versions for now)
			if packet[self.SECTION_VERSION] == self.PROTOCOL_VERSION:
				
				# Application ID
				if self.REPEATER_MODE:
					# Set the application ID to the one we are verifying
					self.APPLICATION_ID = packet[self.SECTION_APPLICATION_ID]
				
				if packet[self.SECTION_APPLICATION_ID] == self.APPLICATION_ID:
					# Packet replay detection
					if not packet[self.SECTION_PACKET_ID] in self.prd:
						if self.DEBUG_MODE:
							self.log.info("Packet ID %s not present in PRD database, adding it in." % packet[self.SECTION_PACKET_ID])
						
						self.prd[packet[self.SECTION_PACKET_ID]] = packet[self.SECTION_SOURCE]
						
						
						# NOTE: The checksum and the callsign signature have already been checked in splitPacket()
						return True
						
					else:
						if self.DEBUG_MODE:
							self.log.warn("Packet replay detected by %s." % self.prd[packet[self.SECTION_PACKET_ID]])
					
				else:
					if self.DEBUG_MODE:
						self.log.warn("The packet received application ID (%s) isn't for this application." % packet[self.SECTION_APPLICATION_ID])
				
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

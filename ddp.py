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
# =============================================== #
# DDP over D-STAR                                 #
# DDPoD                                           #
# DPoD                                            #
# =============================================== #
# DDP over RS-232                                 #
# DDPoR                                           #
# DPoR                                            #
###################################################
# Version:     v0.6.1                             #
###################################################


from datetime import datetime
from StringIO import StringIO

import hashlib
import math
import os
import random
import subprocess
import sys
import threading
import time
import xmlrpclib


###########
# Classes #
###########
class Bits():
	def __init__(self, bits = 16):
		self.bit = {}
		
		if bits < 1:
			bits = 16
		
		for x in xrange(0, bits):
			self.bit[x] = 0
			
	
	def __str__(self):
		s = ""
		
		for x in self.bit.values():
			s += str(x)
		
		return s[::-1]
	
	def get(self, bit):
		return self.bit[bit]
	
	def set(self, bit, value):
		self.bit[bit] = value

class DanRSA():
	def __init__(self, publickey = None, privatekey = None, passphrasecallback = "password"):
		import M2Crypto
		
		
		self.m2crypto = M2Crypto
		self.passphrase_callback = passphrasecallback
		self.public_key = None
		self.public_key_file = publickey
		self.private_key = None
		self.private_key_file = privatekey
		
		if self.public_key_file <> None:
			self.public_key = self.m2crypto.RSA.load_pub_key(self.public_key_file)
		
		if self.private_key_file <> None:
			self.private_key = self.m2crypto.RSA.load_key(self.private_key_file, callback = self.passphraseCallback)
		
		
		if self.public_key_file <> None:
			self.MAX_DATA_LENGTH = self.maximumDataLength()
			
		else:
			self.MAX_DATA_LENGTH = 0
	
	def decrypt(self, bytesin):
		dec = self.private_key.private_decrypt(bytesin, self.m2crypto.RSA.pkcs1_padding)
		
		return dec
	
	def encrypt(self, bytesin):
		enc = self.public_key.public_encrypt(bytesin, self.m2crypto.RSA.pkcs1_padding)
		
		return enc
	
	def generateKeyPair(self, publickey, privatekey, bits = 512):
		rsa = self.m2crypto.RSA.gen_key(bits, self.m2crypto.m2.RSA_F4)
		rsa.save_pub_key(publickey)
		rsa.save_key(privatekey, cipher = "aes_256_cbc", callback = self.passphraseCallback)
		rsa = None
	
	def generatePassphrase(self, length = 128):
		pwd = bytearray()
		
		for x in xrange(0, length):
			pwd.append(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"))
		
		return str(pwd)
	
	def loadPassphrase(self, passphrasefile):
		f = open(passphrasefile, "r")
		
		r = f.readline()
		f.close()
		
		return r
	
	def maximumDataLength(self):
		length = 1
		
		try:
			for x in xrange(0, 8192):
				self.encrypt("a" * length)
				
				length += 1
			
			return 8192
			
		except self.m2crypto.RSA.RSAError, ex:
			return length - 1
	
	def passphraseCallback(self, v):
		return self.passphrase_callback
	
	def savePassphrase(self, passphrasefile, passphrase):
		f = open(passphrasefile, "w")
		
		f.write(passphrase)
		f.close()
	
	def signMessage(self, message):
		evp = self.m2crypto.EVP.load_key(self.private_key_file, callback = self.passphraseCallback)
		evp.sign_init()
		evp.sign_update(message)
		
		return evp.sign_final()
		
	def verifyMessage(self, message, signature):
		evp = self.m2crypto.EVP.PKey()
		evp.assign_rsa(self.public_key)
		evp.verify_init()
		evp.verify_update(message)
		
		return evp.verify_final(signature)

class DDP():
	def __init__(self, hostname = "localhost", port = 7362, data_mode = "PSK500R", carrier_frequency = 1000, sideband = "USB", retries = 5, data_length = 128, tx_wait = 0.15, rx_wait = 0.15, timeout = 30., ack_timeout = 15., tx_hangtime = 0.25, specification = 0, extension_init = None, disable_ec = False, disable_crypto = False, allow_unsigned_packets = False, application = "DDP", ignore_broadcast_packets = True, verify_packet_before_tx = True, repeater_mode = False, colour_logging = True, logger_name = "DDP", debug_mode = False):
		self.compressor = None
		self.crypto = None
		self.devnull = None
		self.fdmdv = None
		self.fldigi = None
		self.prd = {}
		self.reedsolomon = None
		self.serial = None
		
		self.ACK_TIMEOUT = ack_timeout
		self.APPLICATION_ID = ""
		self.BACKEND = ""
		self.BROADCAST_CALLSIGN = "BROADCAST"
		self.CALLSIGN = ""
		self.CARRIER_FREQUENCY = carrier_frequency
		self.COLOUR_LOGGING = colour_logging
		self.CRYPTO_ALLOW_UNSIGNED_PACKETS = allow_unsigned_packets
		self.CRYPTO_AVAILABLE = False
		self.CRYPTO_DIRECTORY = "keys"
		self.CRYPTO_DISABLED = disable_crypto
		self.CRYPTO_LOCAL_DIRECTORY = ""
		self.CRYPTO_LOCAL_NAME = "local"
		self.CRYPTO_PASSPHRASE = ""
		self.CRYPTO_PASSPHRASE_FILE = ""
		self.CRYPTO_PASSPHRASE_NAME = "passphrase.key"
		self.CRYPTO_PRIVATE_KEY_FILE = ""
		self.CRYPTO_PRIVATE_KEY_NAME = "private.key"
		self.CRYPTO_PUBLIC_KEY_FILE = ""
		self.CRYPTO_PUBLIC_KEY_NAME = "public.key"
		self.CRYPTO_REMOTE_DIRECTORY = ""
		self.CRYPTO_REMOTE_NAME = "remote"
		self.DATA_LENGTH = data_length
		self.DATA_MODE = data_mode
		self.DEBUG_MODE = debug_mode
		self.DISABLE_EC = disable_ec
		self.EC_AVAILABLE = False
		self.EXTENSION_INIT = extension_init
		self.FLAG_TCP = 0
		self.FLAG_COMPRESSION = 1
		self.FLAG_EC = 2
		self.FLAG_RETURN_DATA = 3
		self.FLAG_SYN = 12
		self.FLAG_ACK = 13
		self.FLAG_FIN = 14
		self.FLAG_RST = 15
		self.HOSTNAME = hostname
		self.IGNORE_BROADCAST_PACKETS = ignore_broadcast_packets
		self.MAX_RETRIES = retries
		self.MAX_SECTIONS = 12
		self.PORT = port
		self.PROTOCOL_FOOTER = "*DDPF*"
		self.PROTOCOL_HEADER = "*DDPH*"
		self.PROTOCOL_PREAMPLE = "\xcc" * 4
		self.PROTOCOL_VERSION = "0610"
		self.REPEATER_MODE = repeater_mode
		self.RS_K = 48
		self.RS_N = 64
		self.RTS_STATE = False
		self.RTS_WAIT = 0.1
		self.RX_WAIT = rx_wait
		self.SECTION_SEPERATOR = "|"
		self.SECTION_HEADER = 0
		self.SECTION_VERSION = 1
		self.SECTION_SOURCE = 2
		self.SECTION_VIA = 3
		self.SECTION_DESTINATION = 4
		self.SECTION_FLAGS = 5
		self.SECTION_APPLICATION_ID = 6
		self.SECTION_PACKET_ID = 7
		self.SECTION_DATA = 8
		self.SECTION_SIGNATURE = 9
		self.SECTION_CHECKSUM = 10
		self.SECTION_FOOTER = 11
		self.SERIAL_CHUNK_SIZE = 1024
		self.SERIAL_BPS = 0
		self.SIDEBAND = sideband
		self.SPECIFICATION = specification
		self.STATE_RX = "rx"
		self.STATE_TX = "tx"
		self.SYN_TIMEOUT = timeout
		self.TX_HANGTIME = tx_hangtime
		self.TX_WAIT = tx_wait
		self.VERIFY_PACKETS_BEFORE_TX = verify_packet_before_tx
		self.VERSION = "0.6.1"
		
		
		# Initialise the new logger
		from danlog import DanLog
		
		if logger_name == "":
			logger_name = "DDP"
		
		self.log = DanLog(logger_name, colour_logging = self.COLOUR_LOGGING)
		
		
		self.log.info("Displaying copyright/license...")
		
		print """
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
"""
		
		self.log.info("Initialising DDP v%s..." % self.VERSION)
		
		
		# Python version checking
		self.log.info("Checking Python version...")
		
		pyv = sys.version_info
		self.log.info("Running under Python v%d.%d.%d." % (pyv[0], pyv[1], pyv[2]))
		
		
		# Check the platform OS
		self.log.info("Checking platform...")
		
		plat = sys.platform.lower()
		
		if plat == "win32":
			self.COLOUR_LOGGING = False
			
			self.log.warn("You appear to be running on Windows, this platform is not supported and it is preferred you run DDP under Cygwin instead.  Bug reports will not be accepted under this OS.")
			
		elif plat == "cygwin":
			self.log.info("You appear to be running on Cygwin under Windows, this platform is fully supported.")
			
		elif plat == "darwin":
			self.log.info("You appear to be running on MacOS, this platform is fully supported.")
			
		elif plat == "os2":
			self.log.warn("You appear to be running on OS2, this platform has not been tested.  Please provide feedback for this operating system.")
			
		elif plat == "os2emx":
			self.log.warn("You appear to be running on OS2EMX, this platform has not been tested.  Please provide feedback for this operating system.")
			
		elif plat == "riscos":
			self.log.warn("You appear to be running on RiscOS, this platform has not been tested.  Please provide feedback for this operating system.")
			
		elif plat == "atheos":
			self.log.warn("You appear to be running on AtheOS, this platform has not been tested.  Please provide feedback for this operating system.")
			
		else:
			if plat.startswith("freebsd"):
				self.log.info("You appear to be running on FreeBSD, this platform is fully supported.")
				
			elif plat.startswith("linux"):
				self.log.info("You appear to be running on Linux, this platform is fully supported.")
				
			elif plat.startswith("sunos"):
				self.log.warn("You appear to be running on SunOS, this platform has not been tested.  Please provide feedback for this operating system.")
				
			else:
				self.log.warn("Unknown UNIX-type operating system \"%s\", please report this OS to the author." % plat)
		
		
		# See what compression modules we can use
		self.log.info("Checking compression module...")
		
		import gzip
		
		self.compressor = gzip
		
		
		# Sort out Reed-Solomon if we need to
		if not self.DISABLE_EC:
			if os.path.exists("pyreedsolomon"):
				sys.path.append("pyreedsolomon")
				
				try:
					if self.DEBUG_MODE:
						self.log.info("Testing Reed-Solomon module...")
						
					
					d = bytearray()
					e = bytearray()
					i = "\x00\x01\x02DDP EC\xfd\xfe\xff".ljust(self.RS_K, "\x00")
					
					
					# The subs will need to told they're available
					import rs
					
					self.reedsolomon = rs
					self.EC_AVAILABLE = True
					
					e.extend(self.encodeReedSolomon(i))
					d.extend(self.decodeReedSolomon(e))
					
					if d <> i:
						self.reedsolomon = None
						self.EC_AVAILABLE = False
						
						self.log.warn("pyreedsolomon comparsion test failed, EC won't be available.")
						
					else:
						self.EC_AVAILABLE = True
					
				except Exception, ex:
					self.reedsolomon = None
					self.EC_AVAILABLE = False
					
					
					self.log.warn("pyreedsolomon threw an exception, EC won't be available.")
					
					if self.DEBUG_MODE:
						self.log.fatal(str(ex))
			
			
			if self.EC_AVAILABLE:
				s = (float(self.RS_N) - float(self.RS_K)) / 2.
				
				self.log.info("pyreedsolomon tests successful, EC enabled (N = %d, K = %d, S = %.2f, Lmax = %.2f%%)." % (self.RS_N, self.RS_K, s, (s / float(self.RS_N)) * 100))
			
		else:
			self.log.warn("EC has been disabled as per application request.")
		
		
		
		# Now sort out the crypto module for callsign signatures
		if not self.CRYPTO_DISABLED:
			try:
				if self.DEBUG_MODE:
					self.log.info("Checking whether we can offer callsign signatures...")
				
				
				# Create the directory structures if we've got this far
				if self.DEBUG_MODE:
					self.log.info("Creating directories...")
				
				
				self.CRYPTO_LOCAL_DIRECTORY = os.path.join(self.CRYPTO_DIRECTORY, self.CRYPTO_LOCAL_NAME)
				self.CRYPTO_REMOTE_DIRECTORY = os.path.join(self.CRYPTO_DIRECTORY, self.CRYPTO_REMOTE_NAME)
				self.CRYPTO_PASSPHRASE_FILE = os.path.join(self.CRYPTO_LOCAL_DIRECTORY, self.CRYPTO_PASSPHRASE_NAME)
				
				self.CRYPTO_PUBLIC_KEY_FILE = os.path.join(self.CRYPTO_LOCAL_DIRECTORY, self.CRYPTO_PUBLIC_KEY_NAME)
				self.CRYPTO_PRIVATE_KEY_FILE = os.path.join(self.CRYPTO_LOCAL_DIRECTORY, self.CRYPTO_PRIVATE_KEY_NAME)
				
				
				if not os.path.exists(self.CRYPTO_DIRECTORY):
					os.mkdir(self.CRYPTO_DIRECTORY)
				
				if not os.path.exists(self.CRYPTO_LOCAL_DIRECTORY):
					os.mkdir(self.CRYPTO_LOCAL_DIRECTORY)
				
				if not os.path.exists(self.CRYPTO_REMOTE_DIRECTORY):
					os.mkdir(self.CRYPTO_REMOTE_DIRECTORY)
				
				
				# Sort the passphrase file out
				if not os.path.exists(self.CRYPTO_PASSPHRASE_FILE):
					if self.DEBUG_MODE:
						self.log.warn("No passphrase file found, creating it...")
					
					
					c = DanRSA()
					c.savePassphrase(self.CRYPTO_PASSPHRASE_FILE, c.generatePassphrase())
					c = None
				
				
				# Read the passphrase in
				if os.path.exists(self.CRYPTO_PASSPHRASE_FILE):
					c = DanRSA()
					self.CRYPTO_PASSPHRASE = c.loadPassphrase(self.CRYPTO_PASSPHRASE_FILE)
					c = None
				
				
				# Generate the key pairs, if required
				if not os.path.exists(self.CRYPTO_PUBLIC_KEY_FILE) or not os.path.exists(self.CRYPTO_PRIVATE_KEY_FILE):
					if self.DEBUG_MODE:
						self.log.warn("No RSA key pair found, creating one...")
					
					
					c = DanRSA(passphrasecallback = self.CRYPTO_PASSPHRASE)
					c.generateKeyPair(self.CRYPTO_PUBLIC_KEY_FILE, self.CRYPTO_PRIVATE_KEY_FILE)
					c = None
				
				
				# Test the crypto with our keys, first encryption
				if self.DEBUG_MODE:
					self.log.info("Testing public key encryption...")
				
				
				i = "\x00\x01\x02DDP RSA\xfd\xfe\xff"
				
				c = DanRSA(self.CRYPTO_PUBLIC_KEY_FILE, None, self.CRYPTO_PASSPHRASE)
				e = c.encrypt(i)
				c = None
				
				
				# Now decryption
				if self.DEBUG_MODE:
					self.log.info("Testing private key decryption...")
				
				
				c = DanRSA(None, self.CRYPTO_PRIVATE_KEY_FILE, self.CRYPTO_PASSPHRASE)
				d = c.decrypt(e)
				c = None
				
				
				# Analysis the result
				if d <> i:
					self.crypto = None
					self.CRYPTO_AVAILABLE = False
					
					self.log.warn("The decrypted data doesn't match the test case, callsign authentication won't be available.")
					
				else:
					# Everything is fine, setup the main RSA object
					self.crypto = DanRSA(self.CRYPTO_PUBLIC_KEY_FILE, self.CRYPTO_PRIVATE_KEY_FILE, self.CRYPTO_PASSPHRASE)
					self.CRYPTO_AVAILABLE = True
				
			except Exception, ex:
				self.crypto = None
				self.CRYPTO_AVAILABLE = False
				
				
				self.log.warn("Unable to offer crypto since the module threw an exception, ensure you have M2Crypto installed.")
				
				if self.DEBUG_MODE:
					self.log.fatal(str(ex))
			
			
			if self.CRYPTO_AVAILABLE:
				self.log.info("Callsign authentication tests successful.")
			
		else:
			self.crypto = None
			self.CRYPTO_AVAILABLE = False
			
			
			if self.DEBUG_MODE:
				self.log.warn("The crypto module has been disabled as per user request, this means we can't offer callsign signatures or verify the packet source.")
		
		
		if self.CRYPTO_ALLOW_UNSIGNED_PACKETS:
			self.log.warn("Unsigned packets are allowed, this is not recommended.")
			
		else:
			self.log.info("Unsigned packets are NOT allowed.")
		
		
		# Application ID
		if application == "":
			application = "DDP"
		
		self.APPLICATION_ID = self.sha1(application)
		
		
		self.log.info("DDP has been initialised with application ID %s." % self.APPLICATION_ID)
		
		
		# Repeater mode
		if self.REPEATER_MODE:
			self.log.info("DDP is running in repeater mode, packets will be handled differently (application ID).")
		
		
		# Sort out the data mode
		if self.DATA_MODE.upper() == "D-STAR":
			if self.DEBUG_MODE:
				self.log.info("Setting up for D-STAR (DV) mode...")
			
			
			self.BACKEND = "D-STAR"
			self.setupDSTAR(self.HOSTNAME, self.PORT)
			
		elif self.DATA_MODE.upper() == "RS-232":
			if self.DEBUG_MODE:
				self.log.info("Setting up for RS-232 mode...")
			
			
			self.BACKEND = "RS-232"
			self.setupRS232(self.HOSTNAME, self.PORT)
			
		elif self.DATA_MODE.upper() == "GMSK":
			if self.DEBUG_MODE:
				self.log.info("Setting up for GMSK mode...")
			
			
			self.BACKEND = "GMSK"
			self.setupGMSK(self.HOSTNAME, self.PORT)
			
		elif self.DATA_MODE.upper() == "EXTENSION":
			if self.DEBUG_MODE:
				self.log.info("Setting up for EXTENSION mode...")
			
			
			if self.EXTENSION_INIT is not None:
				self.EXTENSION_INIT(self.HOSTNAME, self.PORT)
				
			else:
				if self.DEBUG_MODE:
					self.log.warn("The extension initialisation subroutine appears to be null, cannot run it.")
			
		elif self.DATA_MODE.upper() == "FDMDV":
			if self.DEBUG_MODE:
				self.log.info("Setting up for FDMDV mode...")
			
			
			self.BACKEND = "FDMDV"
			self.setupFDMDV(self.HOSTNAME, self.PORT)
			
		else:
			if self.DEBUG_MODE:
				self.log.info("Setting up for Fldigi mode using %s..." % self.DATA_MODE)
			
			
			self.BACKEND = "FLDIGI"
			self.setupFldigi(self.HOSTNAME, self.PORT)
			
		
		
		# Warnings
		if self.BACKEND == "FLDIGI":
			if self.EC_AVAILABLE and not self.DISABLE_EC:
				if self.DATA_MODE.upper().startswith("PSK") and self.DATA_MODE.upper().endswith("R"):
					self.log.warn("EC is available but will not be used when using fldigi, a robust mode has already been chosen.")
					
				else:
					self.log.warn("EC is available but will not be used when using fldigi, just use a robust digital mode like PSK500R.")
		
		
		# The specifications are now dynamically loaded, this allows for adding new specs without changing the core
		self.log.info("Importing specification ID %d..." % self.SPECIFICATION)
		
		self.spec_module = __import__("ddp_specification_%02d" % self.SPECIFICATION)
		self.spec_module.init(self)
		
		
		# Other useful information
		self.log.info("SYN packet timeout is %.2f seconds." % self.SYN_TIMEOUT)
		self.log.info("ACK packet timeout is %.2f seconds (when using TCP mode)." % self.ACK_TIMEOUT)
		self.log.info("TX hangtime (PTT) is %.3f seconds." % self.TX_HANGTIME)
		
		
		# Completed
		self.log.info("Initialisation complete.")
	
	def compressStream(self, data):
		if self.DEBUG_MODE:
			self.log.info("Running...")
			
		
		dio = StringIO()
		
		com = self.compressor.GzipFile(fileobj = dio, mode = "wb", compresslevel = 9)
		com.write(data)
		com.close()
		
		return dio.getvalue()
	
	def constructPacket(self, callsign_from, via, callsign_to, flags, data, application_id = "", signature = ""):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		if application_id == "":
			application_id = self.APPLICATION_ID
		
		return self.spec_module.constructPacket(self, callsign_from, via, callsign_to, flags, data, application_id, signature)
	
	def cw(self, message):
		if self.DEBUG_MODE:
			self.log.info("Running...")
			
		
		if self.serial is not None:
			if self.DEBUG_MODE:
				self.log.warn("Can't send CW over serial, so ignoring...")
		
		elif self.fldigi is not None:
			self.fldigi.modem.set_by_name("CW")
			self.fldigi.modem.set_carrier(800)
			self.fldigi.text.clear_rx()
			self.fldigi.text.clear_tx()
			self.fldigi.text.add_tx(message + "^r")
			
			self.fldigi.main.tx()
			
			while self.fldigi.main.get_trx_status() == "tx":
				time.sleep(self.TX_WAIT)
			
			# Reset
			self.fldigi.modem.set_by_name(self.DATA_MODE)
			self.fldigi.modem.set_carrier(self.CARRIER_FREQUENCY)
			
			self.fldigi.main.set_lock(True)
			
			self.fldigi.text.clear_rx()
			self.fldigi.text.clear_tx()
	
	def decodeBase128ToStream(self, data, offset = 0, hexmode = False):
		if self.DEBUG_MODE:
			self.log.info("Running...")
			
		
		ret = bytearray()
		
		for c in xrange(0, len(data), 2):
			if hexmode:
				ret.extend(chr(int(data[c:c + 2], 16)))
				
			else:
				ret.extend(chr(ord(data[c:c + 1]) + ord(data[c + 1:c + 2])))
		
		return self.offsetChar(str(ret), -offset)
	
	def decodeBaseToNumber(self, data, base = 256):
		if self.DEBUG_MODE:
			self.log.info("Running...")
			
		
		ret = 0
		
		for c in data:
			ret *= base
			ret += ord(c)
		
		return ret
	
	def decodeData(self, data, flags):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		return self.spec_module.decodeData(self, data, flags)
	
	def decodeReedSolomon(self, data):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		if self.EC_AVAILABLE:
			coder = self.reedsolomon.RSCoder(self.RS_N, self.RS_K)
			ret = bytearray()
			
			for c in xrange(0, len(data), self.RS_N):
				ret.extend(coder.decode(str(data)[c:c + self.RS_N], nostrip = True))
			
			return str(ret)
			
		else:
			if self.DEBUG_MODE:
				self.log.warn("EC is not available, returning the data anyway...")
			
			return str(data)
	
	def decompressStream(self, data):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		dio = StringIO(data)
		com = self.compressor.GzipFile(fileobj = dio, mode = "rb")
		
		return com.read()
	
	def deinterleave(self, data):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		return self.interleave(data, log = False)
	
	def descramble(self, data):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		return self.scramble(data, log = False)
	
	def dispose(self):
		if self.DEBUG_MODE:
			self.log.info("Running...")
			
		
		if self.devnull is not None:
			self.devnull.close()
		
		
		if self.fldigi is not None:
			self.fldigi = None
			
		elif self.serial is not None:
			self.serial.close()
			self.serial = None
	
	def encodeData(self, data, flags):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		return self.spec_module.encodeData(self, data, flags)
	
	def encodeNumberToBase(self, number, base = 256):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		ret = ""
		
		while number <> 0:
			ret = chr(number % base) + ret
			number /= base
		
		return ret
	
	def encodeReedSolomon(self, data):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		if self.EC_AVAILABLE:
			coder = self.reedsolomon.RSCoder(self.RS_N, self.RS_K)
			ret = bytearray()
			
			for b in xrange(0, len(data), self.RS_K):
				c = coder.encode(str(data)[b:b + self.RS_K].ljust(self.RS_K, "\x00"))
				ret.extend(c)
			
			return str(ret)
			
		else:
			if self.DEBUG_MODE:
				self.log.warn("EC is not available, returning the data anyway...")
			
			return str(data)
	
	def encodeStreamToBase128(self, data, offset = 0, hexmode = False):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		ret = bytearray()
		
		for c in self.offsetChar(data, offset):
			if hexmode:
				ret.extend(hex(ord(c)).replace("0x", "").rjust(2, "0"))
				
			else:
				if ord(c) > 127:
					ret.extend(chr(127))
					ret.extend(chr(ord(c) - 127))
					
				else:
					ret.extend(chr(0))
					ret.extend(chr(ord(c)))
		
		return str(ret)
	
	def generatePacketID(self):
		return self.uuid()
	
	def interleave(self, data, log = True):
		if log and self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		ret = bytearray()
		
		llen = int(math.sqrt(self.RS_N))
		chunks = self.splitDataIntoChunks(data, self.RS_N)
		
		for subchunk in chunks:
			lines = self.splitDataIntoChunks(subchunk, llen)
			
			if len(lines) == llen:
				if self.DEBUG_MODE:
					self.log.info("Matrix: -")
					self.log.info("    12345678")
					self.log.info("  -----------")
					self.log.info("A |" + repr(lines[0]))
					self.log.info("B |" + repr(lines[1]))
					self.log.info("C |" + repr(lines[2]))
					self.log.info("D |" + repr(lines[3]))
					self.log.info("E |" + repr(lines[4]))
					self.log.info("F |" + repr(lines[5]))
					self.log.info("G |" + repr(lines[6]))
					self.log.info("H |" + repr(lines[7]))
				
				for j in zip(lines[7], lines[6], lines[5], lines[4], lines[3], lines[2], lines[1], lines[0]):
					for i in j[::-1]:
						ret.extend(i)
				
			else:
				if self.DEBUG_MODE:
					self.log.error("The subchunks appear to have a invalid length (%d/%d), returning data so far..." % (len(lines), llen))
					
				return str(ret)
		
		if self.DEBUG_MODE:
			self.log.info("In : %s" % repr(data))
			self.log.info("Out: %s" % repr(str(ret)[::-1]))
		
		return str(ret)[::-1]
	
	def offsetChar(self, data, offset):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		if offset <> 0:
			ret = bytearray()
			
			for c in data:
				x = 0
				
				if ord(c) + offset < 0:
					x = (ord(c) + offset) + 256
				
				elif ord(c) + offset > 255:
					x = (ord(c) + offset) - 256
					
				else:
					x = (ord(c) + offset)
				
				ret.extend(chr(x))
			
			return str(ret)
			
		else:
			return data
	
	def ptt(self, state):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		if self.serial is not None:
			lock = threading.Lock()
			
			with lock:
				self.RTS_STATE = state
				
				self.serial.setRTS(state)
				
				
				if self.DEBUG_MODE:
					# Hang around to give the rig chance to react
					if self.TX_HANGTIME > 0.:
						time.sleep(self.TX_HANGTIME)
					
					
					if state == True:
						self.log.info("PTT on.")
						
					else:
						self.log.info("PTT off.")
	
	def receiveData(self, callsign_from, callsign_to):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		data = self.receiveDataFromAny(callsign_from)
		
		if data is not None:
			# Verify the packet source
			if data[1][self.SECTION_SOURCE] == callsign_to:
				
				# And the destination
				if data[1][self.SECTION_DESTINATION] == callsign_from or (data[1][self.SECTION_DESTINATION] == self.BROADCAST_CALLSIGN and not self.IGNORE_BROADCAST_PACKETS):
					return data
					
				else:
					if self.DEBUG_MODE:
						if data[1][self.SECTION_DESTINATION] == self.BROADCAST_CALLSIGN:
							self.log.warn("Broadcast packet ignored as per user settings.")
							
						else:
							self.log.warn("Packet didn't appear to be for us as it's for %s." % callsign_from)
					
					return None
				
			else:
				if self.DEBUG_MODE:
					self.log.warn("Packet didn't appear to come from %s." % callsign_to)
			
			return None
			
		else:
			if self.DEBUG_MODE:
				self.log.warn("No valid data has been received...")
			
			return None
	
	def receiveDataFromAny(self, callsign_from):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		retries = 1
		rx = []
		
		# Loop around until we timeout or receive the FIN packet and ACK it
		while True:
			if self.DEBUG_MODE:
				self.log.info("Receiving packet...")
			
			
			packet = self.receivePacket(self.SYN_TIMEOUT)
			error = False
			
			if packet is not None:
				# If the from_callsign is blank, set to what the packet has - useful for monitoring packets
				if callsign_from == "" and not self.IGNORE_BROADCAST_PACKETS:
					callsign_from = packet[self.SECTION_DESTINATION]
				
				
				# Ensure the packet is for us before continuing
				if packet[self.SECTION_DESTINATION] == callsign_from or (packet[self.SECTION_DESTINATION] == self.BROADCAST_CALLSIGN and not self.IGNORE_BROADCAST_PACKETS):
					# Check the flags
					f = str(packet[self.SECTION_FLAGS])[::-1]
					
					if f[self.FLAG_RST] == "1":
						if self.DEBUG_MODE:
							self.log.warn("The returned packet was RST.")
						
					else:
						if f[self.FLAG_SYN] == "1" and f[self.FLAG_ACK] == "0":
							# All looks good, move on - the actual data isn't important
							rx.append(packet)
							
							
							# TCP traffic must be ACK'ed
							if f[self.FLAG_TCP] == "1":
								if self.DEBUG_MODE:
									self.log.info("SYN (TCP) packet received, ACK'ing...")
								
								flags = Bits()
								flags.set(self.FLAG_COMPRESSION, 0)
								flags.set(self.FLAG_SYN, 1)
								flags.set(self.FLAG_ACK, 1)
								
								self.transmitPacket(callsign_from, "", packet[self.SECTION_SOURCE], flags, "SYN-ACK")
								
							else:
								if self.DEBUG_MODE:
									self.log.info("SYN (UDP) packet received.")
							
						elif f[self.FLAG_FIN] == "1" and f[self.FLAG_ACK] == "0":
							if f[self.FLAG_TCP] == "1":
								# FIN received, send a FIN-ACK
								if self.DEBUG_MODE:
									self.log.info("FIN (TCP) packet received, ACK'ing...")
								
								flags = Bits()
								flags.set(self.FLAG_COMPRESSION, 0)
								flags.set(self.FLAG_ACK, 1)
								flags.set(self.FLAG_FIN, 1)
								
								self.transmitPacket(callsign_from, "", packet[self.SECTION_SOURCE], flags, "FIN-ACK")
								
							else:
								if self.DEBUG_MODE:
									self.log.info("FIN (UDP) packet received.")
							
							
							# FIN indicates the end of the data, so return the data
							break
						
						
						# Return the data if the packet has been flagged to do so
						if f[self.FLAG_RETURN_DATA] == "1":
							if self.DEBUG_MODE:
								self.log.info("Returning data as requested by the packet flag...")
							
							break
					
				else:
					if self.DEBUG_MODE:
						if packet[self.SECTION_DESTINATION] == self.BROADCAST_CALLSIGN:
							self.log.warn("Broadcast packet ignored as per user settings.")
							
						else:
							self.log.warn("The packet wasn't for us, it was for %s." % packet[self.SECTION_DESTINATION])
				
			else:
				error = True
			
			
			# Timeout or packet not heard
			if error:
				if self.DEBUG_MODE:
					self.log.warn("No valid packet was received.")
				
				if retries >= self.MAX_RETRIES:
					if self.DEBUG_MODE:
						self.log.warn("Maximum retries (%d) has been exceeded." % self.MAX_RETRIES)
					
					return None
				
				retries += 1
		
		
		# Return the data
		if len(rx) == 0:
			return None
			
		else:
			data = bytearray()
			
			for r in rx:
				data.extend(self.decodeData(str(r[self.SECTION_DATA]), r[self.SECTION_FLAGS]))
			
			return [str(data), rx[0]]
	
	def receivePacket(self, timeout = 0.):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		buffer = bytearray()
		
		starttime = time.time()
		
		
		# Ensure we're not keyed up
		if self.serial is not None:
			self.ptt(False)
		
		while True:
			extracted = None
			
			if self.fldigi is not None:
				# Fldigi requires the buffer to be filled differently...
				buffer = bytearray()
				bytes = self.fldigi.text.get_rx_length()
				
				if bytes > 0:
					# Ensure we're thread-safe
					lock = threading.Lock()
					
					with lock:
						try:
							# Check it twice, to reduce the chance of getting a "Integer parameter too high" exception
							bytes = self.fldigi.text.get_rx_length()
							
							if bytes > 0:
								buffer.extend(str(self.fldigi.text.get_rx(0, bytes - 1).data))
							
						except xmlrpclib.Fault, ex:
							if self.DEBUG_MODE:
								self.log.fatal(str(ex))
				
				x = str(buffer).rfind(self.PROTOCOL_HEADER)
				
				if x <> -1:
					y = str(buffer).rfind(self.PROTOCOL_FOOTER, x + len(self.PROTOCOL_HEADER))
					
					if y <> -1:
						if y > x:
							if self.DEBUG_MODE:
								self.log.info("A packet has been found in the text.")
							
							
							# Clear fldigi, we can't do it earlier since it misses chunks of information if we clear too often
							self.fldigi.text.clear_rx()
							
							y += len(self.PROTOCOL_FOOTER)
							
							# There appears to be complete packet in there, extract it
							extracted = self.spec_module.parsePacket(self, str(buffer[x:y]))
							
						else:
							if self.DEBUG_MODE:
								self.log.warn("Packet not ready yet (%d/%d)." % (x, y))
					
			elif self.serial is not None:
				# We fill up the buffer with as much data as we can before the timeout and extract out any packets we find
				lock = threading.Lock()
				
				with lock:
					try:
						bytes = self.serial.read(self.serial.inWaiting())
						
						if len(bytes) > 0:
							if self.DEBUG_MODE:
								self.log.info("%d bytes will be put into the serial buffer." % len(bytes))
							
							buffer.extend(bytes)
						
					except Exception, ex:
						if self.DEBUG_MODE:
							self.log.fatal(str(ex))
				
				
				# Read the packet backwards to avoid getting any part packets in the buffer
				x = str(buffer).rfind(self.PROTOCOL_HEADER)
				
				if x <> -1:
					y = str(buffer).rfind(self.PROTOCOL_FOOTER, x + len(self.PROTOCOL_HEADER))
					
					if y <> -1:
						if y > x:
							if self.DEBUG_MODE:
								self.log.info("A packet has been found in the buffer.")
							
							
							y += len(self.PROTOCOL_FOOTER)
							
							# There appears to be complete packet in there, extract it
							extracted = self.spec_module.parsePacket(self, str(buffer[x:y]))
							
							if extracted is None:
								# If the packet doesn't parse, clear the buffer otherwise we may enter a loop until the serial buffer overflows
								if self.DEBUG_MODE:
									self.log.warn("The packet didn't parse correctly, the buffer will be cleared.")
								
								buffer = bytearray()
							
						else:
							if self.DEBUG_MODE:
								self.log.warn("Packet not ready yet (%d/%d)." % (x, y))
			
			
			# Anything to return yet?
			if extracted is not None:
				packet = self.splitPacket(extracted)
				
				if packet is not None:
					if self.verifyPacket(packet):
						
						if self.DEBUG_MODE:
							self.log.info("Packet received is valid.")
						
						return packet
						
					else:
						if self.DEBUG_MODE:
							self.log.warn("Packet received is invalid.")
						
						break
					
				else:
					if self.DEBUG_MODE:
						self.log.warn("Packet did not split correctly.")
					
					break
			
			
			# Timer
			endtime = time.time()
			
			if (endtime - starttime) >= timeout:
				if self.DEBUG_MODE:
					self.log.warn("Timeout waiting for packet.")
				
				break
				
			else:
				time.sleep(self.RX_WAIT)
		
		return None
	
	def scramble(self, data, log = True):
		if log and self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		random.seed(self.PROTOCOL_HEADER + self.PROTOCOL_VERSION + self.PROTOCOL_FOOTER)
		
		
		ret = bytearray()
		
		for c in data:
			ret.extend(chr(ord(c) ^ random.randint(0, 255)))
		
		return str(ret)
	
	def setCallsign(self, callsign):
		self.CALLSIGN = callsign
	
	def setupDSTAR(self, device = "/dev/ttyu0", port = "9600/8/N/1", timeout = 60.):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		self.setupRS232(device, port, timeout)
		
		
		# Fudge some settings for improved performance
		self.DATA_LENGTH = 640
		self.TX_HANGTIME = 0.1
	
	def setupFDMDV(self, play_device = "/dev/dsp0", record_device = "/dev/dsp1"):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		try:
			self.fdmdv = FDMDV(colour_logging = self.COLOUR_LOGGING, debug_mode = self.DEBUG_MODE)
			
		except ImportError:
			self.log.fatal("Failed to load the FDMDV module, please note this will only work under FreeBSD, Linux, and other Unixes.")
			
		except Exception, ex:
			self.log.fatal("Failed to initialise the FDMDV backend.")
			self.log.fatal(str(ex))
	
	def setupFldigi(self, hostname = "localhost", port = 7362):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		self.fldigi = xmlrpclib.ServerProxy("http://%s:%s" % (hostname, port))
		
		self.fldigi.main.set_lock(False)
		
		self.fldigi.modem.set_carrier(self.CARRIER_FREQUENCY)
		self.fldigi.modem.set_by_name(self.DATA_MODE)
		
		self.fldigi.main.set_sideband(self.SIDEBAND)
		self.fldigi.main.set_lock(True)
		
		
		# Fudge some settings for improved performance
		self.TX_HANGTIME = 0.2
	
	def setupGMSK(self, device = "/dev/ttyu0", port = "9600/8/N/1", timeout = 60.):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		self.setupRS232(device, port, timeout)
		
		
		# Fudge some settings for improved performance
		self.TX_HANGTIME = 0.1
		
		self.PROTOCOL_PREAMPLE = "\xcc" * 16
	
	def setupRS232(self, device = "/dev/ttyu0", port = "9600/8/N/1", timeout = 60.):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		try:
			import serial
			
			
			conn = port.split("/")
			
			self.serial = serial.Serial()
			self.serial.baudrate = int(conn[0])
			self.serial.bytesize = int(conn[1])
			self.serial.parity = conn[2]
			self.serial.port = device
			self.serial.stopbits = int(conn[3])
			self.serial.timeout = timeout
			self.serial.writeTimeout = None
			self.serial.xonxoff = None
			
			self.serial.open()
			
			self.serial.setRTS(False)
			
			self.serial.flushInput()
			self.serial.flushOutput()
			
			
			# Fudge some settings for improved performance
			self.TX_HANGTIME = 0.075
			
			
			# How much data can we send per second?
			p = 0.
			
			if self.serial.parity <> "N":
				p = 1.
			
			self.SERIAL_BPS = float(self.serial.baudrate) / (float(self.serial.bytesize) + p + float(self.serial.stopbits))
			
			
			if self.DEBUG_MODE:
				self.log.info("Serial port can handle %d bytes per second." % self.SERIAL_BPS)
			
		except ImportError:
			self.log.fatal("Failed to load the serial module, ensure PySerial is installed.")
			
		except Exception, ex:
			self.log.fatal("Failed to initialise the RS-232 backend.")
			self.log.fatal(str(ex))
	
	def sha1(self, data):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		h = hashlib.sha1()
		h.update(data)
		
		return str(h.hexdigest())
	
	def splitDataIntoChunks(self, data, length):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		chunks = []
		
		for i in xrange(0, len(data), length):
			chunks.append(data[i:i + length])
		
		return chunks
	
	def splitPacket(self, packet):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		return self.spec_module.splitPacket(self, packet)
	
	def transmitBroadcast(self, callsign_from, data):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		# Broadcast packets are always UDP and never send a FIN packet when done
		self.transmitData(callsign_from, "", self.BROADCAST_CALLSIGN, data, 0, 0, False)
	
	def transmitData(self, callsign_from, via, callsign_to, data, tcp = 1, compress = 1, fin = True, return_data = 0):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		chunks = self.splitDataIntoChunks(data, self.DATA_LENGTH)
		
		
		flags = Bits()
		flags.set(self.FLAG_TCP, tcp)
		
		if not self.spec_module.isCompressionAllowed(self):
			compress = 0
		
		flags.set(self.FLAG_COMPRESSION, compress)
		
		if self.BACKEND <> "FLDIGI":
			flags.set(self.FLAG_EC, int(self.EC_AVAILABLE))
		
		flags.set(self.FLAG_RETURN_DATA, return_data)
		flags.set(self.FLAG_SYN, 1)
		
		
		for c in chunks:
			# First we send a SYN packet, we should get a SYN-ACK back (if using TCP) which means we can send the next packet
			retries = 1
			
			while True:
				if self.DEBUG_MODE:
					self.log.info("Sending SYN (attempt %d/%d)..." % (retries, self.MAX_RETRIES))
				
				
				self.transmitPacket(callsign_from, via, callsign_to, flags, c)
				
				# Wait the ACK packet back
				if tcp == 1:
					if self.DEBUG_MODE:
						self.log.info("Waiting for SYN-ACK...")
					
					
					back = self.receivePacket(self.ACK_TIMEOUT)
					
					if back is not None:
						# Check the source
						if back[self.SECTION_SOURCE] == callsign_to:
							
							# And the destination
							if back[self.SECTION_DESTINATION] == callsign_from:
								# Check the flags
								f = str(back[self.SECTION_FLAGS])[::-1]
								
								if f[self.FLAG_RST] == "1":
									if self.DEBUG_MODE:
										self.log.warn("The returned packet was RST.")
										
										break
									
								else:
									if f[self.FLAG_SYN] == "1" and f[self.FLAG_ACK] == "1":
										# All looks good, move on - the actual data bs[5] isn't important
										if self.DEBUG_MODE:
											self.log.info("SYN-ACK received.")
										
										break
										
									else:
										if self.DEBUG_MODE:
											self.log.warn("Packet didn't appear to be ACK'ed.")
								
							else:
								if self.DEBUG_MODE:
									self.log.warn("Packet didn't appear to be for us as it's for %s." % callsign_from)
							
						else:
							if self.DEBUG_MODE:
								self.log.warn("Packet didn't appear to come from %s." % callsign_to)
					
					
					# Timeout or packet not heard
					if self.DEBUG_MODE:
						self.log.warn("No valid packet was received.")
					
					if retries >= self.MAX_RETRIES:
						if self.DEBUG_MODE:
							self.log.warn("No SYN-ACK received after %d retries..." % self.MAX_RETRIES)
						
						return False
					
					retries += 1
					
				else:
					break
		
		
		# Finally, send a FIN packet (if requested)
		if fin:
			flags = Bits()
			flags.set(self.FLAG_TCP, tcp)
			flags.set(self.FLAG_COMPRESSION, 0)
			
			if self.BACKEND <> "FLDIGI":
				flags.set(self.FLAG_EC, int(self.EC_AVAILABLE))
			
			flags.set(self.FLAG_FIN, 1)
			
			retries = 1
			
			while True:
				# First we send a FIN packet, we should get a FIN-ACK (if using TCP) back which means we can send the next packet
				if self.DEBUG_MODE:
					self.log.info("Sending FIN (attempt %d/%d)..." % (retries, self.MAX_RETRIES))
				
				
				self.transmitPacket(callsign_from, via, callsign_to, flags, "73")
				
				# Wait the ACK packet back
				if tcp == 1:
					if self.DEBUG_MODE:
						self.log.info("Waiting for FIN-ACK...")
					
					
					back = self.receivePacket(self.ACK_TIMEOUT)
					
					if back is not None:
						# Validate the source
						if back[self.SECTION_SOURCE] == callsign_to:
							
							# And now the destination
							if back[self.SECTION_DESTINATION] == callsign_from:
								# Check the flags
								f = str(back[self.SECTION_FLAGS])[::-1]
								
								if f[self.FLAG_RST] == "1":
									if self.DEBUG_MODE:
										self.log.warn("The returned packet was RST.")
										
										break
									
								else:
									if f[self.FLAG_FIN] == "1" and f[self.FLAG_ACK] == "1":
										# All looks good, move on - the actual data bs[5] isn't important
										if self.DEBUG_MODE:
											self.log.info("FIN-ACK received.")
										
										break
										
									else:
										if self.DEBUG_MODE:
											self.log.warn("Packet didn't appear to be ACK'ed.")
								
							else:
								if self.DEBUG_MODE:
									self.log.warn("Packet didn't appear to be for us as it's for %s." % callsign_from)
							
						else:
							if self.DEBUG_MODE:
								self.log.warn("Packet didn't appear to come from %s." % callsign_to)
					
					
					# Timeout or packet not heard
					if self.DEBUG_MODE:
						self.log.warn("No valid packet was received.")
					
					if retries >= self.MAX_RETRIES:
						if self.DEBUG_MODE:
							self.log.warn("No SYN-ACK received after %d retries..." % self.MAX_RETRIES)
						
						return False
					
					retries += 1
					
				else:
					break
		
		
		# Ensure we've got the rig off key
		self.ptt(False)
		
		return True
	
	def transmitPacket(self, callsign_from, via, callsign_to, flags, data):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		p = self.constructPacket(callsign_from, via, callsign_to, flags, data)
		
		self.transmitRawPacket(p)
	
	def transmitRawPacket(self, packet):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		# First verify the packet (if required) before transmitting
		if self.VERIFY_PACKETS_BEFORE_TX:
			if not self.validatePacket(packet):
				return
		
		
		# Wait until we are rx'ing before continuing
		self.waitUntil(self.STATE_RX)
		
		
		lock = threading.Lock()
		
		if self.fldigi is not None:
			with lock:
				s = bytearray()
				s.extend(str(packet))
				
				try:
					self.fldigi.text.clear_rx()
					self.fldigi.text.clear_tx()
					
					self.fldigi.text.add_tx_bytes(xmlrpclib.Binary(str(s)))
					
					
					if self.DEBUG_MODE:
						self.log.info("Transmitting raw packet %s (%d bytes)..." % (repr(packet), len(str(packet))))
					
					self.fldigi.main.tx()
					
				except xmlrpclib.Fault, ex:
					if self.DEBUG_MODE:
						self.log.fatal(str(ex))
			
		elif self.serial is not None:
			with lock:
				s = bytearray()
				s.extend(str(packet))
				
				
				wrote = None
				
				try:
					self.ptt(True)
					
					
					if self.DEBUG_MODE:
						self.log.info("Transmitting raw packet %s (%d bytes)..." % (repr(packet), len(str(packet))))
					
					
					# Time how long it takes to write the data in-case the OS caches the serial data
					starttime = time.time()
					
					wrote = self.serial.write(str(s))
					self.serial.flush()
					
					finishtime = time.time()
					
					
					dlen = float(len(str(s)))
					timeneeded = (dlen / self.SERIAL_BPS)
					timetaken = (finishtime - starttime)
					
					if self.DEBUG_MODE:
						self.log.info("Data length: %d, BPS: %d, Time required: %.5f, Time taken: %.5f" % (dlen, self.SERIAL_BPS, timeneeded, timetaken))
					
					
					p = round(timeneeded - timetaken, 3)
					
					if p > 0.:
						if self.DEBUG_MODE:
							self.log.warn("Waiting for %.3f seconds for data to flush..." % p)
						
						time.sleep(p)
					
					
					if wrote is not None:
						if wrote <> len(s):
							if self.DEBUG_MODE:
								self.log.warn("%d/%d bytes where written to the serial port." % (wrote, len(s)))
					
					
					self.ptt(False)
					
				except Exception, ex:
					if self.DEBUG_MODE:
						self.log.fatal(str(ex))
				
				
				if wrote is not None:
					
					if wrote <> len(s):
						if self.DEBUG_MODE:
							self.log.warn("%d/%d bytes where written to the serial port." % (wrote, len(s)))
			
		elif self.fdmdv is not None:
			with lock:
				s = bytearray()
				s.extend(str(packet))
				
				
				wrote = None
				
				try:
					if self.DEBUG_MODE:
						self.log.info("Transmitting raw packet %s (%d bytes)..." % (repr(packet), len(str(packet))))
					
					
					self.fdmdv.transmitPacket(str(s))
					
				except Exception, ex:
					if self.DEBUG_MODE:
						self.log.fatal(str(ex))
				
				
				if wrote is not None:
					
					if wrote <> len(s):
						if self.DEBUG_MODE:
							self.log.warn("%d/%d bytes where written to the serial port." % (wrote, len(s)))
		
		# Wait until everything has been tx'ed
		self.waitUntil(self.STATE_RX)
	
	def uuid(self, *args):
		import socket
		
		
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		t = long(time.time() * 1000)
		r = long(random.random() * 100000000000000000L)
		a = None
		
		try:
			a = socket.gethostbyname(socket.gethostname())
		
		except:
			# We can't get a network address, so improvise
			a = random.random() * 100000000000000000L
		
		data = str(t) + " " + str(r) + " " + str(a) + str(args)
		
		return self.sha1(data)
	
	def validatePacket(self, packet):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		x = packet.rfind(self.PROTOCOL_HEADER)
		
		if x <> -1:
			y = packet.rfind(self.PROTOCOL_FOOTER, x + len(self.PROTOCOL_HEADER))
			
			if y <> -1:
				y += len(self.PROTOCOL_FOOTER)
				
				a = self.spec_module.parsePacket(self, str(packet[x:y]))
				
				if a is not None:
					b = self.spec_module.splitPacket(self, a)
					
					if b is not None:
						c = self.spec_module.verifyPacket(self, b)
						
						if c:
							if self.DEBUG_MODE:
								self.log.info("Packet has been validated.")
							
							return True
							
						else:
							self.log.error("The packet doesn't appear parse.")
						
					else:
						self.log.error("The packet failed to split correctly.")
					
				else:
					self.log.error("The packet failed to parse correctly.")
				
			else:
				self.log.error("The packet doesn't appear to be complete (1).")
			
		else:
			self.log.error("The packet doesn't appear to be complete (2).")
		
		return False
	
	def verifyPacket(self, packet):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		return self.spec_module.verifyPacket(self, packet)
	
	def waitUntil(self, state):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		if self.fldigi is not None:
			while self.fldigi.main.get_trx_status() <> state:
				time.sleep(self.TX_WAIT)
			
		elif self.serial is not None or self.fdmdv is not None:
			if state == self.STATE_RX:
				state = False
				
			elif state == self.STATE_TX:
				state = True
			
			
			if self.serial is not None:
				while self.RTS_STATE <> state:
					time.sleep(self.TX_WAIT)
				
			elif self.fdmdv is not None:
				while self.fdmdv.getState() <> state:
					time.sleep(self.TX_WAIT)
	
	def xorChecksum(self, data):
		s = 0
		
		for i in str(data):
			s = s ^ ord(i)
		
		s = "%02x" % s
		
		return s

class FDMDV():
	def __init__(self, dsp_play_device ="/dev/dsp", dsp_record_device = "/dev/dsp", colour_logging = True, debug_mode = False):
		self.devnull = None
		self.dsp_play = None
		self.dsp_record = None
		
		
		self.AUDIO_CHANNELS = 1
		self.AUDIO_SAMPLERATE = 8000
		self.AUDIO_SPS = (self.AUDIO_CHANNELS * self.AUDIO_SAMPLERATE) * 2 # 2x for 16bit
		self.COLOUR_LOGGING = colour_logging
		self.DSP_PLAY_DEVICE = dsp_play_device
		self.DSP_RECORD_DEVICE = dsp_record_device
		self.DEBUG_MODE = debug_mode
		self.MODEM_BPS = 174 # 1400 / 8 (48 bit frames)
		self.PREAMPLE = "\xcc"
		self.RTS_STATE = False
		
		
		from danlog import DanLog
		
		self.log = DanLog("FDMDV")
		
		
		self.log.warn("")
		self.log.warn("***************************************************************")
		self.log.warn("* This is a very experimental feature, expect plenty of bugs! *")
		self.log.warn("***************************************************************")
		self.log.warn("")
		self.log.info("Initialising the FDMDV modem (provided by Codec2)...")
		
		
		
		import ossaudiodev
		
		
		if self.DEBUG_MODE:
			self.log.info("Setting up DSP device \"%s\" for recording..." % self.DSP_RECORD_DEVICE)
		
		self.dsp_record = ossaudiodev.open(self.DSP_RECORD_DEVICE, "r")
		self.dsp_record.setfmt(ossaudiodev.AFMT_S16_LE)
		self.dsp_record.channels(self.AUDIO_CHANNELS)
		self.dsp_record.speed(self.AUDIO_SAMPLERATE)
		
		
		if self.DEBUG_MODE:
			self.log.info("Setting up DSP device \"%s\" for playback..." % self.DSP_PLAY_DEVICE)
		
		self.dsp_play = ossaudiodev.open(self.DSP_PLAY_DEVICE, "w")
		self.dsp_play.setfmt(ossaudiodev.AFMT_S16_LE)
		self.dsp_play.channels(self.AUDIO_CHANNELS)
		self.dsp_play.speed(self.AUDIO_SAMPLERATE)
		
		
		self.log.info("OSS module imported and configured successfully.")
		
		
		# Setup anything else we need
		self.devnull = open(os.devnull, "wb")
		
		
		if self.DEBUG_MODE:
			self.log.info("Modem can handle %d bytes per second." % self.MODEM_BPS)
	
	def decodeData(self, data):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		d = subprocess.Popen(["./fdmdv_demod", "-", "-"], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = False)
		
		if d is not None:
			r = d.communicate(data)
			d.wait()
			
			return r[0]
	
	def encodeData(self, data):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		d = subprocess.Popen(["./fdmdv_mod", "-", "-"], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = False)
		
		if d is not None:
			r = d.communicate(data)
			d.wait()
			
			return r[0]
	
	def generatePreample(self, bytesneeded = 28, character = "\xcc"):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		return character * bytesneeded
	
	def getState(self):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		return self.RTS_STATE
	
	def padData(self, data, blocksize = 174):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		dlen = len(str(data))
		
		major = dlen / blocksize
		minor = (dlen % blocksize) + 1 # Exact blocksizes causes data to be clipped
		
		blocks = major
		
		if minor > 0:
			blocks += 1
		
		
		if self.DEBUG_MODE:
			self.log.info("%d %d-blocks required for %d bytes of data." % (blocks, blocksize, dlen))
		
		return str(data).center(blocks * blocksize, "\xcc")
	
	def playData(self, data):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		self.dsp_play.write(data)
	
	def transmitPacket(self, data):
		if self.DEBUG_MODE:
			self.log.info("Running...")
		
		
		# Appears the modem takes a while to sync as well as trimming the data
		d = bytearray()
		d.extend(self.generatePreample(10))
		d.extend(data)
		d.extend(self.generatePreample(30))
		
		p = str(d)
		e = self.encodeData(p)
		
		if self.DEBUG_MODE:
			self.log.info("Transmitting raw packet %s (%d bytes)..." % (repr(p), len(p)))
		
		
		# Time how long it should take to transmit the data and wait accordingly
		starttime = time.time()
		
		self.RTS_STATE = True
		self.playData(e)
		
		finishtime = time.time()
		
		
		dlen = float(len(p))
		timeneeded = (dlen / self.MODEM_BPS)
		timetaken = (finishtime - starttime)
		
		if self.DEBUG_MODE:
			self.log.info("Data length: %d, BPS: %d, Time required: %.5f, Time taken: %.5f" % (dlen, self.MODEM_BPS, timeneeded, timetaken))
		
		
		p = round(timeneeded - timetaken, 3)
		
		if p > 0.:
			if self.DEBUG_MODE:
				self.log.info("Waiting for %.3f seconds for data to be played..." % p)
			
			time.sleep(p)
		
		
		self.RTS_STATE = False

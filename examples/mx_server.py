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
import sqlite3
import sys
import time
from xml.dom import minidom


###########
# Globals #
###########
conn = None

log = DanLog("MXServer")


#############
# Constants #
#############
ALLOW_UNSIGNED_PACKETS = False

BACKEND_DATAMODE = "PSK500R"
BACKEND_HOSTNAME = "localhost"
BACKEND_PORT = 7362

CW_BEACON_TEXT = "CHANGEME"

DB_VERSION = 1000
DEBUG_MODE = False
DISABLE_CRYPTO = False

MX_CALLSIGN = "CHANGEME"

SPECIFICATION = 0

USE_TCP = 0

XML_SETTINGS_FILE = "mxserver-settings.xml"


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

def connectToDatabase():
	global conn
	
	
	conn = sqlite3.connect("mxserver.dbl")

def danLookup(strfield, strtable, strwhere):
	global conn
	
	
	strsql = ""
	
	if strwhere == "":
		strsql = "SELECT %s FROM %s" % (strfield, strtable)
		
	else:
		strsql = "SELECT %s FROM %s WHERE %s" % (strfield, strtable, strwhere)
	
	
	try:
		cur = conn.cursor()
		cur.execute(strsql)
		
		return cur.fetchone()[0]
		
	except Exception, ex:
		if DEBUG_MODE:
			log.fatal("SQLite: %s" % str(ex))
		
		return None

def disconnectFromDatabase():
	global conn
	
	
	if conn is not None:
		conn.close()

def escapeString(strin):
	return strin.replace("'", "\\'")

def executeSQLCommand(strsql, parameters = ()):
	global conn
	
	
	try:
		strsql = strsql.replace("NOT NULL", "").replace("START TRANSACTION", "BEGIN TRANSACTION")
		
		cur = conn.cursor()
		cur.execute(strsql, parameters)
		
		conn.commit()
		
		return True
		
	except Exception, ex:
		if DEBUG_MODE:
			log.fatal("SQLite: %s" % str(ex))
		
		return False

def executeSQLQuery(strsql, parameters = ()):
	global conn
	
	
	try:
		cur = conn.cursor()
		return cur.execute(strsql, parameters)
		
	except Exception, ex:
		if DEBUG_MODE:
			log.fatal("SQLite: %s" % str(ex))
		
		return None

def exitProgram():
	disconnectFromDatabase()
	
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
	log.info("Mail Exchanger - Server")
	log.info("=======================")
	log.info("Checking settings...")
	
	if os.path.exists(XML_SETTINGS_FILE) == False:
		log.warn("The XML settings file doesn't exist, create one...")
		
		xmlMXSettingsWrite()
		
		
		log.info("The XML settings file has been created using the default settings.  Please edit it and restart the MX server once you're happy with the settings.")
		
		exitProgram()
		
	else:
		log.info("Reading XML settings...")
		
		xmlMXSettingsRead()
		
		# This will ensure it will have any new settings in
		if os.path.exists(XML_SETTINGS_FILE + ".bak"):
			os.unlink(XML_SETTINGS_FILE + ".bak")
			
		os.rename(XML_SETTINGS_FILE, XML_SETTINGS_FILE + ".bak")
		xmlMXSettingsWrite()
	
	
	log.info("Checking the config...")
	
	if MX_CALLSIGN == "" or MX_CALLSIGN == "CHANGEME":
		log.error("The MX server callsign is invalid.  Please edit the config XML file.")
		exitProgram()
	
	if CW_BEACON_TEXT == "" or CW_BEACON_TEXT == "CHANGEME":
		log.error("The CW beacon text is invalid.  Please edit the config XML file.")
		exitProgram()
	
	
	log.info("Setting up database...")
	connectToDatabase()
	updateDatabase()
	
	
	log.info("Setting up DDP...")
	ddp = DDP(hostname = BACKEND_HOSTNAME, port = BACKEND_PORT, data_mode = BACKEND_DATAMODE, timeout = 60., ack_timeout = 30., tx_hangtime = 1.25, data_length = 512, specification = SPECIFICATION, disable_ec = False, disable_crypto = DISABLE_CRYPTO, allow_unsigned_packets = ALLOW_UNSIGNED_PACKETS, application = "DDP Example: MX", ignore_broadcast_packets = True, debug_mode = DEBUG_MODE)
	
	ddp.setCallsign(MX_CALLSIGN)
	
	
	log.info("Waiting for a packet...")
	
	starttime = time.time()
	
	while True:
		try:
			data = ddp.receiveDataFromAny(MX_CALLSIGN)
			
			if data is not None:
				# Check the flags
				d = data[0]
				packet = data[1]
				
				if d == "RETRIEVE":
					log.info("%s requested their emails." % packet[ddp.SECTION_SOURCE])
					
					msg = executeSQLQuery("SELECT Subject, Message, [From], DateTimeOfEmail FROM tblEmails WHERE [To] = ? AND DateTimeOfRetrieval IS NULL ORDER BY ID", (packet[ddp.SECTION_SOURCE],))
					
					if msg is not None:
						tosend = ""
						
						for row in msg:
							msg_subject = row[0]
							msg_message = ddp.encodeStreamToBase128(row[1], 0, True)
							msg_from = row[2]
							msg_date = row[3]
							
							tosend += "%s%s%s%s%s%s%s\n" % (msg_subject, chr(27), msg_message, chr(27), msg_from, chr(27), msg_date)
						
						if ddp.transmitData(MX_CALLSIGN, "", packet[ddp.SECTION_SOURCE], tosend, USE_TCP, 1):
							executeSQLCommand("UPDATE tblEmails SET DateTimeOfRetrieval = ? WHERE [To] = ? AND DateTimeOfRetrieval IS NULL", (sqlDateTime(), packet[ddp.SECTION_SOURCE],))
						
						
						log.info("%s should now all the emails." % packet[ddp.SECTION_SOURCE])
						
					else:
						log.info("Unable to send the emails to %s due to no data." % packet[ddp.SECTION_SOURCE])
					
				elif d.startswith("SEND"):
					log.info("%s is sending a new email." % packet[ddp.SECTION_SOURCE])
					
					
					rx = ddp.receiveData(MX_CALLSIGN, packet[ddp.SECTION_SOURCE])
					
					if rx is not None:
						data = rx[0]
						
						if len(data) > 0:
							lines = data.split("\n")
							
							if len(lines) == 4:
								# We have something to post
								msg_to = escapeString(lines[0])
								msg_subject = escapeString(lines[1])
								msg_message = escapeString(ddp.decodeBase128ToStream(lines[2], 0, True))
								msg_from = escapeString(packet[ddp.SECTION_SOURCE])
								msg_date = sqlDateTime()
								
								
								log.info("New email from %s..." % packet[ddp.SECTION_SOURCE])
								
								if executeSQLCommand("INSERT INTO tblEmails(Subject, Message, [From], [To], DateTimeOfEmail, DateTimeOfRetrieval) VALUES(?, ?, ?, ?, ?, NULL)", (msg_subject, msg_message, msg_from, msg_to, msg_date,)):
									log.info("A new message has been sent by %s." % packet[ddp.SECTION_SOURCE])
									
								else:
									log.warn("Unable to write out the email from %s." % packet[ddp.SECTION_SOURCE])
								
							else:
								log.warn("It appears the email is incomplete from %s." % packet[ddp.SECTION_SOURCE])
							
						else:
							log.warn("There appears to be nothing in the data from %s." % packet[ddp.SECTION_SOURCE])
						
					else:
						log.warn("Unable to email from %s as nothing was received." % packet[ddp.SECTION_SOURCE])
				
			else:
				endtime = time.time()
				
				if (endtime - starttime) >= 300.:
					log.info("Nothing received in 5 minutes, transmitting beacon text via CW...")
					starttime = time.time()
					
					ddp.cw(CW_BEACON_TEXT)
					
					log.info("Listening for packets again...")
				
		except KeyboardInterrupt:
			break
			
		except Exception, ex:
			log.fatal(ex)
	
	
	log.info("Cleaning up...")
	ddp.dispose()
	ddp = None
	
	log.info("Exiting...")
	exitProgram()

def sqlDateTime():
	t = datetime.now()
	
	return str(t.strftime("%Y/%m/%d %H:%M:%S"))

def updateDatabase():
	global conn
	
	
	##########
	# Tables #
	##########
	executeSQLCommand("START TRANSACTION")
	
	executeSQLCommand("CREATE TABLE tblEmails(ID integer PRIMARY KEY)")
	executeSQLCommand("ALTER TABLE tblEmails ADD COLUMN Subject nvarchar(100) NOT NULL")
	executeSQLCommand("ALTER TABLE tblEmails ADD COLUMN Message nvarchar(4096) NOT NULL")
	executeSQLCommand("ALTER TABLE tblEmails ADD COLUMN [From] nvarchar(10) NOT NULL")
	executeSQLCommand("ALTER TABLE tblEmails ADD COLUMN [To] nvarchar(10) NOT NULL")
	executeSQLCommand("ALTER TABLE tblEmails ADD COLUMN DateTimeOfEmail datetime NOT NULL")
	executeSQLCommand("ALTER TABLE tblEmails ADD COLUMN DateTimeOfRetrieval datetime NULL")
	
	
	# tblSystem
	executeSQLCommand("CREATE TABLE tblSystem(ID integer PRIMARY KEY)")
	executeSQLCommand("ALTER TABLE tblSystem ADD COLUMN DatabaseVersion int NOT NULL")
	
	rowcount = int(ifNoneReturnZero(danLookup("COUNT(ID)", "tblSystem", "")))
	
	if rowcount == 0:
		# First time, create the row
		cur = conn.cursor()
		cur.execute("INSERT INTO tblSystem(DatabaseVersion) VALUES(0)")
		
		conn.commit()
	
	
	###########
	# Updates #
	###########
	curr_db_version = int(ifNoneReturnZero(danLookup("DatabaseVersion", "tblSystem", "")))
	
	if curr_db_version < DB_VERSION:
		# Update needed
		
		
		# Finally, update the db version
		executeSQLCommand("UPDATE tblSystem SET DatabaseVersion = %d" % DB_VERSION)
	
	executeSQLCommand("COMMIT")

def xmlMXSettingsRead():
	global ALLOW_UNSIGNED_PACKETS, BACKEND_DATAMODE, BACKEND_HOSTNAME, BACKEND_PORT, CW_BEACON_TEXT, DEBUG_MODE, DISABLE_CRYPTO, MX_CALLSIGN, SPECIFICATION, USE_TCP
	
	
	if os.path.exists(XML_SETTINGS_FILE):
		xmldoc = minidom.parse(XML_SETTINGS_FILE)
		
		myvars = xmldoc.getElementsByTagName("Setting")
		
		for var in myvars:
			for key in var.attributes.keys():
				val = str(var.attributes[key].value)
				
				# Now put the correct values to correct key
				if key == "ServerCallsign":
					MX_CALLSIGN = val
					
				elif key == "CWBeaconText":
					CW_BEACON_TEXT = val.upper()
					
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
					
				else:
					log.warn("XML setting attribute \"%s\" isn't known.  Ignoring..." % key)

def xmlMXSettingsWrite():
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
		var.setAttribute("ServerCallsign", str(MX_CALLSIGN))
		settings.appendChild(var)
		
		var = xmldoc.createElement("Setting")
		var.setAttribute("CWBeaconText", str(CW_BEACON_TEXT))
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

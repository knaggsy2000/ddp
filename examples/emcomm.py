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
import threading
from xml.dom import minidom


#############
# Variables #
#############
client_callsign = ""
conn = None

ddp = None

log = DanLog("EmComm")

rxalive = False


#############
# Constants #
#############
ALLOW_UNSIGNED_PACKETS = False

BACKEND_DATAMODE = "PSK500R"
BACKEND_HOSTNAME = "localhost"
BACKEND_PORT = 7362

DB_VERSION = 1000
DEBUG_MODE = False
DISABLE_CRYPTO = False

SPECIFICATION = 0

USE_TCP = 0

XML_SETTINGS_FILE = "emcomm-settings.xml"


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
	
	
	conn = sqlite3.connect("emcomm.dbl", check_same_thread = False)

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
			log.fatal(ex)
		
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
		strsql = strsql.replace("NOT NULL","").replace("START TRANSACTION", "BEGIN TRANSACTION")
		
		cur = conn.cursor()
		cur.execute(strsql, parameters)
		
		conn.commit()
		
		return True
		
	except Exception, ex:
		if DEBUG_MODE:
			log.fatal(ex)
		
		return False

def executeSQLQuery(strsql, parameters = ()):
	global conn
	
	
	try:
		cur = conn.cursor()
		return cur.execute(strsql, parameters)
		
	except Exception, ex:
		if DEBUG_MODE:
			log.fatal(ex)
		
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
	global client_callsign, ddp, rxalive
	
	
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
	log.info("EmComm")
	log.info("======")
	log.info("Checking settings...")
	
	if os.path.exists(XML_SETTINGS_FILE) == False:
		log.warn("The XML settings file doesn't exist, create one...")
		
		xmlEMCOMMSettingsWrite()
		
		
		log.info("The XML settings file has been created using the default settings.  Please edit it and restart EmComm once you're happy with the settings.")
		
		exitProgram()
		
	else:
		log.info("Reading XML settings...")
		
		xmlEMCOMMSettingsRead()
		
		# This will ensure it will have any new settings in
		if os.path.exists(XML_SETTINGS_FILE + ".bak"):
			os.unlink(XML_SETTINGS_FILE + ".bak")
			
		os.rename(XML_SETTINGS_FILE, XML_SETTINGS_FILE + ".bak")
		xmlEMCOMMSettingsWrite()
	
	
	log.info("Setting up database...")
	connectToDatabase()
	updateDatabase()
	
	
	log.info("Setting up DDP...")
	ddp = DDP(hostname = BACKEND_HOSTNAME, port = BACKEND_PORT, data_mode = BACKEND_DATAMODE, timeout = 60., ack_timeout = 30., tx_hangtime = 1.25, data_length = 512, specification = SPECIFICATION, disable_ec = False, disable_crypto = DISABLE_CRYPTO, allow_unsigned_packets = ALLOW_UNSIGNED_PACKETS, application = "DDP Example: EmComm", ignore_broadcast_packets = True, debug_mode = DEBUG_MODE)
	
	
	log.info("")
	log.info("Starting background RX thread...")
	rxalive = True
	
	
	rxthread = threading.Thread(target = rxLoop)
	rxthread.setDaemon(1)
	rxthread.start()
	
	
	log.info("")
	
	while client_callsign == "":
		log.info("Please enter your callsign: ", newline = False)
		
		client_callsign = readInput().strip().upper()
	
	
	log.info("")
	log.info("Type ? for commands.")
	log.info("")
	
	while True:
		try:
			log.info("")
			log.info("EMCOMM# ", newline = False)
			
			c = readInput().strip()
			cs = c.split(" ")
			
			log.info("")
			
			if cs[0] == "?":
				log.info("Help")
				log.info("====")
				log.info("i N           Read inbound message N, if N is omitted a list is shown")
				log.info("o N           Read outbound message N, if N is omitted a list is shown")
				log.info("ri N          Re-transmit inbound message N")
				log.info("ro N          Re-transmit outbound message N")
				log.info("p             Post a new message")
				log.info("q             Quit the program")
				
			elif cs[0] == "p":
				try:
					log.info("")
					log.info("Press CTRL+C to abort the message if you make a mistake.")
					
					
					message_id = 0
					message_to = ""
					message_to_position = ""
					message_from = ""
					message_from_position = ""
					message_subject = ""
					message_datetime = sqlDateTime()
					message_message = ""
					message_radio_operator = ""
					
					while message_to == "":
						log.info("To: ", newline = False)
						
						message_to = readInput().strip()
					
					while message_to_position == "":
						log.info("To Position: ", newline = False)
						
						message_to_position = readInput().strip()
					
					while message_from == "":
						log.info("From: ", newline = False)
						
						message_from = readInput().strip()
					
					while message_from_position == "":
						log.info("From Position: ", newline = False)
						
						message_from_position = readInput().strip()
					
					while message_subject == "":
						log.info("Subject: ", newline = False)
						
						message_subject = readInput().strip()
					
					log.info("Please enter the message, just enter a \".\" and it's own line then press ENTER to end.")
					log.info("Message: ", newline = False)
					
					while True:
						m = readInput().strip()
						
						if m == ".":
							break
							
						else:
							message_message += m + "\n"
					
					
					while message_radio_operator == "":
						log.info("Radio Operator: ", newline = False)
						
						message_radio_operator = readInput().strip()
					
					
					# Show the message to the user before sending
					log.info("")
					log.info("To:             %s" % message_to)
					log.info("To Position:    %s" % message_to_position)
					log.info("From:           %s" % message_from)
					log.info("From Position:  %s" % message_from_position)
					log.info("")
					log.info("Subject:        %s" % message_subject)
					log.info("Radio Operator: %s" % message_radio_operator)
					log.info("")
					log.info("Message:        %s" % message_message)
					log.info("")
					
					
					answer = ""
					
					while True:
						log.info("Do you want to send this message? (Y/N): ", newline = False)
						answer = readInput().strip().upper()
						
						if answer == "Y" or answer == "N":
							break
					
					log.info("")
					
					if answer == "Y":
						log.info("Storing message in database...")
						
						
						p = (message_from, message_from_position, message_to, message_to_position, message_subject, message_datetime, message_message, message_radio_operator,)
						
						if executeSQLCommand("INSERT INTO tblOutboundMessages([From], FromPosition, [To], ToPosition, Subject, [DateTime], Message, RadioOperator) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", p):
							q = executeSQLQuery("SELECT last_insert_rowid()")
							
							if q is not None:
								for m in q:
									message_id = int(m[0])
									break # Only expecting one
							
							
							if message_id > 0:
								log.info("Sending message (ID %d)..." % message_id)
								
								if ddp.transmitData(client_callsign, "", "EMCOMM", "EMCOMM_MESSAGE", USE_TCP):
									tosend = "%d\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s" % (message_id, message_to, message_to_position, message_from, message_from_position, message_subject, message_datetime, ddp.encodeStreamToBase128(message_message, 0, True), message_radio_operator)
									
									if ddp.transmitData(client_callsign, "", "EMCOMM", tosend, USE_TCP, 1):
										log.info("Message ID %d has been sent successfully." % message_id)
										
									else:
										log.warn("Message has FAILED to be sent.")
									
								else:
									log.warn("Failed to send request.")
								
							else:
								log.warn("Message ID appears to be zero, message cannot be sent.")
							
						else:
							log.warn("Failed to write the message to the database, will not send message.")
						
					else:
						log.warn("The message will not be sent.")
					
				except KeyboardInterrupt:
					break
					
				except Exception, ex:
					log.fatal(ex)
				
			elif cs[0] == "i" or cs[0] == "o":
				if len(cs) <= 1:
					# Display a list of messages
					if cs[0] == "i":
						log.info("Inbound messages: -")
						
					elif cs[0] == "o":
						log.info("Outbound messages: -")
					
					log.info("")
					
					
					msg_id = "ID".rjust(6, " ")
					msg_msgid = "RemoteID".rjust(9, " ")
					msg_from = "From".ljust(20, " ")
					msg_to = "To".ljust(20, " ")
					msg_subject = "Subject".ljust(30, " ")
					msg_date = "Date".ljust(19, " ")
					msg_op = "Operator".ljust(20, " ")
					
					log.info("%s %s %s %s %s %s %s" % (msg_id, msg_msgid, msg_from, msg_to, msg_subject, msg_date, msg_op))
					log.info("=" * 140)
					
					
					q = None
					
					if cs[0] == "i":
						q = executeSQLQuery("SELECT ID, RemoteID, [From], [To], Subject, [DateTime], RadioOperator FROM tblInboundMessages ORDER BY ID DESC")
						
					elif cs[0] == "o":
						q = executeSQLQuery("SELECT ID, '', [From], [To], Subject, [DateTime], RadioOperator FROM tblOutboundMessages ORDER BY ID DESC")
					
					
					for row in q:
						msg_id = str(row[0]).rjust(6, " ")
						msg_msgid = str(row[1]).rjust(9, " ")
						msg_from = row[2][:20].ljust(20, " ")
						msg_to = row[3][:20].ljust(20, " ")
						msg_subject = row[4][:30].ljust(30, " ")
						msg_date = row[5].ljust(19, " ")
						msg_op = row[6][:20].ljust(20, " ")
						
						
						log.info("%s %s %s %s %s %s %s" % (msg_id, msg_msgid, msg_from, msg_to, msg_subject, msg_date, msg_op))
					
				else:
					if cs[1].isalpha() == False:
						# Display the message
						p = (int(cs[1]),)
						q = None
						
						if cs[0] == "i":
							q = executeSQLQuery("SELECT ID, RemoteID, [From], FromPosition, [To], ToPosition, Subject, [DateTime], Message, RadioOperator FROM tblInboundMessages WHERE ID = ?", p)
							
						elif cs[0] == "o":
							q = executeSQLQuery("SELECT ID, '', [From], FromPosition, [To], ToPosition, Subject, [DateTime], Message, RadioOperator FROM tblOutboundMessages WHERE ID = ?", p)
						
						for row in q:
							log.info("ID:             %s" % row[0])
							log.info("RemoteID:       %s" % row[1])
							log.info("")
							log.info("To:             %s" % row[4])
							log.info("To Position:    %s" % row[5])
							log.info("")
							log.info("From:           %s" % row[2])
							log.info("From Position:  %s" % row[3])
							log.info("")
							log.info("Subject:        %s" % row[6])
							log.info("Date:           %s" % row[7])
							log.info("")
							log.info("Radio Operator: %s" % row[9])
							log.info("")
							log.info("Message:        %s" % row[8])
						
					else:
						log.warn("You haven't entered a number for the message number.")
			
			elif cs[0] == "ri" or cs[0] == "ro":
				if len(cs) <= 1:
					log.warn("You must specify the message ID to re-transmit.")
					
				else:
					# Retransmit the message
					p = (int(cs[1]),)
					q = None
					
					if cs[0] == "ri":
						q = executeSQLQuery("SELECT ID, RemoteID, [From], FromPosition, [To], ToPosition, Subject, [DateTime], Message, RadioOperator FROM tblInboundMessages WHERE ID = ?", p)
						
					elif cs[0] == "ro":
						q = executeSQLQuery("SELECT ID, '', [From], FromPosition, [To], ToPosition, Subject, [DateTime], Message, RadioOperator FROM tblOutboundMessages WHERE ID = ?", p)
					
					for row in q:
						message_id = 0
						message_to = row[4]
						message_to_position = row[5]
						message_from = row[2]
						message_from_position = row[3]
						message_subject = "RT: " + str(row[6])
						message_datetime = sqlDateTime()
						message_message = "*** This is a re-transmitted message ID " + str(row[0]) + " on " + str(row[7]) + " ***\n\n" + str(row[8])
						message_radio_operator = row[9]
						
						
						answer = ""
						
						while True:
							log.info("Are you sure you want to re-transmit this message? (Y/N): ", newline = False)
							answer = readInput().strip().upper()
							
							if answer == "Y" or answer == "N":
								break
						
						log.info("")
						
						if answer == "Y":
							log.info("Storing message in database...")
							
							
							p = (message_from, message_from_position, message_to, message_to_position, message_subject, message_datetime, message_message, message_radio_operator,)
							
							if executeSQLCommand("INSERT INTO tblOutboundMessages([From], FromPosition, [To], ToPosition, Subject, [DateTime], Message, RadioOperator) VALUES(?, ?, ?, ?, ?, ?, ?, ?)", p):
								q = executeSQLQuery("SELECT last_insert_rowid()")
								
								if q is not None:
									for m in q:
										message_id = int(m[0])
										break # Only expecting one
								
								
								if message_id > 0:
									log.info("Re-transmitting message (ID %d)..." % message_id)
									
									if ddp.transmitData(client_callsign, "", "EMCOMM", "EMCOMM_MESSAGE", USE_TCP):
										tosend = "%d\n%s\n%s\n%s\n%s\n%s\n%s\n%s\n%s" % (message_id, message_to, message_to_position, message_from, message_from_position, message_subject, message_datetime, ddp.encodeStreamToBase128(message_message, 0, True), message_radio_operator)
										
										if ddp.transmitData(client_callsign, "", "EMCOMM", tosend, USE_TCP, 1):
											log.info("Message ID %d has been re-transmitted successfully." % message_id)
											
										else:
											log.warn("Message has FAILED to be re-transmitted.")
										
									else:
										log.warn("Failed to send request.")
									
								else:
									log.warn("Message ID appears to be zero, message cannot be re-transmitted.")
								
							else:
								log.warn("Failed to write the message to the database, will not send re-transmitted.")
							
						else:
							log.warn("The message will not be re-transmitted.")
						
						break # Only expecting one
			
			elif cs[0] == "q":
				break
			
		except KeyboardInterrupt:
			break
			
		except Exception, ex:
			log.fatal(ex)
	
	rxalive = False
	
	
	log.info("Cleaning up...")
	ddp.dispose()
	ddp = None
	
	log.info("Exiting...")
	sys.exit(0)

def readInput():
	return sys.stdin.readline().replace("\r", "").replace("\n", "")

def rxLoop():
	global ddp, rxalive
	
	
	while rxalive:
		try:
			data = ddp.receiveDataFromAny("EMCOMM")
			
			if data is not None:
				# Check the flags
				d = data[0]
				packet = data[1]
				
				
				if d == "EMCOMM_MESSAGE":
					rx = ddp.receiveData(packet[ddp.SECTION_DESTINATION], packet[ddp.SECTION_SOURCE])
					
					if rx is not None:
						rxdata = rx[0]
						
						if len(rxdata) > 0:
							# Store the message in the database for reading
							r = rxdata.split("\n")
							
							if len(r) == 9:
								p = (r[0], r[1], r[2], r[3], r[4], r[5], r[6], ddp.decodeBase128ToStream(r[7], 0, True), r[8],)
								
								if executeSQLCommand("INSERT INTO tblInboundMessages(RemoteID, [To], ToPosition, [From], FromPosition, Subject, [DateTime], Message, RadioOperator) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", p):
									message_id = 0
									q = executeSQLQuery("SELECT last_insert_rowid()")
									
									if q is not None:
										for m in q:
											message_id = int(m[0])
											break # Only expecting one
									
									
									if message_id > 0:
										log.info("")
										log.info("*******************************")
										log.info("*** EMCOMM MESSAGE RECEIVED ***")
										log.info("*******************************")
										log.info("")
										log.info("Message ID: %d (remote ID %d)" % (message_id, int(r[0])))
										log.info("")
										
									else:
										log.warn("The message ID appears to be zero.")
									
								else:
									log.warn("Failed to write inbound message to the database from %s." % packet[ddp.SECTION_SOURCE])
								
							else:
								log.warn("Incomplete message received from %s." % packet[ddp.SECTION_SOURCE])
							
						else:
							log.warn("There appears to be nothing in the data from %s." % packet[ddp.SECTION_SOURCE])
						
					else:
						log.warn("Unable to receive the message from %s as nothing was received." % packet[ddp.SECTION_SOURCE])
					
				else:
					log.warn("The packet received isn't valid for this program.")
					
			else:
				log.warn("No packets have been received.")
			
		except Exception, ex:
			log.fatal(ex)

def sqlDateTime():
	t = datetime.now()
	
	return str(t.strftime("%Y/%m/%d %H:%M:%S"))

def updateDatabase():
	global conn
	
	
	##########
	# Tables #
	##########
	executeSQLCommand("START TRANSACTION")
	
	executeSQLCommand("CREATE TABLE tblInboundMessages(ID integer PRIMARY KEY)")
	executeSQLCommand("ALTER TABLE tblInboundMessages ADD COLUMN RemoteID integer NOT NULL")
	executeSQLCommand("ALTER TABLE tblInboundMessages ADD COLUMN [From] nvarchar(10) NOT NULL")
	executeSQLCommand("ALTER TABLE tblInboundMessages ADD COLUMN FromPosition nvarchar(50) NOT NULL")
	executeSQLCommand("ALTER TABLE tblInboundMessages ADD COLUMN [To] nvarchar(100) NOT NULL")
	executeSQLCommand("ALTER TABLE tblInboundMessages ADD COLUMN ToPosition nvarchar(50) NOT NULL")
	executeSQLCommand("ALTER TABLE tblInboundMessages ADD COLUMN Subject nvarchar(100) NOT NULL")
	executeSQLCommand("ALTER TABLE tblInboundMessages ADD COLUMN [DateTime] datetime NOT NULL")
	executeSQLCommand("ALTER TABLE tblInboundMessages ADD COLUMN Message nvarchar(1024) NOT NULL")
	executeSQLCommand("ALTER TABLE tblInboundMessages ADD COLUMN RadioOperator nvarchar(100) NOT NULL")
	
	executeSQLCommand("CREATE TABLE tblOutboundMessages(ID integer PRIMARY KEY)")
	executeSQLCommand("ALTER TABLE tblOutboundMessages ADD COLUMN [From] nvarchar(10) NOT NULL")
	executeSQLCommand("ALTER TABLE tblOutboundMessages ADD COLUMN FromPosition nvarchar(50) NOT NULL")
	executeSQLCommand("ALTER TABLE tblOutboundMessages ADD COLUMN [To] nvarchar(100) NOT NULL")
	executeSQLCommand("ALTER TABLE tblOutboundMessages ADD COLUMN ToPosition nvarchar(50) NOT NULL")
	executeSQLCommand("ALTER TABLE tblOutboundMessages ADD COLUMN Subject nvarchar(100) NOT NULL")
	executeSQLCommand("ALTER TABLE tblOutboundMessages ADD COLUMN [DateTime] datetime NOT NULL")
	executeSQLCommand("ALTER TABLE tblOutboundMessages ADD COLUMN Message nvarchar(1024) NOT NULL")
	executeSQLCommand("ALTER TABLE tblOutboundMessages ADD COLUMN RadioOperator nvarchar(100) NOT NULL")
	
	
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

def xmlEMCOMMSettingsRead():
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

def xmlEMCOMMSettingsWrite():
	if os.path.exists(XML_SETTINGS_FILE) == False:
		xmloutput = file(XML_SETTINGS_FILE, "w")
		
		
		xmldoc = minidom.Document()
		
		# Create header
		settings = xmldoc.createElement("EmComm")
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

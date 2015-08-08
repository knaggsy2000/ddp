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
import sqlite3
import sys
from xml.dom import minidom


###########
# Globals #
###########
conn = None

log = DanLog("MXClient")


#############
# Variables #
#############
client_callsign = ""
server_callsign = ""


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

XML_SETTINGS_FILE = "mxclient-settings.xml"


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
	
	
	conn = sqlite3.connect("mxclient.dbl")

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
	log.info("Mail Exchanger - Client")
	log.info("=======================")
	log.info("Checking settings...")
	
	if os.path.exists(XML_SETTINGS_FILE) == False:
		log.warn("The XML settings file doesn't exist, create one...")
		
		xmlMXSettingsWrite()
		
		
		log.info("The XML settings file has been created using the default settings.  Please edit it and restart the MX client once you're happy with the settings.")
		
		exitProgram()
		
	else:
		log.info("Reading XML settings...")
		
		xmlMXSettingsRead()
		
		# This will ensure it will have any new settings in
		if os.path.exists(XML_SETTINGS_FILE + ".bak"):
			os.unlink(XML_SETTINGS_FILE + ".bak")
			
		os.rename(XML_SETTINGS_FILE, XML_SETTINGS_FILE + ".bak")
		xmlMXSettingsWrite()
	
	
	log.info("Setting up database...")
	connectToDatabase()
	updateDatabase()
	
	
	log.info("Setting up DDP...")
	ddp = DDP(hostname = BACKEND_HOSTNAME, port = BACKEND_PORT, data_mode = BACKEND_DATAMODE, timeout = 60., ack_timeout = 30., tx_hangtime = 1.25, data_length = 512, specification = SPECIFICATION, disable_ec = False, disable_crypto = DISABLE_CRYPTO, allow_unsigned_packets = ALLOW_UNSIGNED_PACKETS, application = "DDP Example: MX", ignore_broadcast_packets = True, debug_mode = DEBUG_MODE)
	
	
	log.info("")
	log.info("Type ? for commands.")
	log.info("")
	
	while True:
		try:
			log.info("")
			log.info("MX# ", newline = False)
			
			c = readInput().strip()
			cs = c.split(" ")
			
			log.info("")
			
			if cs[0] == "?":
				log.info("Help")
				log.info("====")
				log.info("f CALLSIGN    Connects to MX server named CALLSIGN and fetches all of your unread emails")
				log.info("r N           Read message N, if N is omitted then your mailbox list will be shown")
				log.info("s             Send a email")
				log.info("q             Quit the program")
				
			elif cs[0] == "f":
				if len(cs) == 2:
					server_callsign = cs[1].strip().upper()
				
				
				if server_callsign == "":
					log.info("Please enter the MX server callsign: ", newline = False)
					
					server_callsign = readInput().strip().upper()
					log.info("")
				
				if client_callsign == "":
					log.info("Please enter your callsign: ", newline = False)
					
					client_callsign = readInput().strip().upper()
					log.info("")
				
				
				if server_callsign <> "" and client_callsign <> "":
					ddp.setCallsign(client_callsign)
					
					
					log.info("")
					log.info("Requesting emails...")
					
					if ddp.transmitData(client_callsign, "", server_callsign, "RETRIEVE", USE_TCP, 0):
						log.info("Receiving data...")
						data = ddp.receiveData(client_callsign, server_callsign)
						
						em = 0
						
						if data is not None:
							msgs = data[0].split("\n")
							
							for msg in msgs:
								if len(msg) > 0:
									line = msg.split(chr(27))
									
									msg_subject = line[0]
									msg_message = ddp.decodeBase128ToStream(line[1], 0, True)
									msg_from = line[2]
									msg_date = line[3]
									
									
									if executeSQLCommand("INSERT INTO tblEmails(Subject, Message, [From], [To], DateTimeOfEmail) VALUES(?, ?, ?, ?, ?)", (msg_subject, msg_message, msg_from, client_callsign, msg_date,)):
										em += 1
										
									else:
										log.warn("Email failed to write into the database.")
							
							log.info("%d/%d emails have been downloaded successfully." % (em, len(msgs) - 1))
							
						else:
							log.warn("Nothing received, prehaps you have no emails waiting?")
						
					else:
						log.warn("Failed to send request.")
					
				else:
					if server_callsign == "":
						log.warn("No MX server callsign entered.")
					
					if client_callsign == "":
						log.warn("Your callsign hasn't been entered.")
				
			elif cs[0] == "s":
				to = ""
				subject = ""
				message = ""
				
				if server_callsign == "":
					log.info("Please enter the MX server callsign: ", newline = False)
					
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
				log.info("Do you want to send this email? (Y/N): ", newline = False)
				
				answer = readInput().strip().upper()
				log.info("")
				
				if answer == "Y":
					log.info("Sending email...")
					
					if ddp.transmitData(client_callsign, "", server_callsign, "SEND", USE_TCP):
						tosend = "%s\n%s\n%s\n" % (to, subject, ddp.encodeStreamToBase128(message, 0, True))
						
						if ddp.transmitData(client_callsign, "", server_callsign, tosend, USE_TCP, 1):
							log.info("Email has been sent to the server.")
							
						else:
							log.warn("Email has NOT been sent to the server.")
						
					else:
						log.warn("Failed to send request.")
					
				else:
					log.warn("The email will not be sent.")
				
			elif cs[0] == "r":
				if len(cs) == 1:
					msg = executeSQLQuery("SELECT ID, SUBSTR(Subject, 1, 30) AS Subject, SUBSTR(Message, 1, 30) AS Message, [From], DateTimeOfEmail FROM tblEmails ORDER BY DateTimeOfEmail DESC")
					
					if msg is not None:
						# Display the messages
						msg_id = "ID".rjust(9, " ")
						msg_from = "From".ljust(10, " ")
						msg_subject = "Subject".ljust(30, " ")
						msg_message = "Message".ljust(30, " ")
						msg_date = "Date".ljust(19, " ")
						
						log.info("")
						log.info("%s %s %s %s %s" % (msg_id, msg_from, msg_subject, msg_message, msg_date))
						log.info("=" * 102)
						
						for row in msg:
							msg_id = str(row[0]).rjust(9, " ")
							msg_subject = row[1].ljust(30, " ")
							msg_message = row[2].ljust(30, " ").replace("\n", " ")
							msg_from = row[3].ljust(10, " ")
							msg_date = row[4].ljust(19, " ")
							
							log.info("%s %s %s %s %s" % (msg_id, msg_from, msg_subject, msg_message, msg_date))
					
				elif len(cs) == 2:
					if cs[1].isalpha() == False:
						msg = executeSQLQuery("SELECT ID, Subject, Message, [From], DateTimeOfEmail FROM tblEmails WHERE ID = ?", (int(cs[1]),))
						
						if msg is not None:
							for row in msg:
								log.info("ID:      %s" % row[0])
								log.info("From:    %s" % row[3])
								log.info("Posted:  %s" % row[4])
								log.info("Subject: %s" % row[1])
								log.info("Message: %s" % row[2])
								break
						
					else:
						log.warn("You haven't entered a number for the email number.")
				
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

def xmlMXSettingsWrite():
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

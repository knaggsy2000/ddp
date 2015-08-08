#!/usr/bin/env python
# -*- coding: utf-8 -*-

#########################################################################
# Copyright/License Notice (BSD License)                                #
#########################################################################
#########################################################################
# Copyright (c) 2012, Daniel Knaggs                                     #
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


###########
# Classes #
###########
class DanLog():
	def __init__(self, header, file_appender = False, colour_logging = True):
		from datetime import datetime
		
		import inspect
		import sys
		
		
		self.datetime = datetime
		self.inspect = inspect
		self.sys = sys
		
		
		self.file_appender = file_appender
		
		
		self.COLOUR_LOGGING = colour_logging
		self.DEBUG = "Debug"
		self.ERROR = "Error"
		self.FATAL = "Fatal"
		self.HEADER = header
		self.INFO = "Info"
		self.WARN = "Warn"
		
		
		self.info("Displaying license for DanLog...")
		self.info("""
#########################################################################
# Copyright/License Notice (BSD License)                                #
#########################################################################
#########################################################################
# Copyright (c) 2012, Daniel Knaggs                                     #
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
		
		self.info("DanLog has been initialised.")
	
	def debug(self, message, newline = True):
		self.log(self.DEBUG, message, newline)
	
	def error(self, message, newline = True):
		self.log(self.ERROR, message, newline)
	
	def exit(self, exitcode = 0):
		self.sys.exit(exitcode)
	
	def fatal(self, message, newline = True):
		self.log(self.FATAL, message, newline)
	
	def getCurrentDateTime(self):
		t = self.datetime.now()
		
		return str(t.strftime("%d/%m/%Y %H:%M:%S.%f"))
	
	def info(self, message, newline = True):
		self.log(self.INFO, message, newline)
	
	def log(self, level, message, newline = True):
		t = self.getCurrentDateTime()
		header = self.HEADER
		message = str(message)
		
		
		stack = self.inspect.stack()
		stack1 = stack[1]
		stack2 = stack[2]
		
		caller = stack2[1]
		
		s1 = stack1[3]
		s2 = stack2[3]
		
		
		module = ""
		
		if s2.startswith("<"):
			module = s1
			
		else:
			module = s2
		
		module += "()"
		
		original_module = module
		
		
		colour_output = ""
		normal_output = "%s/%s/%s/%s - %s\n" % (t, header, module, level, message)
		
		if self.COLOUR_LOGGING:
			t = "\033[1;30m%s\033[1;m" % t
			
			header = "\033[1;35m%s\033[1;m" % header
			
			
			c1 = "\033[1;36m"
			c2 = "\033[1;m"
			
			module = c1 + module + c2
			
			
			if level == self.INFO:
				c1 = "\033[1;32m"
				
			elif level == self.WARN:
				c1 = "\033[1;33m"
				
			elif level == self.ERROR:
				c1 = "\033[1;31m"
				
			elif level == self.FATAL:
				c1 = "\033[0;31m"
				
			elif level == self.DEBUG:
				c1 = "\033[1;34m"
			
			level = level.ljust(5)
			level = c1 + level + c2
			
			
			c1 = "\033[1;37m"
			
			message = c1 + str(message) + c2
			
			
			colour_output = "%s/%s/%s/%s - %s\n" % (t, header, module, level, message)
		
		
		if not newline:
			colour_output = colour_output[0:-1]
			normal_output = normal_output[0:-1]
		
		
		# Send the output to the appenders
		if self.COLOUR_LOGGING:
			self.sys.stdout.write(colour_output)
			
		else:
			self.sys.stdout.write(normal_output)
		
		self.sys.stdout.flush()
		
		
		if self.file_appender:
			with open("%s.log" % caller, "a") as f:
				f.write(normal_output)
				f.flush()
				f.close()
	
	def warn(self, message, newline = True):
		self.log(self.WARN, message, newline)

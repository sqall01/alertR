#!/usr/bin/python2

# written by sqall
# twitter: https://twitter.com/sqall01
# blog: http://blog.h4des.org
# github: https://github.com/sqall01
#
# Licensed under the GNU Public License, version 2.

import SocketServer
import logging
import os
BUFSIZE = 1024


# this class is used for the threaded unix stream server and 
# extends the constructor to pass the global configured data to all threads
class ThreadedUnixStreamServer(SocketServer.ThreadingMixIn,
	SocketServer.UnixStreamServer):
	
	def __init__(self, globalData, serverAddress, RequestHandlerClass):

		# get reference to global data object
		self.globalData = globalData

		SocketServer.TCPServer.__init__(self, serverAddress, 
			RequestHandlerClass)


# this class is used for incoming local client connections (i.e. web page)
class LocalServerSession(SocketServer.BaseRequestHandler):

	def __init__(self, request, clientAddress, server):

		# file nme of this file (used for logging)
		self.fileName = os.path.basename(__file__)

		# get reference to global data object
		self.globalData = server.globalData
		self.serverComm = self.globalData.serverComm

		SocketServer.BaseRequestHandler.__init__(self, request, 
			clientAddress, server)

	def handle(self):

		logging.info("[%s]: Client connected." % self.fileName)

		# get received data
		data = self.request.recv(BUFSIZE).strip()

		# check if the alert system should be activated or not
		if data.upper() == "ACTIVATE":
			logging.info("[%s]: Activating alert system" % self.fileName)
			self.serverComm.sendOption("alertSystemActive", 1)
		elif data.upper() == "DEACTIVATE":
			logging.info("[%s]: Deactivating alert system" % self.fileName)
			self.serverComm.sendOption("alertSystemActive", 0)
		else:
			logging.error("[%s]: Unknown command %s" % (self.fileName, data))

		logging.info("[%s]: Client disconnected." 
			% self.fileName)
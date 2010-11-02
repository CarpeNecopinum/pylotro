# coding=utf-8
###########################################################################
# Name:   PyLotROUtils
# Author: Alan Jackson
# Date:   11th March 2009
#
# Support classes for the Linux/OS X based launcher
# for the game Lord of the Rings Online
#
# Based on a script by SNy <SNy@bmx-chemnitz.de>
# Python port of LotROLinux by AJackson <ajackson@bcs.org.uk>
#
# (C) 2009 AJackson <ajackson@bcs.org.uk>
#
# This file is part of PyLotRO
#
# PyLotRO is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# PyLotRO is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyLotRO.  If not, see <http://www.gnu.org/licenses/>.
###########################################################################
import os
import subprocess
import sys
import glob
from PyQt4 import QtCore
import xml.dom.minidom

# If Python 3.0 is in use use http otherwise httplib
if sys.version_info[:2] < (3, 0):
	from httplib import HTTPConnection, HTTPSConnection
	from urllib import quote
else:
	from http.client import HTTPConnection, HTTPSConnection
	from urllib.parse import quote

def WebConnection(urlIn):
	if urlIn.upper().find("HTTP://") >= 0:
		url = urlIn[7:].split("/")[0]
		post = urlIn[7:].replace(url, "")
		return HTTPConnection(url), post
	else:
		url = urlIn[8:].split("/")[0]
		post = urlIn[8:].replace(url, "")
		return HTTPSConnection(url), post

def GetText(nodelist):
	rc = ""
	for node in nodelist:
		if node.nodeType == node.TEXT_NODE or node.nodeType == node.CDATA_SECTION_NODE:
			rc = rc + node.data
	return rc

class BaseConfig:
	def __init__(self, configFile):
		self.GLSDataCentreService = ""
		self.gameName = ""

		try:
			doc = xml.dom.minidom.parse(configFile)

			nodes = doc.getElementsByTagName("appSettings")[0].childNodes
			for node in nodes:
				if node.nodeType == node.ELEMENT_NODE:
					if node.attributes.item(1).firstChild.nodeValue == "Launcher.DataCenterService.GLS":
						self.GLSDataCentreService = node.attributes.item(0).firstChild.nodeValue
					elif node.attributes.item(1).firstChild.nodeValue == "DataCenter.GameName":
						self.gameName = node.attributes.item(0).firstChild.nodeValue

			self.isConfigOK = True
		except:
			self.isConfigOK = False

class DetermineGame:
	def __init__(self):
		self.configFile = ""
		self.configFileAlt = ""
		self.icoFile = ""
		self.pngFile = ""
		self.title = ""

	def GetSettings(self, usingDND, usingTest):
		self.configFile = os.sep + "TurbineLauncher.exe.config"

		if os.name == 'mac':
			self.__os = " - Launcher for Mac OS X"
		elif os.name == 'nt':
			self.__os = " - Launcher for Windows"
		else:
			self.__os = " - Launcher for Linux"

		if usingTest:
			self.__test = " (Test)"
		else:
			self.__test = ""

		if usingDND:
			self.configFileAlt = os.sep + "dndlauncher.exe.config"
			self.icoFile = os.path.join("images", "DDOLinuxIcon.png")
			self.pngFile = os.path.join("images", "DDOLinux.png")

			self.title = "Dungeons & Dragons Online" + self.__test + self.__os
		else:
			self.configFileAlt = "/TurbineLauncher.exe.config"
			self.icoFile = os.path.join("images", "LotROLinuxIcon.png")
			self.pngFile = os.path.join("images", "LotROLinux.png")

			self.title = "Lord of the Rings Online" + self.__test + self.__os

class DetermineOS:
	def __init__(self):
		if os.name == 'mac':
			self.usingMac = True
			self.usingWindows = False
			self.appDir = "Library/Application Support/LotROLinux/"
			self.globalDir = "/Application"
			self.settingsCXG = "Library/Application Support/CrossOver Games/Bottles"
			self.settingsCXO = "Library/Application Support/CrossOver/Bottles"
			self.directoryCXG = "/CrossOver Games.app/Contents/SharedSupport/CrossOverGames/bin/"
			self.directoryCXO = "/CrossOver.app/Contents/SharedSupport/CrossOver/bin/"
			self.macPathCX = os.environ.get('CX_ROOT')
			if self.macPathCX == None:
				self.macPathCX = ""
		elif os.name == 'nt':
			self.usingMac = False
			self.usingWindows = True
			self.appDir = "PyLotRO" + os.sep
			self.globalDir = ""
			self.settingsCXG = ""
			self.settingsCXO = ""
			self.directoryCXG = ""
			self.directoryCXO = ""
			self.macPathCX = ""
		else:
			self.usingMac = False
			self.usingWindows = False
			self.appDir = ".LotROLinux" + os.sep
			self.globalDir = "/opt"
			self.settingsCXG = ".cxgames"
			self.settingsCXO = ".cxoffice"
			self.directoryCXG = "/cxgames/bin/"
			self.directoryCXO = "/cxoffice/bin/"
			self.macPathCX = ""

	def startCXG(self):
		finished = True

		if self.usingMac:
			uid = os.getuid()
			tempfile = subprocess.Popen("ps -ocomm -U%s" % (uid), shell=True, stdout=subprocess.PIPE).stdout
			cxPath = ""
			for line in tempfile.readlines():
				line = line.strip()
				if line.endswith("CrossOver Games"):
					cxPath = line

			if cxPath == "":
				process = QtCore.QProcess()
				process.start("open", ["-b", "com.codeweavers.CrossOverGames"])
				finished = process.waitForFinished()
				if finished:
					tempfile = subprocess.Popen("ps -ocomm -U%s" % (uid), shell=True, stdout=subprocess.PIPE).stdout
					cxPath = ""
					for line in tempfile.readlines():
						line = line.strip()
						if line.endswith("CrossOver Games"):
							cxPath = line
				else:
					process.close()

			if finished:
				lineout = ""

				lines = cxPath.split("/")
				for line in lines[0:len(lines) - 3]:
					lineout += "%s/" % (line)

				cxPath = lineout

				path = os.environ.get('PATH')

				os.environ["CX_ROOT"] = "%s/Contents/SharedSupport/CrossOverGames" % (cxPath)
				os.environ["FONT_ENCODINGS_DIRECTORY"] = (cxPath + "/Contents/SharedSupport/X11/lib/" +
					"X11/fonts/encodings/encodings.dir")
				os.environ["FONTCONFIG_ROOT"] = "%s/Contents/SharedSupport/X11" % (cxPath)
				os.environ["COMMAND_MODE"] = "legacy" 
				os.environ["FONTCONFIG_PATH"] = "%s/Contents/SharedSupport/X11/etc/fonts" % (cxPath)
				os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (cxPath + "/Contents/SharedSupport/X11/lib" +
					":" + os.environ.get('HOME') + "/lib:/usr/local/lib:/lib:/usr/lib")
				os.environ["PATH"] = (path + ":" + cxPath + "/Contents/SharedSupport/CrossOverGames/bin")
				self.macPathCX = os.environ.get('CX_ROOT')

				tempfile =  subprocess.Popen("defaults read com.coeweavers.CrossOverGames Display",
					shell=True, stdout=subprocess.PIPE).stdout
				display = tempfile.read().strip()
				if display == "":
					display = "2"
				os.environ["DISPLAY"] = ":%s" % (display)

		return finished			

	def startCXO(self):
		finished = True

		if self.usingMac:
			uid = os.getuid()
			tempfile = subprocess.Popen("ps -ocomm -U%s" % (uid), shell=True, stdout=subprocess.PIPE).stdout
			cxPath = ""
			for line in tempfile.readlines():
				line = line.strip()
				if line.endswith("CrossOver"):
					cxPath = line

			if cxPath == "":
				process = QtCore.QProcess()
				process.start("open", ["-b", "com.codeweavers.CrossOver"])
				finished = process.waitForFinished()
				if finished:
					tempfile = subprocess.Popen("ps -ocomm -U%s" % (uid), shell=True, stdout=subprocess.PIPE).stdout
					cxPath = ""
					for line in tempfile.readlines():
						line = line.strip()
						if line.endswith("CrossOver"):
							cxPath = line
				else:
					process.close()

			if finished:
				lineout = ""

				lines = cxPath.split("/")
				for line in lines[0:len(lines) - 3]:
					lineout += "%s/" % (line)

				cxPath = lineout

				path = os.environ.get('PATH')

				os.environ["CX_ROOT"] = "%s/Contents/SharedSupport/CrossOver" % (cxPath)
				os.environ["FONT_ENCODINGS_DIRECTORY"] = (cxPath + "/Contents/SharedSupport/X11/lib/" +
					"X11/fonts/encodings/encodings.dir")
				os.environ["FONTCONFIG_ROOT"] = "%s/Contents/SharedSupport/X11" % (cxPath)
				os.environ["COMMAND_MODE"] = "legacy" 
				os.environ["FONTCONFIG_PATH"] = "%s/Contents/SharedSupport/X11/etc/fonts" % (cxPath)
				os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (cxPath + "/Contents/SharedSupport/X11/lib" +
					":" + os.environ.get('HOME') + "/lib:/usr/local/lib:/lib:/usr/lib")
				os.environ["PATH"] = (path + ":" + cxPath + "/Contents/SharedSupport/CrossOver/bin")
				self.macPathCX = os.environ.get('CX_ROOT')

				tempfile =  subprocess.Popen("defaults read com.coeweavers.CrossOver Display",
					shell=True, stdout=subprocess.PIPE).stdout
				display = tempfile.read().strip()
				if display == "":
					display = "2"
				os.environ["DISPLAY"] = ":%s" % (display)

		return finished			

class GLSDataCentre:
	def __init__(self, urlGLSDataCentreService, gameName, baseDir, osType):
		SM_TEMPLATE = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\
<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\">\
<soap:Body><GetDatacenters xmlns=\"http://www.turbine.com/SE/GLS\"><game>%s</game>\
</GetDatacenters></soap:Body></soap:Envelope>"

		SoapMessage = SM_TEMPLATE%(gameName)

		try:
			webservice, post = WebConnection(urlGLSDataCentreService)

			webservice.putrequest("POST", post)
			webservice.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
			webservice.putheader("Content-length", "%d" % len(SoapMessage))
			webservice.putheader("SOAPAction", "http://www.turbine.com/SE/GLS/GetDatacenters")
			webservice.endheaders()
			webservice.send(SoapMessage)

			webresp = webservice.getresponse()

			tempxml = webresp.read()

			filename = "%s%sGLSDataCenter.config" % (baseDir, osType.appDir)
			outfile = open(filename, "w")
			outfile.write(tempxml)
			outfile.close()

			if tempxml == "":
				self.loadSuccess = False
			else:
				doc = xml.dom.minidom.parseString(tempxml)

				self.authServer = GetText(doc.getElementsByTagName("AuthServer")[0].childNodes)
				self.patchServer = GetText(doc.getElementsByTagName("PatchServer")[0].childNodes)
				self.launchConfigServer = GetText(doc.getElementsByTagName("LauncherConfigurationServer")[0].childNodes)

				self.realmList = []

				name = ""
				urlChatServer = ""
				urlStatusServer = ""

				for node in doc.getElementsByTagName("World"):
					for realm in node.childNodes:
						if realm.nodeName == "Name":
							name = realm.firstChild.nodeValue
						elif realm.nodeName == "ChatServerUrl":
							urlChatServer = realm.firstChild.nodeValue
						elif realm.nodeName == "StatusServerUrl":
							urlStatusServer = realm.firstChild.nodeValue
					self.realmList.append(Realm(name, urlChatServer, urlStatusServer))

				self.loadSuccess = True
		except:
			self.loadSuccess = False

class Language:
	def __init__(self, code):
		self.code = code.upper()

		if code == "EN_GB":
			self.name = "English (UK)"
			self.patch = "en_gb"
		elif code == "ENGLISH":
			self.name = "English"
			self.patch = "en"
		elif code == "FR":
			self.name = "French"
			self.patch = "fr"
		elif code == "DE":
			self.name = "German"
			self.patch = "de"
		else:
			self.name = code
			self.patch = code

class LanguageConfig():
	def __init__(self, runDir):
		self.langFound = False
		self.langList = []

		for name in glob.glob("%s%sclient_local_*.dat" % (runDir, os.sep)):
			self.langFound = True
			temp = name.replace("%s%sclient_local_" % (runDir, os.sep), "").replace(".dat", "")
			self.langList.append(Language(temp))

class Realm:
	def __init__(self, name, urlChatServer, urlServerStatus):
		self.name = name
		self.urlChatServer = urlChatServer
		self.urlServerStatus = urlServerStatus
		self.realmAvailable = False
		self.nowServing = ""
		self.loginServer = ""
		self.queueURL = ""

	def CheckRealm(self, useDND, baseDir, osType):
		try:
			webservice, post = WebConnection(self.urlServerStatus)

			webservice.putrequest("GET", post)
			webservice.endheaders()

			webresp = webservice.getresponse()

			tempxml = webresp.read()

			filename = "%s%sserver.config" % (baseDir, osType.appDir)
			outfile = open(filename, "w")
			outfile.write(tempxml)
			outfile.close()

			if tempxml == "":
				self.realmAvailable = False
			else:
				doc = xml.dom.minidom.parseString(tempxml)

				try:
					self.nowServing = GetText(doc.getElementsByTagName("nowservingqueuenumber")[0].childNodes)
				except:
					self.nowServing = ""

				try:
					self.queueURL = GetText(doc.getElementsByTagName("queueurls")[0].childNodes).split(";")[0]
				except:
					self.queueURL = ""

				self.loginServer = GetText(doc.getElementsByTagName("loginservers")[0].childNodes).split(";")[0]

				self.realmAvailable = True
		except:
			self.realmAvailable = False

class WorldQueueConfig:
	def __init__(self, urlConfigServer, usingDND, baseDir, osType):
		self.gameClientFilename = ""
		self.gameClientArgTemplate = ""
		self.newsFeedURL = ""
		self.newsStyleSheetURL = ""
		self.patchProductCode = ""
		self.worldQueueURL = ""
		self.worldQueueParam = ""

		try:
			webservice, post = WebConnection(urlConfigServer)

			webservice.putrequest("GET", post)
			webservice.endheaders()

			webresp = webservice.getresponse()

			tempxml = webresp.read()

			filename = "%s%slauncher.config" % (baseDir, osType.appDir)
			outfile = open(filename, "w")
			outfile.write(tempxml)
			outfile.close()

			if tempxml == "":
				self.loadSuccess = False
			else:
				doc = xml.dom.minidom.parseString(tempxml)

				nodes = doc.getElementsByTagName("appSettings")[0].childNodes
				for node in nodes:
					if node.nodeType == node.ELEMENT_NODE:
						if node.attributes.item(1).firstChild.nodeValue == "GameClient.Filename":
							self.gameClientFilename = node.attributes.item(0).firstChild.nodeValue
						elif node.attributes.item(1).firstChild.nodeValue == "GameClient.ArgTemplate":
							self.gameClientArgTemplate = node.attributes.item(0).firstChild.nodeValue
						elif node.attributes.item(1).firstChild.nodeValue == "URL.NewsFeed":
							self.newsFeedURL = node.attributes.item(0).firstChild.nodeValue
						elif node.attributes.item(1).firstChild.nodeValue == "URL.NewsStyleSheet":
							self.newsStyleSheetURL = node.attributes.item(0).firstChild.nodeValue
						elif node.attributes.item(1).firstChild.nodeValue == "Patching.ProductCode":
							self.patchProductCode = node.attributes.item(0).firstChild.nodeValue
						elif node.attributes.item(1).firstChild.nodeValue == "WorldQueue.LoginQueue.URL":
							self.worldQueueURL = node.attributes.item(0).firstChild.nodeValue
						elif node.attributes.item(1).firstChild.nodeValue == "WorldQueue.TakeANumber.Parameters":
							self.worldQueueParam = node.attributes.item(0).firstChild.nodeValue

				self.loadSuccess = True
		except:
			self.loadSuccess = False

class Game:
	def __init__(self, name, description):
		self.name = name
		self.description = description

class AuthenticateUser:
	def __init__(self, urlLoginServer, name, password, game, baseDir, osType):
		SM_TEMPLATE = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\
<soap:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" \
xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" \
xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\">\
<soap:Body><LoginAccount xmlns=\"http://www.turbine.com/SE/GLS\"><username>%s</username>\
<password>%s</password><additionalInfo></additionalInfo></LoginAccount></soap:Body></soap:Envelope>"

		SoapMessage = SM_TEMPLATE%(name, password)

		webresp = None

		try:
			webservice, post = WebConnection(urlLoginServer)

			webservice.putrequest("POST", post)
			webservice.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
			webservice.putheader("Content-length", "%d" % len(SoapMessage))
			webservice.putheader("SOAPAction", "http://www.turbine.com/SE/GLS/LoginAccount")
			webservice.endheaders()
			webservice.send(SoapMessage)

			webresp = webservice.getresponse()

			self.gameList = []

			activeAccount = False
			self.ticket = ""

			tempxml = webresp.read()

			filename = "%s%sGLSAuthServer.config" % (baseDir, osType.appDir)
			outfile = open(filename, "w")
			outfile.write(tempxml)
			outfile.close()

			if tempxml == "":
				self.authSuccess = False
				self.messError = "[E08] Server not found - may be down"
			else:
				doc = xml.dom.minidom.parseString(tempxml)

				self.ticket = GetText(doc.getElementsByTagName("Ticket")[0].childNodes)

				for nodes in doc.getElementsByTagName("GameSubscription"):
					game2 = ""
					status = ""
					name = ""
					desc = ""

					for node in nodes.childNodes:
						if node.nodeName == "Game":
							game2 = GetText(node.childNodes)
						elif node.nodeName == "Status":
							status = GetText(node.childNodes)
						elif node.nodeName == "Name":
							name = GetText(node.childNodes)
						elif node.nodeName == "Description":
							desc = GetText(node.childNodes)

					if game2 == game:
						activeAccount = True
						self.gameList.append(Game(name, desc))

				if activeAccount:
					self.messError = "No Error"
					self.authSuccess = True
				else:
					self.messError = "[E14] Game account not associated with user account - please visit games website and check account details"
					self.authSuccess = False
		except:
			self.authSuccess = False

			if webresp.status == 500:
				self.messError = "[E07] Account details incorrect"
			else:
				self.messError = "[E08] Server not found - may be down (%s)" % (webresp.status)

class JoinWorldQueue:
	def __init__(self, argTemplate, account, ticket, queue, urlIn, baseDir, osType):
		try:
			webservice, post = WebConnection(urlIn)

			argComplete = argTemplate.replace("{0}", account).replace("{1}",
				quote(ticket)).replace("{2}", quote(queue))

			webservice.putrequest("POST", post)
			webservice.putheader("Content-type", "application/x-www-form-urlencoded")
			webservice.putheader("Content-length", "%d" % len(argComplete))
			webservice.putheader("SOAPAction", "http://www.turbine.com/SE/GLS/LoginAccount")
			webservice.endheaders()
			webservice.send(argComplete)

			webresp = webservice.getresponse()

			tempxml = webresp.read()

			filename = "%s%sWorldQueue.config" % (baseDir, osType.appDir)
			outfile = open(filename, "w")
			outfile.write(tempxml)
			outfile.close()

			if tempxml == "":
				self.joinSuccess = False
			else:
				doc = xml.dom.minidom.parseString(tempxml)

				if GetText(doc.getElementsByTagName("HResult")[0].childNodes) == "0x00000000":
					self.number = GetText(doc.getElementsByTagName("QueueNumber")[0].childNodes)
					self.serving = GetText(doc.getElementsByTagName("NowServingNumber")[0].childNodes)

					self.joinSuccess = True
				else:
					self.joinSuccess = False
		except:
			self.joinSuccess = False


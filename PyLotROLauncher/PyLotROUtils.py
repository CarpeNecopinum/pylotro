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
import sys
import httplib
import glob
import urllib
from Ft.Xml.Domlette import NonvalidatingReader, Print
from Ft.Lib import Uri

def WebConnection(urlIn):
	if urlIn.upper().find("HTTP://") >= 0:
		url = urlIn[7:].split("/")[0]
		post = urlIn[7:].replace(url, "")
		return httplib.HTTPConnection(url), post
	else:
		url = urlIn[8:].split("/")[0]
		post = urlIn[8:].replace(url, "")
		return httplib.HTTPSConnection(url), post

class BaseConfig:
	def __init__(self, configFile):
		self.GLSDataCentreService = ""
		self.gameName = ""

		try:
			file_uri = Uri.OsPathToUri(configFile)
			doc = NonvalidatingReader.parseUri(file_uri)

			val = (None, u'value')
			xpathquery = u"//appSettings/add[@key=\"%s\"]"

			self.GLSDataCentreService = doc.xpath(xpathquery % ("Launcher.DataCenterService.GLS"))[0].attributes[val].value
			self.gameName = doc.xpath(xpathquery % ("DataCenter.GameName"))[0].attributes[val].value

			self.isConfigOK = True
		except:
			self.isConfigOK = False

class DetermineGame:
	def __init__(self, rootDir):
		self.configFile = ""
		self.configFileAlt = ""
		self.icoFile = ""
		self.pngFile = ""
		self.title = ""
		self.rootDir = rootDir

	def GetSettings(self, usingDND, usingTest):
		self.configFile = "/TurbineLauncher.exe.config"

		if os.name == 'mac':
			self.__os = " - Launcher for Mac OS X"
		else:
			self.__os = " - Launcher for Linux"

		if usingTest:
			self.__test = " (Test)"
		else:
			self.__test = ""

		if usingDND:
			self.configFileAlt = "/dndlauncher.exe.config"
			self.icoFile = os.path.join(self.rootDir, "images", "DDOLinux.ico")
			self.pngFile = os.path.join(self.rootDir, "images", "DDOLinux.png")

			self.title = "Dungeons & Dragons Online" + self.__test + self.__os
		else:
			self.configFileAlt = "/TurbineLauncher.exe.config"
			self.icoFile = os.path.join(self.rootDir, "images", "LotROLinux.ico")
			self.pngFile = os.path.join(self.rootDir, "images", "LotROLinux.png")

			self.title = "Lord of the Rings Online" + self.__test + self.__os

class DetermineOS:
	def __init__(self):
		if os.name == 'mac':
			self.appDir = "Library/Application Support/LotROLinux/"
			self.globalDir = "/Application"
			self.settingsCXG = "Library/Application Support/CrossOver Games/Bottles"
			self.settingsCXO = "Library/Application Support/CrossOver/Bottles"
			self.directoryCXG = "/CrossOver Games.app/Contents/SharedSupport/CrossOverGames/bin/"
			self.directoryCXO = "/CrossOver.app/Contents/SharedSupport/CrossOver/bin/"
			self.macPathCX = os.environ.get('CX_ROOT')
			if self.macPathCX == None:
				self.macPathCX = ""
		else:
			self.appDir = ".LotROLinux/"
			self.globalDir = "/opt"
			self.settingsCXG = ".cxgames"
			self.settingsCXO = ".cxoffice"
			self.directoryCXG = "/cxgames/bin/"
			self.directoryCXO = "/cxoffice/bin/"
			self.macPathCX = ""

class GLSDataCentre:
	def __init__(self, urlGLSDataCentreService, gameName):
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

			if tempxml == "":
				self.loadSuccess = False
			else:
				tempxml = tempxml.split("<GetDatacentersResult>")[1].split("</GetDatacentersResult>")[0]
				tempxml = "<zxz>" + tempxml + "</zxz>"
				doc = NonvalidatingReader.parseString(tempxml, urlGLSDataCentreService)

				self.authServer = doc.xpath(u"//AuthServer")[0].firstChild.nodeValue
				self.patchServer = doc.xpath(u"//PatchServer")[0].firstChild.nodeValue
				self.launchConfigServer = doc.xpath(u"//LauncherConfigurationServer")[0].firstChild.nodeValue

				self.realmList = []

				name = ""
				urlChatServer = ""
				urlStatusServer = ""

				for node in doc.xpath(u"//World"):
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

		for name in glob.glob("%s/client_local_*.dat" % (runDir)):
			self.langFound = True
			temp = name.replace("%s/client_local_" % (runDir), "").replace(".dat", "")
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

	def CheckRealm(self, useDND):
		try:
			webservice, post = WebConnection(self.urlServerStatus)

			webservice.putrequest("GET", post)
			webservice.endheaders()

			webresp = webservice.getresponse()

			tempxml = webresp.read()

			if tempxml == "":
				self.realmAvailable = False
			else:
				doc = NonvalidatingReader.parseString(tempxml, self.urlServerStatus)

				if useDND:
					self.nowServing = ""
					self.queueURL = ""
				else:
					self.nowServing = doc.xpath(u"//nowservingqueuenumber")[0].firstChild.nodeValue
					self.queueURL = doc.xpath(u"//queueurls")[0].firstChild.nodeValue.split(";")[0]

				self.loginServer = doc.xpath(u"//loginservers")[0].firstChild.nodeValue.split(";")[0]

				self.realmAvailable = True
		except:
			self.realmAvailable = False

class WorldQueueConfig:
	def __init__(self, urlConfigServer, usingDND):
		try:
			doc = NonvalidatingReader.parseUri(urlConfigServer)

			val = (None, u'value')
			xpathquery = u"//appSettings/add[@key=\"%s\"]"

			self.gameClientFilename = doc.xpath(xpathquery % ("GameClient.Filename"))[0].attributes[val].value
			self.gameClientArgTemplate = doc.xpath(xpathquery % ("GameClient.ArgTemplate"))[0].attributes[val].value
			self.newsFeedURL = doc.xpath(xpathquery % ("URL.NewsFeed"))[0].attributes[val].value
			self.newsStyleSheetURL = doc.xpath(xpathquery % ("URL.NewsStyleSheet"))[0].attributes[val].value
			self.patchProductCode = doc.xpath(xpathquery % ("Patching.ProductCode"))[0].attributes[val].value

			if usingDND:
				self.worldQueueURL = ""
				self.worldQueueParam = ""
			else:
				self.worldQueueURL = doc.xpath(xpathquery % ("WorldQueue.LoginQueue.URL"))[0].attributes[val].value
				self.worldQueueParam = doc.xpath(xpathquery % ("WorldQueue.TakeANumber.Parameters"))[0].attributes[val].value

			self.loadSuccess = True
		except:
			self.loadSuccess = False

class Game:
	def __init__(self, name, description):
		self.name = name
		self.description = description

class AuthenticateUser:
	def __init__(self, urlLoginServer, name, password, game):
		SM_TEMPLATE = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\
<soap:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" \
xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" \
xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\">\
<soap:Body><LoginAccount xmlns=\"http://www.turbine.com/SE/GLS\"><username>%s</username>\
<password>%s</password><additionalInfo></additionalInfo></LoginAccount></soap:Body></soap:Envelope>"

		SoapMessage = SM_TEMPLATE%(name, password)

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

			if tempxml == "":
				self.authSuccess = False
				self.messError = "[E08] Server not found - may be down"
			else:
				tempxml = "<zxz>" + tempxml.split("<LoginAccountResult>")[1].split("</LoginAccountResult>")[0] + "</zxz>"

				doc = NonvalidatingReader.parseString(tempxml, urlLoginServer)

				self.ticket = doc.xpath(u"//Ticket")[0].firstChild.nodeValue

				for node in doc.xpath(u"//GameSubscription"):
					validGame = True
					name = ""
					desc = ""
					for node2 in node.childNodes:
						if node2.nodeName == "Game":
							if node2.firstChild.nodeValue != game:
								validGame = False
						elif node2.nodeName == "Status":
							if node2.firstChild.nodeValue != "Active":
								validGame = False
						elif node2.nodeName == "Name":
							name = node2.firstChild.nodeValue
						elif node2.nodeName == "Description":
							desc = node2.firstChild.nodeValue

					if validGame:
						activeAccount = True
						self.gameList.append(Game(name, desc))

				if activeAccount:
					self.messError = "No Error"
					self.authSuccess = True
				else:
					self.messError = "[E06] Account marked as not active"
					self.authSuccess = False
		except:
			self.authSuccess = False

			if webresp.status == 500:
				self.messError = "[E07] Account details incorrect"
			else:
				self.messError = "[E08] Server not found - may be down"

class JoinWorldQueue:
	def __init__(self, argTemplate, account, ticket, queue, urlIn):
		try:
			webservice, post = WebConnection(urlIn)

			argComplete = argTemplate.replace("{0}", account).replace("{1}",
				urllib.quote(ticket)).replace("{2}", urllib.quote(queue))

			webservice.putrequest("POST", post)
			webservice.putheader("Content-type", "application/x-www-form-urlencoded")
			webservice.putheader("Content-length", "%d" % len(argComplete))
			webservice.putheader("SOAPAction", "http://www.turbine.com/SE/GLS/LoginAccount")
			webservice.endheaders()
			webservice.send(argComplete)

			webresp = webservice.getresponse()

			tempxml = webresp.read()

			if tempxml == "":
				self.joinSuccess = False
			else:
				doc = NonvalidatingReader.parseString(tempxml, urlIn)

				if doc.xpath(u"//HResult")[0].firstChild.nodeValue == "0x00000000":
					self.number = doc.xpath(u"//QueueNumber")[0].firstChild.nodeValue
					self.serving = doc.xpath(u"//NowServingNumber")[0].firstChild.nodeValue

				self.joinSuccess = True
		except:
			self.joinSuccess = False


from ups_db import *
import socket, select             
from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint
from world_ups_pb2 import *
from ups_amazon_pb2 import *
import sys
from message import *
import psycopg2
from multiprocessing.pool import ThreadPool
import time
import threading
from queue import Queue
from global_var import *

# ----------------------------------------- each time we receive a message, send ack.
def sendACK(num, socket, seqnum):
	# 0: send to world
	# 1: send to amazon
	# return: exists, true
	# return: not exists, false
	global receivedW
	global receivedA
	value = True
	if num==0:
		# ------- if it's the first time to receive, append and return false(do not exists)
		if seqnum not in receivedW:
			receivedW.append(seqnum)
			value = False
		else:
			print("The message from world has been received before. Seqnum is", seqnum)
		sendW = UCommands()
		sendW.acks.append(seqnum)
		sendMsg(socket, sendW)
		print("send ack to world, ack=", seqnum)
	else:
		if seqnum not in receivedA:
			receivedA.append(seqnum)
			value = False
		else:
			print("The message from amazon has been received before. Seqnum is", seqnum)
		sendA = UMessages()
		sendA.acks.append(seqnum)
		sendMsg(socket, sendA)
		print("send ack to amazon, ack=", seqnum)
	return value


# ----------------------------------------- add order into the database, with ups account
def actionAddOrder1(wSocket, cmd, truckid):
	productids=[]
	products=[]
	counts=[]
	for product in cmd.product:
		productids.append(product.productid)
		products.append(product.description)
		counts.append(product.count)
	print("add order, type1, packageid is", cmd.packageid, "truckid is", truckid, "uAccountName is", cmd.uAccountName)
	res = addOrder1(cmd.uAccountName, cmd.packageid, truckid, cmd.x, cmd.y, cmd.worldid, counts, productids, products)
	if not res:
		print("error with addOrder1, add failed")

# ----------------------------------------- add order into the database, without ups account
def actionAddOrder2(wSocket, cmd, truckid):
	productids=[]
	products=[]
	counts=[]
	for product in cmd.product:
		productids.append(product.productid)
		products.append(product.description)
		counts.append(product.count)
	print("add order, type2, packageid is", cmd.packageid, "truckid is", truckid)
	res = addOrder2(cmd.packageid, truckid, cmd.x, cmd.y, cmd.worldid, counts, productids, products)
	if not res:
		print("error with addOrder2")

# ----------------------------------------- get the truck, and send the message to the world
def sendTruck(wSocket, whid):
	global trucks
	global seqCounter
	global toWorldMsg
	sendWorld = UCommand(100, False, -1)
	truck = trucks.getTruckWh(whid)
	sendWorld.addPickups(truck, whid, seqCounter.getWorldSeq())
	sendMsg(wSocket, sendWorld.command)
	toWorldMsg.addMsg(sendWorld.seqnum, sendWorld)
	print("send truck to the world, truckid", truck, " to wh", whid, "seqnum is", sendWorld.seqnum)
	return truck


# ----------------------------------------- deal with the received message of getTruck
#cmd is messgae.getTrucks
def getTruckHandle(cmd, wSocket, aSocket):
	global seqCounter
	if(cmd.HasField('uAccountName')):
		#cmd received
		uid = find_uAccount(cmd.uAccountName)
		#mess to send
		mess = UMessage()
		if(uid>=0):#exits, send uaccountresult, add order, then send truck
			mess = UMessage()
			mess.addUAccountResult(cmd.packageid, True, cmd.uAccountName, uid, seqCounter.getAmazonSeq())
			truckid = sendTruck(wSocket, cmd.whid)
			actionAddOrder1(wSocket, cmd, truckid)
			print("send amazon uaccount exists，seqnum is", mess.seqnum)
		else:
			truckid = sendTruck(wSocket, cmd.whid)
			actionAddOrder2(wSocket, cmd, truckid)
			mess.addUAccountResult(cmd.packageid, False, cmd.uAccountName, -1, seqCounter.getAmazonSeq())
			print("send amazon uaccount doesn't exists, seqnum is", mess.seqnum)
		toAmazonMsg.addMsg(mess.seqnum, mess)
		sendMsg(aSocket, mess.command)
	else:
		truckid = sendTruck(wSocket, cmd.whid)
		actionAddOrder2(wSocket, cmd, truckid)

# ----------------------------------------- create a client socket and connect to the given server
def buildSocket(ip, port):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#s.connect(('vcm-14419.vm.duke.edu', port))
	#s.connect(('127.0.0.1', port))
	#s.connect(('vcm-14632.vm.duke.edu', port))
	s.connect((ip, port))
	return s

# ----------------------------------------- close the socket connection
def closeSocket(s):
	s.shutdown(socket.SHUT_RDWR)
	s.close()

# ----------------------------------------- print out the information that ups received from 'Uconnected'
def listUConnected(msg):
	print("receive UConnected: worldid =", msg.worldid, " result =", msg.result)

# ----------------------------------------- receive a message from the connection s
def recvMsg(s, msg):
	var_int_buff = []
	while True:
	    buf = s.recv(1)
	    var_int_buff += buf
	    msg_len, new_pos = _DecodeVarint32(var_int_buff, 0)
	    if new_pos != 0:
	        break
	whole_message = s.recv(msg_len)
	msg.ParseFromString(whole_message)
	return msg

# ----------------------------------------- send a message through the connection s
def sendMsg(s, msg):
	newMsg = msg.SerializeToString()
	_EncodeVarint(s.send, len(newMsg), None)
	s.send(newMsg)

# ----------------------------------------- helper function: initialize a truck
def genUInitTruck(id, x, y):
	truck = UInitTruck()
	truck.id = id
	truck.x= x
	truck.y = y
	return truck

# ----------------------------------------- helper function: initialize a Uconnect command to the world
def genUConnect(worldid, initialtrucks, isAmazon):
	uconnect = UConnect()
	if(worldid>0):
		uconnect.worldid = worldid
	for truck in initialtrucks:
		uconnect.trucks.append(truck)
	uconnect.isAmazon = False
	return uconnect

# ----------------------------------------- helper function: initialize UInitialWorldid message to Amazon
def genUInitialWorldid(worldid):
	unitialworldid = UInitialWorldid()
	unitialworldid.worldid = worldid
	return unitialworldid

# ----------------------------------------- connect with world and amazon, send worldid to amazon
def WAconnect(ip, numTruck):
	#wSocket: world socket, aSocket: amazon socket
	global seqCounter
	wSocket = buildSocket(ip, 12345)
	aSocket = buildSocket(ip, 34567)
	initialtrucks = []
	for i in range (numTruck):
		initialtrucks.append(genUInitTruck(i, 0, 0))
	uconnect = genUConnect(-1, initialtrucks, False)

	# connect to the world
	sendMsg(wSocket, uconnect)
	uconnected = UConnected()
	#TODO: set time out for failure of connection
	#TODO: what if result = fail
	uconnected = recvMsg(wSocket, uconnected)
	listUConnected(uconnected)

	sendWorld = UMessage()
	sendWorld.addUInitialWorldid(uconnected.worldid, seqCounter.getAmazonSeq())
	ainitial = AMessages()
	recvMsg(aSocket, ainitial)
	#TODO: send error if the first message received from amazon is not initialWorldid
	if(ainitial.HasField('initialWorldid')):
		sendACK(1, aSocket, ainitial.initialWorldid.seqnum)
		sendMsg(aSocket, sendWorld.command)
	return wSocket, aSocket
	

# ----------------------------------------- amazon thread
class AThread (threading.Thread):
    def __init__(self, threadID, aSocket, wSocket):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.aSocket = aSocket
        self.wSocket = wSocket
    def run(self):
        aActions(self.aSocket, self.wSocket)
	
def aActions(aSocket, wSocket):
	global toWorldMsg
	global seqCounter
	global trucks
	inputs = [aSocket]
	while 1:
		rs,ws,es=select.select(inputs,[],[],1)
		for r in rs:
			if r is aSocket:
				fromA_msg = AMessages()
				recvMsg(aSocket, fromA_msg)
				if not fromA_msg:
					print("The connection with Amazon broken down\n")
					return
				else:

					# ------------------- amazon tells ups to get truck ----------------
					if len(fromA_msg.getTrucks):
						for cmd in fromA_msg.getTrucks:
							print("received getTrucks from amazon, seqnum is", cmd.seqnum)
							if not sendACK(1, aSocket, cmd.seqnum):
								getTruckHandle(cmd, wSocket, aSocket)

					elif len(fromA_msg.delivers):
						print("received delivers")
						#---------------- amazon finish loaded, tell ups to deliver------------
						for deliver in fromA_msg.delivers:
							print("received delivers from amazon(finish loaded), seqnum is", deliver.seqnum)
							if not sendACK(1, aSocket, deliver.seqnum):
								ids, xs, ys = change_status(deliver.truckid, 3)
								sendW = UCommand(100, False, -1)
								packages = []
								for i in range(len(ids)):
									package = UDeliveryLocation()
									package.packageid = ids[i]
									package.x = xs[i]
									package.y = ys[i]
									packages.append(package)
									print("prepare delivery location, packageid is", package.packageid, "trukid is", deliver.truckid)
								sendW.addDeliveries(deliver.truckid, packages, seqCounter.getWorldSeq())
								sendMsg(wSocket, sendW.command)
								print("send deliveries to the world, seqnum is", sendW.seqnum)
								toWorldMsg.addMsg(sendW.seqnum, sendW)
								trucks.truckToDeliver(deliver.truckid)

					# ------------------- deal with account connection request from amazon -------
					elif len(fromA_msg.accountConnections):
						print("received accountConnections")
						for conn in fromA_msg.accountConnections:
							if not sendACK(1, aSocket, conn.seqnum):
								uid = associateAU(conn.aAccountid, conn.uAccountName, conn.worldid)
								sendA = UMessage()
								if(uid>=0):
									sendA.addUAccountConnectionResult(True, uid, seqCounter.getAmazonSeq())
								else:
									sendA.addUAccountConnectionResult(False, uid, seqCounter.getAmazonSeq())
								toAmazonMsg.addMsg(sendA.seqnum, sendA)
								sendMsg(aSocket, sendA.command)

					elif len(fromA_msg.acks):
						for ack in fromA_msg.acks:
							toAmazonMsg.delMsg(ack)
							print("received ack from amazon, ack=", ack)


					else:
						print("The message type is not known\n")




# ----------------------------------------- world thread
class WThread (threading.Thread):
    def __init__(self, threadID, aSocket, wSocket):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.aSocket = aSocket
        self.wSocket = wSocket
    def run(self):
        wActions(self.aSocket, self.wSocket)

# ----------------------------------------- keep receiving from world and make actions
def wActions(aSocket, wSocket):
	global toWorldMsg
	global trucks
	global seqCounter
	inputs = [wSocket]
	while 1:
		rs,ws,es=select.select(inputs,[],[],1)
		for r in rs:
			if r is wSocket:
				fromW_msg = UResponses()
				recvMsg(wSocket, fromW_msg)

				# --------------------- World tells ups truck arrives at the warehouse -------------
				if len(fromW_msg.completions):
					for completion in fromW_msg.completions:
						if not sendACK(0, wSocket, completion.seqnum):
							if completion.status=='ARRIVE WAREHOUSE':
								print("received completion, completion.status is" ,completion.status, "seqnum is", completion.seqnum)
								#---send UTruckReady for each package ---#
								ids, xs, ys = change_status(completion.truckid, 2)
								for packageid in ids:
									sendA = UMessage()
									sendA.addUTruckReady(completion.truckid, packageid, seqCounter.getAmazonSeq())
									toAmazonMsg.addMsg(sendA.seqnum, sendA)
									sendMsg(aSocket, sendA.command)
									print("send UTruckReady to amazon, truckid is", completion.truckid, "packageid is", packageid,\
										"seqnum is", sendA.seqnum)

							else: # all delivery made
								print("received completion, completion.status is" ,completion.status, "seqnum is", completion.seqnum)
								trucks.truckToIdle(completion.truckid)

				# ---------------------- World tells ups each package delivered ------------------
				if len(fromW_msg.delivered):
					for deliver in fromW_msg.delivered:
						print("received package delivered from the world, packageid is", deliver.packageid, \
							"seqnum is", deliver.seqnum)
						if not sendACK(0, wSocket, deliver.seqnum):
							sendA = UMessage()
							sendA.addUPackageDelivered(deliver.packageid, seqCounter.getAmazonSeq())
							toAmazonMsg.addMsg(sendA.seqnum, sendA)
							sendMsg(aSocket, sendA.command)
							if not change_package_status(deliver.packageid, 4):
								print("error in change_package_status with pacakgeid", deliver.packageid)

				if fromW_msg.HasField('finished'):
					print("received finished from the world, finished is", fromW_msg.finished)

				if len(fromW_msg.error):
					for err in fromW_msg.error:
						if not sendACK(0, wSocket, err.seqnum):
							print("received error!! err is", err.err, "originseqnum is", err.originseqnum, \
							"seqnum is", err.seqnum)

				if len(fromW_msg.acks):
					for ack in fromW_msg.acks:
						print("received ack from world, ack=", ack)
						toWorldMsg.delMsg(ack)

# ----------------------------------------- this thread keep finding sent message with no ack received, and resend
class ResendThread (threading.Thread):
    def __init__(self, threadID, aSocket, wSocket):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.aSocket = aSocket
        self.wSocket = wSocket
    def run(self):
        resendActions(self.aSocket, self.wSocket)
	

# ----------------------------------------- keep searching 
def checkMsg(toMsg, socket, name):
	for seqnum in toMsg.getKeys():
			msg = toMsg.getMsg(seqnum)
			if msg is not None:
				currTime = time.time()
				if(currTime - msg.sendTime > 10):
					print(name, ": No ack received, need to resend. Seqnum is", msg.seqnum, "sendTime is", msg.sendTime, \
						"currTime is", currTime)
					msg.sendTime = currTime
					sendMsg(socket, msg.command)
					toMsg.updateMsg(msg.seqnum, msg)


def resendActions(aSocket, wSocket):
	global toWorldMsg
	while True:
		checkMsg(toWorldMsg, wSocket, "world")
		checkMsg(toAmazonMsg, aSocket, "amazon")


# ----------------------------------------- main function
def ups(argv):
	clear_table(0)
	ip = argv[1]
	wSocket, aSocket = WAconnect(ip, 100)
	#TODO: start two main threads, one for amazon and one for the world
	aThread = AThread(1, aSocket, wSocket)
	aThread.start()
	wThread = WThread(2, aSocket, wSocket)
	wThread.start()
	resendThread = ResendThread(3, aSocket, wSocket)
	resendThread.start()
	aThread.join()
	wThread.join()
	resendThread.join()


if __name__ == '__main__':
	print("UPS service is starting...")
	trucks = Trucks(1000)
	seqCounter = SeqCounter()
	lockToWorldMsg = threading.RLock()
	lockToAmazonMsg = threading.RLock()
	receivedW = []
	receivedA = []
	toWorldMsg = SendMsg(lockToWorldMsg)
	toAmazonMsg = SendMsg(lockToAmazonMsg)
	ups(sys.argv)



from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint
from world_ups_pb2 import *
from ups_amazon_pb2 import *
import sys
import threading
import time

class UCommand:
	def __init__(self, simspeed, disconnect, ack):
		self.command = UCommands()
		if(simspeed>=0):
			self.command.simspeed = simspeed
		self.command.disconnect = disconnect
		if(ack>=0):
			self.command.acks.append(ack)
		self.seqnum = -1
		self.sendTime = time.time()

	def addPickups(self, truckid, whid, seqnum):
		ugopickup = UGoPickup()
		ugopickup.truckid = truckid
		ugopickup.whid = whid
		ugopickup.seqnum = seqnum
		self.seqnum = seqnum
		self.command.pickups.append(ugopickup)

	def addDeliveries(self, truckid, packages, seqnum):
		ugodeliver = UGoDeliver()
		ugodeliver.truckid = truckid
		for package in packages:
			ugodeliver.packages.append(package)
		ugodeliver.seqnum = seqnum
		self.seqnum = seqnum
		self.command.deliveries.append(ugodeliver)

	def addQueries(self, truckid, seqnum):
		uquery = UQuery()
		uquery.truckid = truckid
		uquery.seqnum = seqnum
		self.seqnum = seqnum
		self.command.queries.append(uquery)

	def addUAccountConnectionResult(self, uexist, uid, seqnum):
		conn = UAccountConnectionResult()
		conn.uAccountExists = uexist
		conn.uAccountid = uid
		conn.seqnum = seqnum
		self.seqnum = seqnum
		self.command.accountconnectionresult.append(conn)

	'''
	def sendWait(self):
		self.sendMsg()
		time1 = time.time()
		while(1):
			if self.received:
				self.receivedACK = True
				break
			time2 = time.time()
			if(time2-time1 > 30):
				self.sendMsg()
				time1 = time.time()

	def threadSend(self):
		t1 = threading.Thread(target=self.sendWait)
		t1.start()

	def __exit__(self):
		print("The object is deleted")
	'''

class UResponse:
	def __init__(self, comm):
		self.comm = comm

	def readResponse(self):
		if(len(self.comm.completions)):
			for completion in self.comm.completions:
				self.listUFinished(completion)
		if(len(self.comm.acks)):
			for ack in self.comm.acks:
				print("ack is", ack)
		if(len(self.comm.delivered)):
			for delivered_single in self.comm.delivered:
				self.listUDeliveryMade(delivered_single)
		if(self.comm.HasField('finished')):
			print("finished: ", self.comm.finished)
		if(len(self.comm.truckstatus)):
			for status in self.comm.truckstatus:
				self.listUTruck(status)
		if(len(self.comm.error)):
			for err in self.comm.error:
				self.listUErr(err)

	def listUFinished(self, msg):
		print("receive UFinished: truckid =", msg.truckid, " x =", msg.x, " y =", msg.y, " seqnum =", msg.seqnum)

	def listUDeliveryMade(self, msg):
		print("receive UDeliveryMade: truckid =", msg.truckid, " packageid =", msg.packageid, " seqnum =", msg.seqnum)
	def listUTruck(self, msg):
		print("receive UTruck: truckid =", msg.truckid, " x =", msg.x, " y =", msg.y, " status =", msg.status, " seqnum =", msg.seqnum)

	def listUErr(self, msg):
		print("receive UErr: err =", msg.err, " originseqnum =", msg.originseqnum, " seqnum =", msg.seqnum)


class UMessage:
	def __init__(self):
		self.command = UMessages()
		self.seqnum = -1
		self.sendTime = time.time()

	def addUInitialWorldid(self, worldid, seqnum):
		comm = UInitialWorldid()
		comm.worldid.append(worldid)
		comm.seqnum = seqnum
		self.seqnum = seqnum
		self.command.initialWorldid.CopyFrom(comm)

	def addUTruckReady(self, truckid, packageid, seqnum):
		self.seqnum = seqnum
		comm = UTruckReady()
		comm.truckid = truckid
		comm.packageid = packageid
		comm.seqnum = seqnum
		self.command.truckReadies.append(comm)

	def addUAccountResult(self, packageid, exist, uname, uid, seqnum):
		comm = UAccountResult()
		comm.packageid = packageid
		comm.uAccountExists = exist
		comm.uAccountName = uname
		comm.uAccountid = uid
		comm.seqnum = seqnum
		self.command.accountResult.CopyFrom(comm)
		self.seqnum = seqnum

	def addUPackageDelivered(self, packageid, seqnum):
		comm = UPackageDelivered()
		comm.packageid = packageid
		comm.seqnum = seqnum
		self.seqnum = seqnum
		self.command.deliveredpackages.append(comm)


class AMessage:
	def __init__(self, comm):
		self.comm = comm
		self.readComm()

	def readComm(self):
		if(len(self.comm.acks)):
			for ack in self.comm.acks:
				print ("ack is", ack)
		if(len(self.comm.initialWorldid)):
			self.listAInitialWorldid()
		if(len(self.getTrucks)):
			for truck in self.getTrucks:
				self.listAGetTruck(truck)
		if(len(self.delivers)):
			for loc in self.delivers.location:
				self.listADeliver(loc)


	def listAInitialWorldid(self):
		if(len(self.comm.initialWorldid)):
			print("receive initialworldid, seqnum is", self.comm.initialWorldid.seqnum)

	def listAGetTruck(self, truck):
		print("receive getTrucks, whid is", truck.whid, " seqnum is", truck.seqnum,\
			 " world id is", truck.worldid)

	def listADeliver(self, location):
		print("receive deliver, package id is",location.packageid, " x is", location.x, " y is", location.y)







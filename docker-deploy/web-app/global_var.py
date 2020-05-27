

#sendW  = {}
#worldSeq = set()
import threading

lockTrucks = threading.RLock()
lockToWorldSeq = threading.RLock()
lockToAmazonSeq = threading.RLock()

class Trucks:
	# -1: available
	# -2: not available
	# >=0: only available for specific warehouse
	def __init__(self, numTruck):
		self.truckList = []
		for i in range(numTruck):
			self.truckList.append(-1)

	def getTruckWh(self, whid):
		with lockTrucks:
			try:
				return self.truckList.index(whid)
			except:
				truckid = self.truckList.index(-1)
				self.truckList[truckid] = whid
				return truckid

	def truckToDeliver(self, truckid):
		with lockTrucks:
			self.truckList[truckid] = -2

	def truckToIdle(self, truckid):
		with lockTrucks:
			self.truckList[truckid] = -1

	def getWhid(self, truckid):
		with lockTrucks:
			return self.truckList[truckid]

class SeqCounter:
	def __init__(self):
		self.worldSeq = 0
		self.amazonSeq = 0

	def getWorldSeq(self):
		with lockToWorldSeq:
			self.worldSeq = self.worldSeq + 1
			return self.worldSeq

	def getAmazonSeq(self):
		with lockToAmazonSeq:
			self.amazonSeq = self.amazonSeq + 1
			return self.amazonSeq


class SendMsg:
	def __init__ (self, lock):
		self.dict = {}
		self.lock = lock

	def addMsg(self, seqnum, msg):
		with self.lock:
			self.dict[seqnum] = msg

	def delMsg(self, seqnum):
		with self.lock:
			if seqnum in self.dict:
				del self.dict[seqnum]

	def updateMsg(self, seqnum, newMsg):
		with self.lock:
			if seqnum in self.dict:
				self.dict[seqnum] = newMsg

	def getMsg(self, seqnum):
		with self.lock:
			return self.dict.get(seqnum)

	def getKeys(self):
		with self.lock:
			return list(self.dict)









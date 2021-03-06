from pyo5m import o5m
import gzip, sys

#Used to renumber ways as OsmAnd map creator does not like 64-bit ways

class RenumberWaysRels(object):
	def __init__(self, output):
		self.output = output
		self.wayRemap = {}
		self.relRemap = {}
		self.nextWay = 1
		self.nextRel = 1
		self.prevType = None
		self.countNodes = 0
		self.countWays = 0
		self.countRelations = 0

	def __del__(self):
		self.output.Finish()

	def StoreIsDiff(self, isDiff):
		self.output.StoreIsDiff(isDiff)

	def StoreBounds(self, bbox):
		self.output.StoreBounds(bbox)

	def StoreNode(self, objectId, metaData, tags, pos):
		if self.prevType is not None and self.prevType != "n":
			self.output.Reset()
		self.output.StoreNode(objectId, metaData, tags, pos)
		self.prevType = "n"
		self.countNodes += 1
		if self.countNodes % 1000 == 0:
			print (self.countNodes)

	def StoreWay(self, objectId, metaData, tags, refs):
		if self.prevType is not None and self.prevType != "w":
			self.output.Reset()
		if objectId in self.wayRemap:
			self.output.StoreWay(self.wayRemap[objectId], metaData, tags, refs)
		else:
			self.wayRemap[objectId] = self.nextWay
			self.output.StoreWay(self.nextWay, metaData, tags, refs)
			self.nextWay += 1
		self.prevType = "w"
		self.countWays += 1
		if self.countWays % 1000 == 0:
			print (self.countWays)

	def StoreRelation(self, objectId, metaData, tags, refs):
		if self.prevType is not None and self.prevType != "r":
			self.output.Reset()

		remappedRefs = []
		for typeStr, refId, role in refs:
			if typeStr == "node":
				remappedRefs.append((typeStr, refId, role))
			elif typeStr == "way":
				if refId in self.wayRemap:
					remappedRefs.append((typeStr, self.wayRemap[refId], role))
				else:
					self.wayRemap[objectId] = self.nextWay
					remappedRefs.append((typeStr, self.nextWay, role))
					self.nextWay += 1
			elif typeStr == "relation":
				if refId in self.relRemap:
					remappedRefs.append((typeStr, self.relRemap[refId], role))
				else:
					self.relRemap[objectId] = self.nextRel
					remappedRefs.append((typeStr, self.nextRel, role))
					self.nextRel += 1

		if objectId in self.relRemap:
			self.output.StoreRelation(self.relRemap[objectId], metaData, tags, remappedRefs)
		else:
			self.relRemap[objectId] = self.nextRel
			self.output.StoreRelation(objectId, metaData, tags, remappedRefs)
			self.nextRel += 1
		self.prevType = "r"
		self.countRelations += 1
		if self.countRelations % 1000 == 0:
			print (self.countRelations)

if __name__ == "__main__":

	finaIn = "uk-eire-fosm-2017-jan.o5m.gz"
	finaOut = "renumbered.o5m.gz"

	if len(sys.argv) >= 2:
		finaIn = sys.argv[1]
	if len(sys.argv) >= 3:
		finaOut = sys.argv[2]
	fiIn = gzip.open(finaIn, "rb")
	fiOut = gzip.open(finaOut, "wb")

	dec = o5m.O5mDecode(fiIn)
	enc = o5m.O5mEncode(fiOut)
	filt = RenumberWaysRels(enc)

	dec.funcStoreNode = filt.StoreNode
	dec.funcStoreWay = filt.StoreWay
	dec.funcStoreRelation = filt.StoreRelation
	dec.funcStoreBounds = filt.StoreBounds
	dec.funcStoreIsDiff = filt.StoreIsDiff
	dec.DecodeHeader()

	eof = False
	while not eof:
		eof = dec.DecodeNext()

	del dec
	del filt
	del enc
	fiOut.close()


#MenuTitle: Place Mosaic Tiles along Paths
# -*- coding: utf-8 -*-

from GlyphsApp import *
from Foundation import NSPoint
from AppKit import NSAffineTransform
import math
import random

FONT = Glyphs.font
def getLayers():
	layers = FONT.selectedLayers
	if layers and len(layers) > 0:
		return layers
	# Fallback: process all glyphs in current master
	masterId = FONT.selectedFontMaster.id
	return [g.layers[masterId] for g in FONT.glyphs]

# --------------------------------------------------

# PARAMETERS

TILE_SIZE = 30
ROW_OFFSET = 20
BASE_GROUT = 7
GROUT_RANDOM = 1.5
RANDOM_SHIFT = 2
RANDOM_ROTATION = 3
FLATNESS = 0.3

# --------------------------------------------------

# HELPERS

def buildSegments(points):
	segments = []
	totalLength = 0
	for i in range(len(points)-1):
		p1 = points[i]
		p2 = points[i+1]
		dx = p2.x - p1.x
		dy = p2.y - p1.y
		segLen = math.hypot(dx, dy)
		if segLen < 0.001:
			continue
		segments.append({
			"p1": p1,
			"p2": p2,
			"len": segLen,
			"start": totalLength,
			"end": totalLength + segLen
		})
		totalLength += segLen
	return segments, totalLength

def pointAndAngleAtDistance(segments, targetDist):
	for seg in segments:
		if seg["start"] <= targetDist <= seg["end"]:
			localDist = targetDist - seg["start"]
			t = localDist / seg["len"]
			p1 = seg["p1"]
			p2 = seg["p2"]
			x = p1.x + (p2.x - p1.x) * t
			y = p1.y + (p2.x - p1.x) * 0 + (p2.y - p1.y) * t
			ang = math.atan2(p2.y - p1.y, p2.x - p1.x)
			return NSPoint(x, y), ang
	return None, 0

def createSquare(center, size, rotation):
	half = size / 2
	pts = [
		NSPoint(-half, -half),
		NSPoint( half, -half),
		NSPoint( half,  half),
		NSPoint(-half,  half),
	]
	transform = NSAffineTransform.transform()
	transform.translateXBy_yBy_(center.x, center.y)
	transform.rotateByDegrees_(rotation)
	path = GSPath()
	for p in pts:
		tp = transform.transformPoint_(p)
		# Integer coordinate normalization
		tp = NSPoint(round(tp.x), round(tp.y))
		node = GSNode(tp)
		node.type = LINE
		path.nodes.append(node)
	path.closed = True
	return path

def pointDistance(p1, p2):
	return math.hypot(p2.x - p1.x, p2.y - p1.y)

def lineIntersection(p1, p2, p3, p4):
	x1, y1 = p1.x, p1.y
	x2, y2 = p2.x, p2.y
	x3, y3 = p3.x, p3.y
	x4, y4 = p4.x, p4.y
	den = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
	if abs(den) < 0.00001:
		return None
	px = ((x1*y2 - y1*x2)*(x3-x4) - (x1-x2)*(x3*y4 - y3*x4)) / den
	py = ((x1*y2 - y1*x2)*(y3-y4) - (y1-y2)*(x3*y4 - y3*x4)) / den
	return NSPoint(px, py)

# Produces parallel offset curve by offsetting each segment and intersecting adjacent offset segments
# This avoids drift that would occur from naive vertex offsets
def offsetPolyline(points, offset):
	if len(points) < 2:
		return []
	offsetSegments = []
	# Build offset segments
	for i in range(len(points)-1):
		p1 = points[i]
		p2 = points[i+1]
		dx = p2.x - p1.x
		dy = p2.y - p1.y
		length = math.hypot(dx, dy)
		if length < 0.001:
			continue
		tx = dx / length
		ty = dy / length
		nx = -ty
		ny = tx
		op1 = NSPoint(p1.x + nx * offset, p1.y + ny * offset)
		op2 = NSPoint(p2.x + nx * offset, p2.y + ny * offset)
		offsetSegments.append((op1, op2))
	if len(offsetSegments) == 0:
		return []
	result = []
	# First point
	result.append(offsetSegments[0][0])
	# Interior joints
	for i in range(len(offsetSegments)-1):
		a1, a2 = offsetSegments[i]
		b1, b2 = offsetSegments[i+1]
		inter = lineIntersection(a1, a2, b1, b2)
		if inter is None:
			# Fallback for parallel segments
			inter = a2
		result.append(inter)
	# Last point
	result.append(offsetSegments[-1][1])
	return result

# --------------------------------------------------

# CORE ALGORITHM

# Tile placement is driven by arc-length sampling of a flattened Bézier path
# Two corrections are applied:
# 1) Local collision correction (forward push) to avoid overlap at sharp bends
# 2) Global drift correction to preserve endpoint alignment
def generateRow(points, tilesToAdd):
	segments, totalLength = buildSegments(points)
	if totalLength <= TILE_SIZE:
		return
	estimatedStep = TILE_SIZE + BASE_GROUT
	tileCount = int(math.floor((totalLength + BASE_GROUT) / estimatedStep))
	if tileCount < 2:
		tileCount = 2
	# First compute *candidate tile centers in path space* instead of placing tiles immediately
	# This allows post-correction (drift alignment)
	# Build raw distances
	distances = []
	d = TILE_SIZE / 2
	previousCenter = None
	MIN_CENTER_DISTANCE = TILE_SIZE + BASE_GROUT
	FORWARD_PUSH = 3
	for i in range(tileCount):
		center, ang = pointAndAngleAtDistance(segments, d)
		if center is None:
			break
		# Local collision correction
		# If a tile would land too close (in Euclidean space) to the previous tile due to path folding (sharp turns), we advance along the path until spacing is valid
		# Adaptive push-forward
		if previousCenter is not None:
			safety = 0
			while pointDistance(center, previousCenter) < MIN_CENTER_DISTANCE:
				d += FORWARD_PUSH
				if d >= totalLength:
					break
				center, ang = pointAndAngleAtDistance(segments, d)
				if center is None:
					break
				safety += 1
				if safety > 100:
					break
		if center is None:
			break
		distances.append(d)
		previousCenter = center
		# Next nominal step
		grout = BASE_GROUT + random.uniform(-GROUT_RANDOM, GROUT_RANDOM)
		d += TILE_SIZE + grout
	if len(distances) < 2:
		return
	# Global correction
	# Because local collision pushing slightly increases total path travel, we redistribute the accumulated drift so the last tile aligns with the path endpoint
	# End alignment correction
	desiredEnd = totalLength - TILE_SIZE / 2
	actualEnd = distances[-1]
	drift = desiredEnd - actualEnd
	# Distribute correction smoothly
	correctedDistances = []
	for i, dist in enumerate(distances):
		t = float(i) / float(len(distances)-1)
		correctedDistances.append(dist + drift * t)
	# Create tiles
	for d in correctedDistances:
		center, ang = pointAndAngleAtDistance(segments, d)
		if center is None:
			continue
		cx = center.x + random.uniform(-RANDOM_SHIFT, RANDOM_SHIFT)
		cy = center.y + random.uniform(-RANDOM_SHIFT, RANDOM_SHIFT)
		rot = math.degrees(ang)
		rot += random.uniform(-RANDOM_ROTATION, RANDOM_ROTATION)
		tile = createSquare(NSPoint(cx, cy), TILE_SIZE, rot)
		tilesToAdd.append(tile)

# --------------------------------------------------
	
# Process layer
def computeLayerTiles(LAYER):
	# Collect tiles here before placing them onto layer
	tilesToAdd = []
	# Process all paths on the layer
	sourcePaths = [
		p for p in LAYER.paths
		if isinstance(p, GSPath)
	]
	for sourcePath in sourcePaths:
		bezier = sourcePath.bezierPath
		bezier.setFlatness_(FLATNESS)
		flat = bezier.bezierPathByFlatteningPath()
		centerPoints = []
		for i in range(flat.elementCount()):
			etype, pts = flat.elementAtIndex_associatedPoints_(i)
			if etype in [0, 1]:
				centerPoints.append(pts[0])
		if len(centerPoints) < 2:
			continue
		# --------------------------------------------------
		# Collect row points for each side of the path
		leftPoints = offsetPolyline(centerPoints, ROW_OFFSET)
		rightPoints = offsetPolyline(centerPoints, -ROW_OFFSET)
		# Generate tiles along each row
		generateRow(leftPoints, tilesToAdd)
		generateRow(rightPoints, tilesToAdd)
	return sourcePaths, tilesToAdd

# --------------------------------------------------

# MAIN PROCESS

FONT.disableUpdateInterface()
try:
	# Process selected layers or all glyphs
	for LAYER in getLayers():
		# Collect tiles for current layer
		sourcePaths, tilesToAdd = computeLayerTiles(LAYER)
		# Remove original construction paths
		for p in sourcePaths:
			if p in LAYER.paths:
				LAYER.removeShape_(p)
		# Add generated mosaic tiles
		for t in tilesToAdd:
			LAYER.paths.append(t)
except Exception as e:
	print("Error in Place Mosaic Tiles:", e)
finally:
	FONT.enableUpdateInterface()
	Glyphs.redraw()
	

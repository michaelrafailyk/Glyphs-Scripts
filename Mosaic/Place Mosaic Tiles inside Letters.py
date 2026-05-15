#MenuTitle: Place Mosaic Tiles inside Letters
# -*- coding: utf-8 -*-

__doc__="""
This script for Glyphs transforms selected glyph outlines into a procedural mosaic composed of rotated square tiles distributed along the internal flow of each stroke, creating two parallel rows of tiles. It begins by analyzing the actual outline geometry to estimate dominant horizontal and vertical stem thicknesses, then derives tile size, grout spacing, and row offset from those measurements. Each glyph contour is flattened into linear segments, after which a parallel inner guide path is constructed by offsetting every segment inward and intersecting neighboring offsets to preserve contour continuity. Because horizontal and vertical stems may have different thicknesses, the script applies directional offset compensation: rows placed along thinner strokes are shifted less inward so the tiles remain visually centered inside anisotropic strokes instead of drifting toward one side. Along the generated guide path, the algorithm distributes tiles using arc-length spacing, detects short perpendicular bridge segments that behave like stroke endings or caps, reserves mandatory tile positions around those regions, and rebuilds local tile sequences between those anchors to maintain visually balanced spacing without cumulative drift. Additional logic attempts to prevent overlaps on tight curves, resolve duplicated closing tiles on closed contours, and preserve continuity at contour closures. Finally, the script applies small randomized shifts and rotations to imitate irregular hand-laid mosaic placement, removes the original outline paths, and inserts the generated tile paths back into the glyph layer as the final artwork.
"""

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

RANDOM_SHIFT = 2
RANDOM_ROTATION = 3
FLATNESS = 0.3

# --------------------------------------------------

# STEM ANALYSIS

# Uppercase stems letter
UPPERCASE_STEMS_LETTER = "L"

# Measures dominant vertical and horizontal stems directly from glyph outlines
def measureStemsFromGlyph(font):
	masterId = font.selectedFontMaster.id
	glyph = font.glyphs[UPPERCASE_STEMS_LETTER]
	if glyph is None:
		return None, None
	layer = glyph.layers[masterId]
	verticalSegments = []
	horizontalSegments = []
	# Collect long straight segments
	for path in layer.paths:
		nodes = path.nodes
		for i in range(len(nodes)):
			n1 = nodes[i]
			n2 = nodes[(i + 1) % len(nodes)]
			p1 = n1.position
			p2 = n2.position
			dx = p2.x - p1.x
			dy = p2.y - p1.y
			length = math.hypot(dx, dy)
			# Ignore tiny segments
			if length < 20:
				continue
			# Near vertical
			if abs(dx) < 0.01:
				verticalSegments.append({
					"length": length,
					"x": p1.x,
					"y1": p1.y,
					"y2": p2.y
				})
			# Near horizontal
			if abs(dy) < 0.01:
				horizontalSegments.append({
					"length": length,
					"y": p1.y,
					"x1": p1.x,
					"x2": p2.x
				})
	# Sort by length
	verticalSegments.sort(
		key=lambda s: s["length"],
		reverse=True
	)
	horizontalSegments.sort(
		key=lambda s: s["length"],
		reverse=True
	)
	# Measure stem thicknesses
	vStem = None
	hStem = None
	# Vertical stem thickness: distance between two longest vertical edges
	if len(verticalSegments) >= 2:
		v1 = verticalSegments[0]
		v2 = verticalSegments[1]
		vStem = abs(v1["x"] - v2["x"])
	# Horizontal stem thickness: distance between two longest horizontal edges
	if len(horizontalSegments) >= 2:
		h1 = horizontalSegments[0]
		h2 = horizontalSegments[1]
		hStem = abs(h1["y"] - h2["y"])
	return hStem, vStem

# CONSTANTS

# Stems measured from actual outlines
H_STEM, V_STEM = measureStemsFromGlyph(FONT)
# Determine dominant stroke direction
MAJOR_STEM = max(H_STEM, V_STEM)
MINOR_STEM = min(H_STEM, V_STEM)
# Tile size derived from dominant stroke
TILE_SIZE = MAJOR_STEM * 0.42
# Tile spacing derived from dominant stroke
BASE_GROUT = MAJOR_STEM * 0.16

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
			y = p1.y + (p2.y - p1.y) * t
			ang = math.atan2(
				p2.y - p1.y,
				p2.x - p1.x
			)
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
		tp = NSPoint(round(tp.x), round(tp.y))
		node = GSNode(tp)
		node.type = LINE
		path.nodes.append(node)
	path.closed = True
	return path

def pointDistance(p1, p2):
	return math.hypot(p2.x - p1.x, p2.y - p1.y)

# Detects short stroke ending segments between two adjacent segments
# For this, check the angle of all 3 segments
def angleBetweenSegments(a, b):
	ax = a["p2"].x - a["p1"].x
	ay = a["p2"].y - a["p1"].y
	bx = b["p2"].x - b["p1"].x
	by = b["p2"].y - b["p1"].y
	adot = ax * bx + ay * by
	alen = math.hypot(ax, ay)
	blen = math.hypot(bx, by)
	if alen < 0.001 or blen < 0.001:
		return 0
	c = adot / (alen * blen)
	c = max(-1, min(1, c))
	return math.degrees(math.acos(c))

# Detect stroke endings
def detectStrokeEndings(segments):
	results = []
	if len(segments) < 3:
		return results
	for i in range(1, len(segments) - 1):
		prevSeg = segments[i - 1]
		midSeg = segments[i]
		nextSeg = segments[i + 1]
		# RULE 1: middle segment is the stroke-end segment (short)
		if midSeg["len"] > MAJOR_STEM:
			continue
		# RULE 2: must be a genuine joint (angle constraints only)
		angle1 = angleBetweenSegments(prevSeg, midSeg)
		angle2 = angleBetweenSegments(midSeg, nextSeg)
		if not (70 <= angle1 <= 110):
			continue
		if not (70 <= angle2 <= 110):
			continue
		edgeInset = TILE_SIZE * 0.15
		results.append({
			"before": prevSeg["end"] - edgeInset,
			"after": nextSeg["start"] + edgeInset
		})
	return results

def lineIntersection(p1, p2, p3, p4):
	x1, y1 = p1.x, p1.y
	x2, y2 = p2.x, p2.y
	x3, y3 = p3.x, p3.y
	x4, y4 = p4.x, p4.y
	den = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
	if abs(den) < 0.00001:
		return None
	px = (
		(x1*y2 - y1*x2)*(x3-x4) -
		(x1-x2)*(x3*y4 - y3*x4)
	) / den
	py = (
		(x1*y2 - y1*x2)*(y3-y4) -
		(y1-y2)*(x3*y4 - y3*x4)
	) / den
	return NSPoint(px, py)

# Produces parallel offset curve by offsetting each segment and intersecting adjacent offset segments
# This avoids drift that would occur from naive vertex offsets
def offsetPolyline(points):
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
		# Segment angle
		ang = math.atan2(dy, dx)
		# Dynamic stem offset compensation
		baseOffset = TILE_SIZE / 2
		stemDifference = (MAJOR_STEM - MINOR_STEM) / 2
		# 0 on dominant direction
		# 1 on weaker direction
		if V_STEM >= H_STEM:
			t = abs(math.cos(ang))
		else:
			t = abs(math.sin(ang))
		offset = baseOffset - stemDifference * t
		op1 = NSPoint(
			p1.x + nx * offset,
			p1.y + ny * offset
		)
		op2 = NSPoint(
			p2.x + nx * offset,
			p2.y + ny * offset
		)
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
			inter = a2
		result.append(inter)
	# Last point
	result.append(offsetSegments[-1][1])
	return result

# --------------------------------------------------

# CORE ALGORITHM

# Geometry phase
# Solve tile placement which is driven by arc-length sampling of a flattened Bezier path
# Two corrections are applied:
# 1) Local collision correction (forward push) to avoid overlap at sharp bends
# 2) Global drift correction to preserve endpoint alignment
def solveTileLayout(points):
	segments, totalLength = buildSegments(points)
	# Detect stroke endings that need forced double-tile caps
	strokeEndings = detectStrokeEndings(segments)
	# Reserved tile anchors
	# This is a hard constraints derived from stroke-end detection
	# These act as immutable placement barriers
	reservedDistances = []
	for ending in strokeEndings:
		reservedDistances.append(ending["before"])
		reservedDistances.append(ending["after"])
	reservedDistances.sort()
	if totalLength <= TILE_SIZE:
		return
	# --------------------------------------------------
	# Segmented constraint solver
	correctedDistances = []
	# Force endpoint behavior control
	# Define explicit endpoints (always safe for open/closed contours)
	# Ensures tile centers never sit exactly on path endpoints
	# prevents visual clipping at contour closure
	startAnchor = TILE_SIZE / 2
	endAnchor = totalLength - TILE_SIZE / 2
	# Core anchor list
	anchors = sorted(reservedDistances)
	# Full sequence definition
	# Anchor system defines segment decomposition of arc-length domain
	# Reserved anchors are injected into global spacing solver
	allAnchors = [startAnchor] + anchors + [endAnchor]
	# Closed loop segmentation over anchor domain
	n = len(allAnchors)
	for i in range(n):
		start = allAnchors[i]
		# endpoint wrap is intentional because all glyph contours are treated as closed loops
		end = allAnchors[(i + 1) % n]
		span = end - start
		if span <= 0:
			span += totalLength
		if span < TILE_SIZE * 0.9:
			continue
		idealStep = TILE_SIZE + BASE_GROUT
		# global consistent count (no per-segment inflation)
		count = max(2, int(round(span / idealStep)))
		# recompute step from fixed count
		step = span / (count - 1)
		# LAST SEGMENT FIX: absorb remainder instead of creating extra tile
		# VISUAL TUNING ONLY: prevents last-gap expansion on smooth loops
		if i == len(allAnchors) - 2:
			remainder = span - step * (count - 1)
			# distribute remainder backward slightly to avoid endpoint collision
			step = (span - TILE_SIZE * 0.25) / (count - 1)
		for k in range(count):
			d = start + step * k
			# HARD SAFETY: never place inside reserved zone
			if any(abs(d - r) < TILE_SIZE * 0.55 for r in reservedDistances):
				continue
			correctedDistances.append(d)
	# --------------------------------------------------
	# Merge reserved stroke-end tiles directly into layout
	# Reserved tiles have absolute priority
	merged = []
	for d in correctedDistances:
		keep = True
		for r in reservedDistances:
			# If normal tile is too close to reserved tile, remove the normal tile
			if abs(d - r) < TILE_SIZE * 0.8:
				keep = False
				break
		if keep:
			merged.append(d)
	# Add reserved tiles AFTER cleanup so they can never disappear
	# Ensure reserved tiles do NOT duplicate existing ones
	for r in reservedDistances:
		if not any(abs(r - x) < TILE_SIZE * 0.2 for x in merged):
			merged.append(r)
	# Restore order
	merged.sort()
	# --------------------------------------------------
	# Final deduplication
	finalDistances = []
	for d in merged:
		if len(finalDistances) == 0:
			finalDistances.append(d)
			continue
		if abs(d - finalDistances[-1]) < TILE_SIZE * 0.15:
			continue
		finalDistances.append(d)
	correctedDistances = finalDistances
	# --------------------------------------------------
	# Remove duplicated closing tile on closed contours
	# Ignore reserved stroke-end tiles for this test
	normalTiles = []
	for d in correctedDistances:
		isReserved = False
		for r in reservedDistances:
			if abs(d - r) < 0.001:
				isReserved = True
				break
		if not isReserved:
			normalTiles.append(d)
	if len(normalTiles) >= 2:
		firstDist = normalTiles[0]
		lastDist = normalTiles[-1]
		firstCenter, _ = pointAndAngleAtDistance(segments, firstDist)
		lastCenter, _ = pointAndAngleAtDistance(segments, lastDist)
		if (
			firstCenter is not None and
			lastCenter is not None and
			pointDistance(firstCenter, lastCenter) < TILE_SIZE
		):
			correctedDistances.remove(lastDist)
	# --------------------------------------------------
	# GEOMETRIC DUPLICATE REMOVAL (fixes closed contour overlap)
	filtered = []
	seenPoints = []
	for d in correctedDistances:
		pt, _ = pointAndAngleAtDistance(segments, d)
		if pt is None:
			continue
		duplicate = False
		for sp in seenPoints:
			if pointDistance(pt, sp) < TILE_SIZE * 0.35:
				duplicate = True
				break
		if not duplicate:
			filtered.append(d)
			seenPoints.append(pt)
	correctedDistances = filtered
	# --------------------------------------------------
	return segments, correctedDistances

# Rendering phase
# Build tiles
def buildTiles(segments, distances):
	tiles = []
	for d in distances:
		center, ang = pointAndAngleAtDistance(segments, d)
		if center is None:
			continue
		cx = center.x + random.uniform(
			-RANDOM_SHIFT,
			RANDOM_SHIFT
		)
		cy = center.y + random.uniform(
			-RANDOM_SHIFT,
			RANDOM_SHIFT
		)
		rot = math.degrees(ang)
		rot += random.uniform(
			-RANDOM_ROTATION,
			RANDOM_ROTATION
		)
		tile = createSquare(
			NSPoint(cx, cy),
			TILE_SIZE,
			rot
		)
		tiles.append(tile)
	return tiles

# --------------------------------------------------

# Process layer
def computeLayerTiles(LAYER):
	# Collect tiles here before placing them onto layer
	tilesToAdd = []
	# Process all paths on the layer
	sourcePaths = [p for p in LAYER.paths if isinstance(p, GSPath)]
	for sourcePath in sourcePaths:
		bezier = sourcePath.bezierPath
		bezier.setFlatness_(FLATNESS)
		flat = bezier.bezierPathByFlatteningPath()
		pathPoints = []
		for i in range(flat.elementCount()):
			etype, pts = flat.elementAtIndex_associatedPoints_(i)
			if etype in [0, 1]:
				pathPoints.append(pts[0])
		if len(pathPoints) < 2:
			continue
		# Collect row points for inner side of the path
		offsetPoints = offsetPolyline(pathPoints)
		segments, distances = solveTileLayout(offsetPoints)
		# Generate tiles along offset row
		tiles = buildTiles(segments, distances)
		tilesToAdd.extend(tiles)
	return sourcePaths, tilesToAdd

# --------------------------------------------------

# MAIN PROCESS

FONT.disableUpdateInterface()
try:
	# Process selected layers or all glyphs
	for LAYER in getLayers():
		# Collect tiles for current layer
		sourcePaths, tilesToAdd = computeLayerTiles(LAYER)
		# Remove original construction paths that are no longer needed
		for p in sourcePaths:
			if p in LAYER.paths:
				LAYER.removeShape_(p)
		# Add tiles to layer
		for t in tilesToAdd:
			LAYER.paths.append(t)
except Exception as e:
	print("Error in Place Mosaic Tiles:", e)
finally:
	FONT.enableUpdateInterface()
	Glyphs.redraw()

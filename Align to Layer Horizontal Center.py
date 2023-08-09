#MenuTitle: Align to Layer Horizontal Center
from __future__ import division
from math import radians, tan
__doc__="""
Align selection to horizontal center of the layer.
"""

layer = Glyphs.font.selectedLayers[0]
selection = layer.selection
if len(selection) > 0:

	# detect if the selection contains only nodes or only one component
	onlyNodes = True
	onlyComponent = True
	componentsCount = 0
	for element in selection:
		if type(element) != GSNode and onlyNodes == True:
			onlyNodes = False
		if type(element) != GSComponent and onlyComponent == True:
			onlyComponent = False
		if type(element) == GSComponent:
			componentsCount += 1
	if onlyComponent and componentsCount != 1:
		onlyComponent = False
	# ignore the handles positions if only nodes are selected (not components/anchors/guides)
	if onlyNodes:
		box = layer.selectionPath().bounds()
	else:
		box = layer.selectionBounds

	# find the horizontal difference between the layer center and the selection center
	layerCenterX = layer.width / 2
	selectionCenterX = box.origin.x + box.size.width / 2
	shift = layerCenterX - selectionCenterX

	# take into account the italic angle if set
	italicAngle = layer.master.italicAngle
	if italicAngle != 0:
		# get an italic vertical 0 origin
		italicVerticalZero = 0
		if 'e+' not in str(layer.master.xHeight):
			italicVerticalZero = layer.master.xHeight / 2
		italicAngleRadiansTan = tan(radians(italicAngle))
		# find the left and right extremes respected to italic angle
		extremeLeft = False
		extremeRight = False
		if onlyNodes:
			# for nodes
			for node in selection:
				# ignoring the handles
				if type(node) == GSNode and node.type != OFFCURVE:
					x = node.x + italicAngleRadiansTan * (italicVerticalZero - node.y)
					if extremeLeft == False or x < extremeLeft:
						extremeLeft = x
					if extremeRight == False or x > extremeRight:
						extremeRight = x
			# get slanted shift
			shift = -(extremeLeft + (extremeRight - extremeLeft) / 2 - layerCenterX)
		elif onlyComponent:
			# for components
			# find the left and right extremes inside the component and respected to italic angle
			componentHome = element.component.layers[Layer.associatedMasterId]
			for path in componentHome.paths:
				for node in path.nodes:
					# ignoring the handles
					if type(node) == GSNode and node.type != OFFCURVE:
						x = node.x + italicAngleRadiansTan * (italicVerticalZero - node.y)
						if extremeLeft == False or x < extremeLeft:
							extremeLeft = x
						if extremeRight == False or x > extremeRight:
							extremeRight = x
			# get component shift
			componentShift = element.x - (italicAngleRadiansTan * element.y)
			# get slanted shift
			shift = -(extremeLeft + (extremeRight - extremeLeft) / 2 - layerCenterX + componentShift)
		else:
			# for components/anchors/guides
			selectionCenterY = box.origin.y + box.size.height / 2
			shift -= italicAngleRadiansTan * (italicVerticalZero - selectionCenterY)

	shift = int(shift)
	# move selection
	for node in selection:
		node.x += shift
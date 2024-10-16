#MenuTitle: Rotate on 180 Degree
from Foundation import NSAffineTransform, NSMidX, NSMidY
__doc__="""
Rotate selection on 180 degree, set the new first node and correct path direction.
"""

layer = Glyphs.font.selectedLayers[0]
selection = layer.selection
bounds = layer.boundsOfSelection() if len(selection) > 0 else layer.bounds
# flip horizontal
transform = NSAffineTransform.new()
transform.translateXBy_yBy_(NSMidX(bounds), NSMidY(bounds))
transform.scaleXBy_yBy_(-1, -1)
transform.translateXBy_yBy_(-NSMidX(bounds), -NSMidY(bounds))
layer.transformSelection_(transform)
# set new first node
if len(selection) > 0:
	for path in layer.paths:
		if path.nodes[0] in selection:
			candidate = {
				'node': False,
				'x': False,
				'y': False
			}
			# find the lowest left node
			for node in path.nodes:
				if type(node) == GSNode and node.type != OFFCURVE:
					# compare node to candidate
					candidateIsEmpty = candidate['x'] == False and candidate['y'] == False
					if candidateIsEmpty or int(node.y) < candidate['y'] or (int(node.y) == candidate['y'] and int(node.x) < candidate['x']):
						# save the better candidate
						candidate['node'] = node
						candidate['x'] = int(node.x)
						candidate['y'] = int(node.y)
			# set the new first node
			path.makeNodeFirst_(candidate['node'])
# correct path direction
layer.correctPathDirection()
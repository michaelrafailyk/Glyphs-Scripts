#MenuTitle: Generate Kern Strings
# -*- coding: utf-8 -*-
from __future__ import print_function
__doc__="""
Generate kern strings based on the Left and Right groups and add them into the Sample Texts.
"""
# Copyright: Michael Rafailyk, 2023-2025, Version 1.3

group = {
	'left': {
		'name': [],
		'uppercase': [],
		'lowercase': [],
		'figure': [],
		'punctuation': [],
		'georgian': [],
		'armenian': [],
		'sc': [],
		'other': []
	},
	'right': {
		'name': [],
		'uppercase': [],
		'lowercase': [],
		'figure': [],
		'georgian': [],
		'armenian': [],
		'punctuation': [],
		'sc': [],
		'other': []
	}
}

strings = {
	'left': '',
	'leftGeorgian': '',
	'leftArmenian': '',
	'category': 0,
	'name': '',
	'text': ''
}

font = Glyphs.font

# Get the left and right unique groups and its characters
def getUniqueGroups():
	if font:
		for glyph in font.glyphs:
			if glyph.leftKerningGroup and glyph.leftKerningGroup not in group['left']['name']:
				getGlyphData(glyph, 'left')
			if glyph.rightKerningGroup and glyph.rightKerningGroup not in group['right']['name']:
				getGlyphData(glyph, 'right')
		# Sort elements inside the groups categories
		group['left']['uppercase'].sort()
		group['left']['lowercase'].sort()
		group['left']['figure'].sort()
		# group['left']['georgian'].sort()
		# group['left']['armenian'].sort()
		group['left']['sc'].sort()
		group['left']['sc'].sort(key=len)
		group['right']['uppercase'].sort()
		group['right']['lowercase'].sort()
		group['right']['figure'].sort()
		# group['right']['georgian'].sort()
		# group['right']['armenian'].sort()
		group['right']['sc'].sort()
		group['right']['sc'].sort(key=len)
	else:
		Glyphs.clearLog()
		Glyphs.showMacroWindow()
		print('Please open the font first')

# Sort unique groups and its characters by category and add them to the group array
def getGlyphData(glyph, side):
	global group
	groupName = ''
	if side == 'left':
		groupName = glyph.leftKerningGroup
	if side == 'right':
		groupName = glyph.rightKerningGroup
	# Write the group name
	group[side]['name'].append(groupName)
	character = ''
	if font.glyphs[groupName]:
		# Try to find a glyph with the same name as the name of this group
		glyph = font.glyphs[groupName]
		if font.glyphs[groupName].string:
			character = glyph.string
		else:
			character = '/' + groupName + ' '
	elif glyph.string:
		# Get the character of current glyph
		character = glyph.string
	else:
		# Get the glyph name (for glyphs with suffixes)
		character = '/' + glyph.name + ' '
	if character == '/':
		# Correct the name for a slash character
		character = '//';
	# Write the character to appropriate category
	if '.sc' in groupName:
		group[side]['sc'].append('/' + glyph.name)
	elif glyph.category == 'Letter' and glyph.script == 'georgian':
		group[side]['georgian'].append(character)
	elif glyph.category == 'Letter' and glyph.script == 'armenian':
		group[side]['armenian'].append(character)
	elif glyph.category == 'Letter' and glyph.case == 1:
		group[side]['uppercase'].append(character)
	elif glyph.category == 'Letter' and glyph.case == 2:
		group[side]['lowercase'].append(character)
	elif glyph.category == 'Number':
		group[side]['figure'].append(character)
	elif glyph.category == 'Punctuation':
		group[side]['punctuation'].append(character)
	else:
		group[side]['other'].append(character)

# Print groups to the Macro Panel output
def printGroups():
	if font:
		global group
		if group['left']['name'] and group['right']['name']:
			leftGroup = ''.join(group['left']['uppercase'] + group['left']['lowercase'] + group['left']['figure'] + group['left']['punctuation'] + group['left']['other'] + group['left']['sc'])
			rightGroup = ''.join(group['right']['uppercase'] + group['right']['lowercase'] + group['right']['figure'] + group['right']['punctuation'] + group['right']['other'] + group['right']['sc'])
			leftGroupGeorgian = ''.join(group['left']['georgian'])
			rightGroupGeorgian = ''.join(group['right']['georgian'])
			leftGroupArmenian = ''.join(group['left']['armenian'])
			rightGroupArmenian = ''.join(group['right']['armenian'])
			print('Right Groups – Latin/Greek/Cyrillic/Figures/Punctuation:')
			print(rightGroup)
			print()
			print('Left Groups – Latin/Greek/Cyrillic/Figures/Punctuation:')
			print(leftGroup)
			print()
			print('Right Groups – Georgian:')
			print(rightGroupGeorgian)
			print()
			print('Left Groups – Georgian:')
			print(leftGroupGeorgian)
			print()
			print('Right Groups – Armenian:')
			print(rightGroupArmenian)
			print()
			print('Left Groups – Armenian:')
			print(leftGroupArmenian)

# Generate kern strings
def generateKernStrings():
	if font:
		global group
		global strings
		if group['left']['name'] and group['right']['name']:
			# Merge categories
			leftGroup = group['left']['uppercase'] + group['left']['lowercase'] + group['left']['figure'] + group['left']['punctuation'] + group['left']['other']
			rightGroup = group['right']['uppercase'] + group['right']['lowercase'] + group['right']['figure'] + group['right']['punctuation'] + group['right']['other'] + group['right']['sc']
			for elem in leftGroup:
				# All characters from Left Groups to kern with
				strings['left'] += elem
			for elem in rightGroup:
				# Two characters at the begin to compare with
				compare = 'HH'
				sc = ''
				scLeft = ''.join(group['left']['sc'])
				if elem[0].islower():
					compare = 'nn'
				elif elem[0].isnumeric():
					compare = '00'
				if elem[0].isupper():
					sc = scLeft
				stringsLine = compare + elem + strings['left'] + sc + '\n'
				if '.sc' in elem:
					stringsLine = '/h.sc/h.sc' + elem + scLeft + '\n'
				# String for kerning
				# elem is the main character needed kerning with all the following ones
				strings['text'] += stringsLine
			# Add Georgian characters to separated kern strings
			if group['left']['georgian'] and group['right']['georgian']:
				for elem in group['left']['georgian']:
					strings['leftGeorgian'] += elem
				for elem in group['right']['georgian']:
					compare = 'იი';
					stringsLine = compare + elem + strings['leftGeorgian'] + '\n'
					strings['text'] += stringsLine
			# Add Armenian characters to separated kern strings
			if group['left']['armenian'] and group['right']['armenian']:
				for elem in group['left']['armenian']:
					strings['leftArmenian'] += elem
				for elem in group['right']['armenian']:
					compare = 'ոո';
					stringsLine = compare + elem + strings['leftArmenian'] + '\n'
					strings['text'] += stringsLine
			# Remove empty string at the end
			strings['text'] = strings['text'][:-1]
			# Set category name the same as font family name
			strings['name'] = font.familyName
		else:
			Glyphs.clearLog()
			Glyphs.showMacroWindow()
			print('Please specify the left and right groups for the glyphs first')

# Add kern strings to the Sample Texts
def addKernStrings():
	global strings
	if strings['name'] and strings['text']:
		# Get Sample Texts
		sampleTexts = Glyphs.defaults["SampleTextsList"].mutableCopy()
		# Remove category with the same name (font family name)
		indexesToRemove = []
		for index, sampleTextEntry in enumerate(sampleTexts):
			if sampleTextEntry["name"] == strings['name']:
				indexesToRemove.append(index)
		for index in reversed(indexesToRemove):
			sampleTexts.removeObjectAtIndex_(index)
		# Save index of added category
		strings['category'] = len(sampleTexts)
		# Add new strings and save Sample Texts
		sampleTexts.append(dict(name=strings['name'], text=strings['text']))
		Glyphs.defaults["SampleTextsList"] = sampleTexts

# Open Sample Texts and select the first string from added category
def openKernStrings():
	global strings
	if strings['name'] and strings['text']:
		# Open the Edit view tab
		tab = font.currentTab
		if not tab:
			tab = font.newTab()
		# Show Group Members
		from GlyphsApp import GSCallbackHandler
		GSCallbackHandler.activateReporter_(GSCallbackHandler.reporterInstances()["ShowClassMembers"])
		# Set kerning-only mode
		tab.graphicView().setDoSpacing_(0)
		tab.graphicView().setDoKerning_(1)
		tab.updateKerningButton()
		# Select Text tool
		font.tool = 'GlyphsToolText'
		# Open Select Sample Text panel
		samples = NSClassFromString("GSSampleTextController").sharedManager()
		samples.showSampleTextDialog()
		samples.sampleTextCategoryController().setSelectionIndex_(strings['category'])
		# The following false call is required sometimes to make sure the string is copied to the Edit view tab
		samples.sampleTextEntryController().setSelectionIndex_(1)
		# Select the first string
		samples.sampleTextEntryController().setSelectionIndex_(0)
		# Set caret position between the first kern pair
		tab.textCursor = 3

getUniqueGroups()
printGroups()
generateKernStrings()
addKernStrings()
openKernStrings()
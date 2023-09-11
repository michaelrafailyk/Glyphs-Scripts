#MenuTitle: Generate Kern Strings
# -*- coding: utf-8 -*-
from __future__ import print_function
__doc__="""
Generate kern strings based on the Left and Right groups and add them into the Sample Texts.
"""
# Copyright: Michael Rafailyk, 2023, Version 1.1

group = {
	'left': {
		'name': [],
		'uppercase': [],
		'lowercase': [],
		'figure': [],
		'punctuation': [],
		'sc': [],
		'other': []
	},
	'right': {
		'name': [],
		'uppercase': [],
		'lowercase': [],
		'figure': [],
		'punctuation': [],
		'sc': [],
		'other': []
	}
}

strings = {
	'left': '',
	'right': '',
	'category': 0,
	'name': '',
	'text': ''
}

# Get the left and right unique groups and its characters
def getUniqueGroups():
	if Glyphs.font:
		for glyph in Glyphs.font.glyphs:
			if glyph.leftKerningGroup and glyph.leftKerningGroup not in group['left']['name']:
				getGlyphData(glyph, 'left')
			if glyph.rightKerningGroup and glyph.rightKerningGroup not in group['right']['name']:
				getGlyphData(glyph, 'right')
		# Sort elements inside the groups categories
		group['left']['uppercase'].sort()
		group['left']['lowercase'].sort()
		group['left']['figure'].sort()
		group['right']['uppercase'].sort()
		group['right']['lowercase'].sort()
		group['right']['figure'].sort()
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
	if Glyphs.font.glyphs[groupName] and Glyphs.font.glyphs[groupName].string:
		# Try to find a glyph with the same name as the name of this group
		glyph = Glyphs.font.glyphs[groupName]
		character = glyph.string
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
	if Glyphs.font:
		global group
		if group['left']['name'] and group['right']['name']:
			leftGroup = ''.join(group['left']['uppercase'] + group['left']['lowercase'] + group['left']['figure'] + group['left']['punctuation'] + group['left']['other'] + group['left']['sc'])
			rightGroup = ''.join(group['right']['uppercase'] + group['right']['lowercase'] + group['right']['figure'] + group['right']['punctuation'] + group['right']['other'] + group['right']['sc'])
			print('Right Groups:')
			print(rightGroup)
			print()
			print('Left Groups:')
			print(leftGroup)

# Generate kern strings
def generateKernStrings():
	if Glyphs.font:
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
				# All characters from Right Groups kern from
				strings['right'] += elem
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
			# Remove empty string at the end
			strings['text'] = strings['text'][:-2]
			# Set category name the same as font family name
			strings['name'] = Glyphs.font.familyName
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
		tab = Glyphs.font.currentTab
		if not tab:
			tab = Glyphs.font.newTab()
		# Show Group Members
		from GlyphsApp import GSCallbackHandler
		GSCallbackHandler.activateReporter_(GSCallbackHandler.reporterInstances()["com.glyphsapp.ShowClassMembers"])
		# Set kerning-only mode
		tab.graphicView().setDoSpacing_(0)
		tab.graphicView().setDoKerning_(1)
		tab.updateKerningButton()
		# Select Text tool
		Glyphs.font.tool = 'GlyphsToolText'
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
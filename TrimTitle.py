## Tested and working script

import os
import xml.etree.ElementTree as ET
import re
import shutil

# ############## ABOUT THIS FILE #####################
#
# A fixer for NFO metadata that removes unwanted text from the title field
# of episode NFOs using regex, in a nominated directory (including subdirs). The
# use case is for folders that display the filename verbatim (eg, mixed media
# in Jellyfin), where this is unhelpful in the GUI, but for some reason it
# is not desired to rename the underlying file. Substituting the title in the
# corresponding NFO (and directing the media server to update from NFOs) will
# alter the GUI display name without affecting the underlying file.
# A backup of the original NFO file is also created (filename.bak).
#
# The NFO files need to all be in a referenced directory (including subdirs).
# If you have NFOs you don't want touched, you will need to move them out of the tree.
#
# EXEMPLAR USE CASE
# I originally wanted to do this for a collection of home videos. The file
# names all start with yyyy Home Videos - but this is not optimal for looking
# at them in a list in a media server interface, I wanted a list of everything
# after that (eg, Bob's Wedding, Sue's Graduation, etc). I didn't want to rename
# the .mp4 files because they have existing NAS backups with versioning that
# I wanted to preserve, and I also didn't want to trigger re-upload to cloud
# backups. I just wanted to change the display title.
#
# .BAK BACKUP FILES
# Be aware that there is no provision at this stage for preserving existing .bak
# files. If there are existing .bak files, from an earlier run of this script
# or for some other reason, they will be overwritten. You will need to rename
# them or move them out to preserve them (or edit the function nfoTrim to give
# the new backups a different file extension).
#
# ###################################################

# ################ USER VARIABLES HERE ###############

# File root for your media, no trailing slash. Working examples with correct
# escaping for Windows: "c:\\python\\test", "\\\\192.168.1.30\\test\\Forensic Files"
showroot = ""

# Options below are strings or regex patterns. fileFilters are used to exclude.
# Use case example: For 2015 Home Videos - The Wedding (480p).nfo: The
# fileFilters 'Home Videos - ' and '( [0-9]+p)' could be used to
# exclude those fragments, to create the title '2015 The Wedding'.
# You can also use appendTerm to add a term on the end, eg, ' (Home Video)'
# These examples together would create a display title of 2015 The Wedding (Home Video).
fileFilter1 = ''
fileFilter2 = ''
fileFilter3 = ''
appendTerm = ''
# More convoluted edits (such as swapping parts around) would be possible with some
# edits to the function makeNFOTrimList. The variable newname becomes the new filename.

# ###################################################

nfoData = []

# Populate nfoData with filename, full path, and cleansed matching term(s).

def makeNFOTrimList(filepath, filetype):
   for root, dirs, files in os.walk(filepath):
      #traverse directories and get files
      for file in files:
         # if file is an nfo, add name and full path to list
         if file.lower().endswith(filetype.lower()):
            newname = str(file)
            if (newname == "season.nfo") or (newname == "tvshow.nfo"):
                continue
            newname = re.sub(fileFilter1, '', newname)
            newname = re.sub(fileFilter2, '', newname)
            newname = re.sub(fileFilter3, '', newname)
            newname = newname.replace('.nfo', '')
            newname = newname + appendTerm
            nfoData.append({"filename": file, "root": root, "path": os.path.join(root, file), "newname": newname})
   return

makeNFOTrimList(showroot, '.nfo')

# Execute file changes

def nfoTrim(db):
   for ea in db:
      #back up nfo
      original = str(ea['path'])
      target = str(ea['path']) + '.bak'
      shutil.copyfile(original, target)
      mytree = ET.parse(ea['path'])
      myroot = mytree.getroot()
      for tag in myroot.iter('title'):
         tag.text = ea['newname']
      for tag in myroot.iter('lockdata'):
         tag.text = 'true'
      mytree.write(ea['path'])

nfoTrim(nfoData)

import os
import sys
import xml.etree.ElementTree as ET
from fuzzywuzzy import fuzz
import re
import csv
import shutil
from datetime import datetime

# ############## ABOUT THIS SCRIPT #####################
#
# A fixer for NFO metadata where you have TV shows or other media with:
#
# - NFO files with incorrect or missing title/plot that you would like to repair
#   (The NFO plot field is displayed as "Overview" in the Jellyfin GUI).
# - A predictable (but not necessarily perfectly consistent) filenaming schema,
#   with NFO filenames that contain one consistently correct reference:
#   -- exact season/episode combination or absolute episode number, or
#   -- an episode name close enough for a fuzzy match
#   -- it doesn't matter if you have both, and they conflict; only one method is chosen.
# - a .csv data set with the right metadata with numbered column headers.
#
# The NFO files need to all be in a referenced directory (including subdirs).
# If you have NFOs you don't want touched, you will need to move them out of the tree.
#
# Other matching options are possible with some script edits; see
# section OTHER MATCHING OPTIONS at the end of this file.
#
# ABOUT YOUR SOURCE DATA
# Your CSV data source must have plot and title for fuzzy matching by title,
# or plot, title, season, and episode for matching by episode numbers. You
# can accommodate absolute episode numbers with no season by adding dummy season data
# and use the filtering options to trim it out from what is actually applied.
# Optionally, you can also have columns for year, runtime, IMDB id, and TVDB id to include
# these in the appropriate NFO fields (application of these edits is not fully tested).
#
# METHOD ONE: FUZZY MATCHING EPISODE TITLES
# For episode titles (fuzzy match), the user is asked to approve
# each match. If approved, NFO is updated (original saved as *.bak). If
# declined, the failed match is logged for user to do manual checking
# later.
#
# METHOD TWO: EPISODE NUMBER MATCHING
# Numerical episode/season matches are applied, normally without a confirm
# step (but see below for exception). Original saves as *.bak,
# and season.nfo and tvshow.nfo are excluded.
#
# .BAK BACKUP FILES
# Be aware that there is no provision at this stage for preserving existing .bak
# files. If there are existing .bak files, from an earlier run of this script
# or for some other reason, they will be overwritten. You will need to rename
# them or move them out to preserve them (or edit the function nfoEdits to give
# the new backups a different file extension).
#
# LOCKDATA FLAG
# In both cases, the NFO file is also set to <lockdata>true</lockdata> -
# in systems that respect this tag, such as Jellyfin, the alteration will not be
# overwritten by metadata refreshes.
#
# OPTIONAL FINAL MANUAL CHECK/EDITS
# There may be cases where you wish to manually edit the changes before they are
# applied - eg, you may have done some manual metadata edits adding extra
# information from other sources, or you may need to adjust for some
# non-standard media such as multiple episodes in a single file. In this
# case, you can set a flag to save the table with the intended edits as a
# .csv file and exit. You can open the .csv file in an editor such as
# excel and manually inspect the changes, and the filename, title, and plot/
# overview will also be included for cross-reference. You can make sensible
# edits to the csv (delete any entries for changes you want to discard).
# Then edit manualResume and resumeFile below to pull in your edits.
# (Note that no QA is done on your edits, they are at your own risk).
# The script will then proceed using your edited version of the update table.
#
# ORPHANED INCORRECT THUMBNAILS
# You may be left with pre-existing incorrect thumbnails in some cases
# (not due to any action of the script). See section FIXING INCORRECT THUMBNAILS
# at the end for ways to fix this.
#
# ###################################################

# ################ USER VARIABLES HERE ###############

# ## Initial Settings ###

# manualSave:   If this is set to 1, tells the script to proceed up to creating
#                 the update table, save the table for manual review, and exit.
#                 (Be sure to change back to 0 when resuming).
# manualResume: If this is set to 1, tells the script to skip creating the update
#                 table and pick up the update file from resumeFile below instead.
# infoDir:        Where you want information files to go (this is for lists of files
#                 that can't be matched, or full update table dumps for manual QA,
#                 as applicable). Include trailing \ (\\ when escaped).
# showroot:       File root for your show, no trailing \
# searchMethod:   Set to 1 to exclude (filter out) unwanted patterns
#                 or 2 to include (filter in) desired patterns. Generally if you are
#                 matching by episode name, you will want 1, and by episode number, 2.
#
# File refs with escaping for Windows: "c:\\test data", "\\\\192.168.1.30\\my show"

infoDir = ""
resumeFile = ""
manualSave = 0
manualResume = 0
showroot = ""
searchMethod = 1

# Options below are strings or regex patterns.
# fileFilters are EXCLUDED and are used with option 1 above.
# season/episodePatterns are INCLUDED and used with option 2.
#
# Use case example:
# Show s01e15 An Episode (480p).mp4 and matching .nfo.
# Episode name is correct:
# Use method 1, fileFilters 'Show s[0-9]+e[0-9]+ ' and ' (480p)'
# could be excluded, to create a search term 'An Episode'.
# Episode number is correct:
# Use method 2, seasonPattern '[Ss][0-9]+' and episodePattern
# '[Ee][0-9]+' are included to reach search terms 's01' and 'e15'.
#
# Any non-numeric characters are stripped from season and episode patterns
# by the script; you do not need to manually adjust for this.

fileFilter1 = ''
fileFilter2 = ''
fileFilter3 = ''
seasonPattern = '[Ss][0-9]+'
episodePattern = '[Ee][0-9]+'

# ## Variables About Your Comparison Data ###

# Your CSV data source must have plot and title for matching option 1 above,
# or plot, title, season, and episode for option 2. Other columns are optional
# for inclusion in the amended NFO. Mark absent columns as 'NA' (with quotes).
# Your csv file must have numerical column headings that match the numbers entered here.

dataFile = ""
seasonColumn = 0
episodeColumn = 1
titleColumn = 2
plotColumn = 3
yearColumn = 'NA'
runtimeColumn = 'NA'
imdbidColumn = 'NA'
tvdbidColumn = 'NA'

# ###################################################

nfoData = []
userData = []
matchList = []
declineList = []

# Populate nfoData with filename, full path, and cleansed matching term(s).

def makeNFOlist(filepath, filetype, method):
   id = 0
   for root, dirs, files in os.walk(filepath):
      #traverse directories and get files
      for file in files:
         # if file is an nfo, add name and full path to list
         if file.lower().endswith(filetype.lower()):
            if method == 1:
               # add cleansed version of filename for matching purposes
               searchTerm = str(file)
               searchTerm = re.sub(fileFilter1, '', searchTerm)
               searchTerm = re.sub(fileFilter2, '', searchTerm)
               searchTerm = re.sub(fileFilter3, '', searchTerm)
               searchTerm = searchTerm.replace('.nfo', '')
               nfoData.append({"id": id, "filename": file, "root": root, "path": os.path.join(root, file), "matchname": searchTerm})
               id += 1
            elif method == 2:
               searchTerm = []
               mySrch = str(file)
               mySrchSeas = re.search(seasonPattern, mySrch)
               if mySrchSeas is None:
                  mySrchSeas = "0"
               else:
                  mySrchSeas = re.sub('[^0-9]', '', mySrchSeas.group(0))
               searchTerm.append(mySrchSeas)
               mySrchEp = re.search(episodePattern, mySrch)
               if mySrchEp is None:
                  mySrchEp = "0"
               else:
                  mySrchEp = re.sub('[^0-9]', '', mySrchEp.group(0))
               searchTerm.append(mySrchEp)
               nfoData.append({"id": id, "filename": file, "root": root, "path": os.path.join(root, file), "matchname": searchTerm})
               id += 1
            else:
               return "Not a valid searchMethod, please check user variables and try again."
   return

if manualResume != 1: makeNFOlist(showroot, '.nfo', searchMethod)

# Populate userData with episode data from the user's dataset.

def makeEpisodeList(db):
   id = 0
   with open(db, newline='') as csvfile:
      reader = csv.DictReader(csvfile)
      for row in reader:
         entry = {}
         entry.update({'id': id})
         for ea in [{'season': seasonColumn}, {'episode': episodeColumn}, {'title': titleColumn}, {'plot': plotColumn}, {'year': yearColumn}, {'runtime': runtimeColumn}, {'imdbid': imdbidColumn}, {'tvdbid': tvdbidColumn}]:
            for key, value in ea.items():
               if value == 'NA':
                  pass
               else:
                  value = row[str(value)]
                  entry.update({key: value})
         userData.append(entry)
         id += 1
   return

if manualResume != 1: makeEpisodeList(dataFile)

# Populate matchList with matches, then append update fields from userData

def compareData(nfos, db, method):
   for file in nfos:
      entry = {'score': 0}
      entry.update({'nfoID': file['id']})
      entry.update({'filename': file['filename']})
      entry.update({'root': file['root']})
      entry.update({'path': file['path']})
      entry.update({'matchname': file['matchname']})
      if method == 1:
         for ep in db:
            myRatio = fuzz.ratio(file['matchname'], ep['title'])
            if myRatio > entry['score']:
               entry.update({'score': myRatio})
               entry.update({'matchtitle': ep['title']})
               entry.update({'matchID': ep['id']})
               entry.update(ep)
         matchList.append(entry)
      elif method == 2:
         for ep in db:
            if (file['matchname'][0] == ep['season']) and (file['matchname'][1] == ep['episode']):
               entry.update({'score': 100})
               entry.update({'matchtitle': ep['title']})
               entry.update({'matchID': ep['id']})
               entry.update(ep)
         matchList.append(entry)
      else:
         return("Invalid searchMethod, please check user variables and try again.")

if manualResume != 1: compareData(nfoData, userData, searchMethod)

# For searchMethod 1 (episode name fuzzy matching), present user
# each match to confirm

def userAccept(db):
   for ea in db:
      suggestedText1 = "SUGGESTED MATCH: " + ea['matchname'] + " AND " + ea['matchtitle']
      suggestedText2 = " (" + str(ea['score']) + "% CONFIDENCE)"
      print(suggestedText1 + suggestedText2)
      answer = input("y to accept, any other input to refuse")
      if answer.lower() == 'y':
         ea.update({'accept': 1})
      else:
         ea.update({'accept': 0})

if manualResume != 1:
   if searchMethod == 1:
      userAccept(matchList)

# Function to pull selected existing NFO data and add to matchList.
# Only used for manualSave cases since this will sometimes have manually
# added data the user might wish to retain. The data is not presently used
# for the update step or anything else by the script (but could possibly
# be the basis of further matching functionality using NFO content in future).

def getExtraData(db):
   for ea in db:
      mytree = ET.parse(ea['path'])
      myroot = mytree.getroot()
      if ea.get('matchID') is None:
         continue
      mydata = ea['matchID']
      #get data
      for item in ['season', 'episode', 'title', 'plot', 'year', 'runtime', 'imdbid', 'tvdbid']:
         try:
            for tag in myroot.iter(item):
               ea.update({str('nfo' + item): tag.text})
         except:
            ea.update({str('nfo' + item): 'null'})

# Create unmatched log and delete from matchList. Save record of Skipped and Matched.
# Check for manualSave flag. If 1, quit. (Use manualResume and saved file to continue).

def noMatchLog(db, method, qa):
   dellist = []
   if method == 1:
      for ea in db:
         if ea['accept'] == 0:
            declineList.append(ea['path'])
            dellist.append(ea)
   elif method == 2:
      for ea in db:
         if ea['score'] == 0:
            declineList.append(ea['path'])
            dellist.append(ea)
   for ea in dellist:
      matchList.remove(ea)
   now = datetime.now()
   destFile = infoDir + now.strftime("%Y-%m-%d %H-%M-%S") + "_Skipped.txt"
   f = open(destFile, "a")
   f.write(str(declineList))
   f.close()
   print("\n\nItems that could not be matched are logged at " + destFile + ".")
   # Save update table:
   now = datetime.now()
   destFile = infoDir + now.strftime("%Y-%m-%d %H-%M-%S") + "_Matched.csv"
   keys = matchList[0].keys()
   with open(destFile, 'w', encoding='utf8', newline='') as myFile:
      dict_writer = csv.DictWriter(myFile, keys)
      dict_writer.writeheader()
      dict_writer.writerows(matchList)
   print("Items that were matched are logged at " + destFile + ".\n")
   if qa == 1:
      print('Manual save flag found (usually set for QA), not proceeding to edits.')
      print('You will need to re-run with the flag removed to execute the changes.')
      print('Optionally you can also manualResume with manual edits, see script comments for details.')
      sys.exit()

if manualResume != 1:
   if manualSave == 1:
      getExtraData(matchList)
   noMatchLog(matchList, searchMethod, manualSave)

if manualResume == 1:
   #import resumeFile and replace matchList
   with open(resumeFile) as file:
      reader = csv.DictReader(file)
      matchList = list(reader)

# Execute file changes

def nfoEdits(db):
   for ea in db:
      #back up nfo
      original = str(ea['path'])
      target = str(ea['path']) + '.bak'
      shutil.copyfile(original, target)
      mytree = ET.parse(ea['path'])
      myroot = mytree.getroot()
#      mydata = src[ea['matchID']]
      #edits
      for item in ['season', 'episode', 'title', 'plot', 'year', 'runtime', 'imdbid', 'tvdbid']:
         try:
            for tag in myroot.iter(item):
               tag.text = ea[item]
         except:
            pass
      for tag in myroot.iter('lockdata'):
         tag.text = 'true'
      mytree.write(ea['path'])

if manualSave != 1: nfoEdits(matchList)

# APPENDIX 1: OTHER MATCHING OPTIONS IN THE NFO FILENAME
#
# This script is heavily commented and could probably be adapted to match with
# other cross-reference data such as episode dates or IMDB IDs, with only relatively
# basic scripting knowledge. You would do this by editing:
#
# - makeNFOlist: Function that pulls out NFO data to make a search term. Add an elif
#   clause for an extra search method and scrape the term into the variable searchTerm.
#   Follow the approach in method 1 if it's a single term (eg, IMDB ID) or in method 2
#   if it's constructed from concatenated data like year-month-date.
#
# - compareData: Function that compares data from makeNFOlist with .csv data source
#   to create final update table. Again, use method 1 or 2 as your starting exemplar,
#   as appropriate.
#
# You may also want to activate the on-screen approval steps used for fuzzy matches by
# editing the line after the function userAccept above:
#   if searchMethod == 1:
#       userAccept(matchList).
#
# APPENDIX 2: OTHER MATCHING OPTIONS IN THE NFO DATA
#
# This script as designed scrapes the comparison data from the NFO filename. It would be
# possible to modify the script to instead scrape from the actual NFO XML content. You would
# need to edit the function makeNFOlist. You might use some of the code in the function
# nfoEdits as a starting point for extracting what you need.
#
# APPENDIX 3: FIXING INCORRECT THUMBNAILS
#
# If your use case is mismatched episode names, you may be left with incorrect
# thumbnail images if they were sourced by a plug-in to match a previously,
# incorrectly-reported episode. This is not easily fixed by script because at least
# some systems don't respect <lockdata> for image references.
#
# One workaround is:
# 1. Move the repaired show folder out of the media server tree.
# 2. Use the GUI delete function to delete the show from the server db. THIS WILL
#    DELETE YOUR MEDIA UNLESS YOU MOVE IT FIRST.
# 3. Remove the thumbnail images from the media directory.
# 4. Move the repaired folder back into where your media server looks for media.
# 5. Let it be picked up as a new show from scratch, making sure it gets the metadata
#    for the episodes etc from your NFO. This will be determined in the metadata
#    settings for the library, but most systems will do this anyway if the
#    <lockdata> flag is in place - even if it tries to update the metadata, it will
#    run into the flag, and then fail over to what's already in the NFO. It is
#    advisable to back up your new NFOs if this is not a tested/known behaviour
#    in your system, though.
# How well this works will vary with your server platform.

# Deslea's NFO Tweaker Tools

A collection of Python tools to tweak the details shown in a media server interface, by tweaking NFO metadata, without editing underlying media files.

The scripts are heavily commented to allow for further customisation.

While further tools and a GUI are planned, I am a hobbyist and do not promise continuous active development. Forks are welcome.

**Dependencies**

The script is written in python and tested in v3.12.8. Imports are as follows: os, sys, xml.etree, fuzzywuzzy, re, csv, shutil, datetime

# The Tools

## FixFromDB.py:

A fixer for NFO metadata where you have TV shows or other media with:
* NFO files with incorrect or missing title/plot that you would like to repair
* A predictable (but not necessarily perfectly consistent) filenaming schema, with NFO filenames that contain one consistently correct reference:
  - exact season/episode combination or absolute episode number, or
  - an episode name close enough for a fuzzy match
  - it doesn't matter if you have both, and they conflict; only one method is chosen.
* a .csv data set with the right metadata with numbered column headers.

## TrimTitle.py:

A fixer for NFO metadata that removes unwanted text from the title field of episode NFOs using regex, in a nominated directory (including subdirs). The use case is for folders that display the filename verbatim (eg, mixed media in Jellyfin), where this is unhelpful in the GUI, but for some reason it is not desired to rename the underlying file. Substituting the title in the corresponding NFO (and directing the media server to update from NFOs) will alter the GUI display name without affecting the underlying file. A backup of the original NFO file is also created (filename.bak).

# Further Details

**.BAK BACKUP FILES _(Both Tools)_**

Be aware that there is no provision at this stage for preserving existing .bak files. If there are existing .bak files, from an earlier run of this script or for some other reason, they will be overwritten. You will need to rename them or move them out to preserve them (or edit the function nfoEdits to give the new backups a different file extension).

**LOCKDATA FLAG _(Both Tools)_**

The NFO file is set to \<lockdata\>true\</lockdata\> - in systems that respect this tag, such as Jellyfin, the alteration will not be overwritten by metadata refreshes.

**ABOUT YOUR SOURCE DATA _(FixFromDB)_**

Your CSV data source must have plot and title for fuzzy matching by title, or plot, title, season, and episode for matching by episode numbers. The column headers must be numbers, but the specific number doesn't matter, you map them in the options. You don't need to remove extraneous columns, anything not mapped is ignored.

You can accommodate absolute episode numbers with no season by adding dummy season data and use the filtering options to trim it out from what is actually applied. Optionally, you can also have columns for year, runtime, IMDB id, and TVDB id to include these in the appropriate NFO fields (application of these edits is not fully tested).

**FIX METHODS _(FixFromDB)_**

_**METHOD ONE: FUZZY MATCHING EPISODE TITLES**_
For episode titles (fuzzy match), the user is asked to approve each match. If approved, NFO is updated (original saved as *.bak). If declined, the failed match is logged for user to do manual checking later.

_**METHOD TWO: EPISODE NUMBER MATCHING**_
Numerical episode/season matches are applied, normally without a confirm step (but see below for exception). Original saves as *.bak, and season.nfo and tvshow.nfo are excluded.

**OPTIONAL FINAL MANUAL CHECK/EDITS _(FixFomDB)_**
There may be cases where you wish to manually edit the changes before they are applied - eg, you may have done some manual metadata edits adding extra information from other sources, or you may need to adjust for some non-standard media such as multiple episodes in a single file. In this case, you can set a flag to save the table with the intended edits as a .csv file and exit. You can open the .csv file in an editor such as excel and manually inspect the changes, and the filename, title, and plot/overview will also be included for cross-reference. You can make sensible edits to the csv (delete any entries for changes you want to discard). Then edit manualResume and resumeFile below to pull in your edits. (Note that no QA is done on your edits, they are at your own risk). The script will then proceed using your edited version of the update table.

# APPENDIX 1: OTHER MATCHING OPTIONS IN THE NFO FILENAME

This script is heavily commented and could probably be adapted to match with other cross-reference data such as episode dates or IMDB IDs, with only relatively basic scripting knowledge. You would do this by editing:

* makeNFOlist: Function that pulls out NFO data to make a search term. Add an elif clause for an extra search method and scrape the term into the variable searchTerm. Follow the approach in method 1 if it's a single term (eg, IMDB ID) or in method 2 if it's constructed from concatenated data like year-month-date.
* compareData: Function that compares data from makeNFOlist with .csv data source to create final update table. Again, use method 1 or 2 as your starting exemplar, as appropriate.
 
You may also want to activate the on-screen approval steps used for fuzzy matches by editing the call to the function userAccept.

# APPENDIX 2: OTHER MATCHING OPTIONS IN THE NFO DATA

This script as designed scrapes the comparison data from the NFO filename. It would be possible to modify the script to instead scrape from the actual NFO XML content. You would need to edit the function makeNFOlist. You might use some of the code in the function nfoEdits as a starting point for extracting what you need.

# APPENDIX 3: FIXING INCORRECT THUMBNAILS

If your use case is mismatched episode names, you may be left with incorrect thumbnail images if they were sourced by a plug-in to match a previously, incorrectly-reported episode. This is not easily fixed by script because at least some systems don't respect \<lockdata\> for image references.

One workaround is:
1. Move the repaired show folder out of the media server tree.
2. Use the GUI delete function to delete the show from the server db. THIS WILL DELETE YOUR MEDIA UNLESS YOU MOVE IT FIRST.
3. Remove the thumbnail images from the media directory.
4. Move the repaired folder back into where your media server looks for media.
5. Let it be picked up as a new show from scratch, making sure it gets the metadata for the episodes etc from your NFO. This will be determined in the metadata settings for the library, but most systems will do this anyway if the \<lockdata\> flag is in place - even if it tries to update the metadata, it will run into the flag, and then fail over to what's already in the NFO. It is advisable to back up your new NFOs if this is not a tested/known behaviour in your system, though.

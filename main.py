# DESLEA'S NFO TWEAKER TOOLS
# A collection of tools to tweak the details shown in a media server
# interface, by tweaking NFO metadata, without editing underlying media
# files.
#
# DEPENDENCIES
# The script is written in python and tested in v3.12.8.
# Imports are as follows:
# os, sys, xml.etree, fuzzywuzzy, re, csv, shutil, datetime
#
# TOOLS:
#
# FixFromDB.py:
# A fixer for NFO metadata where you have TV shows or other media with:
#
# - NFO files with incorrect or missing title/plot that you would like to repair
# - A predictable (but not necessarily perfectly consistent) filenaming schema,
#   with NFO filenames that contain one consistently correct reference:
#   -- exact season/episode combination or absolute episode number, or
#   -- an episode name close enough for a fuzzy match
#   -- it doesn't matter if you have both, and they conflict; only one method is chosen.
# - a .csv data set with the right metadata with numbered column headers.
#
# TrimTitle.py:
# A fixer for NFO metadata that removes unwanted text from the title field
# of episode NFOs using regex, in a nominated directory (including subdirs). The
# use case is for folders that display the filename verbatim (eg, mixed media
# in Jellyfin), where this is unhelpful in the GUI, but for some reason it
# is not desired to rename the underlying file. Substituting the title in the
# corresponding NFO (and directing the media server to update from NFOs) will
# alter the GUI display name without affecting the underlying file.
# A backup of the original NFO file is also created (filename.bak).
#
# The scripts are heavily commented to allow for further customisation.

def main():
    print("\nMain function not currently used. Reserved for future GUI.")
    print("Refer to script comments for usage guidance and execute the desired script direct.")
    print("You will need to manually edit some parameters before the scripts will work.")

if __name__ == '__main__':
    main()
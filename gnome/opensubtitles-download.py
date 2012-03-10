#!/usr/bin/python
# -*- coding: utf-8 -*-

# OpenSubtitles download / Gnome edition
# Version 1.1
#
# Automatically find and download subtitles for your favorite videos!

# Emeric Grange <emeric.grange@gmail.com>
# Carlos Acedo <carlos@linux-labs.net> for the original script

# Copyright (c) 2011 by Emeric GRANGE <emeric.grange@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import struct
import subprocess
import mimetypes
from sys import argv
from xmlrpclib import ServerProxy, Error

# ==== Language selection ======================================================
# You can change the search language here by using either 2-letter (ISO 639-1) 
# or 3-letter (ISO 639-2) language codes.
# Supported ISO codes: http://www.opensubtitles.org/addons/export_languages.php

SubLanguageID = ['eng']
languages = {'alb': 'Albanian',  'ara': 'Arabic',  'arm': 'Armenian', 'may': 'Malay',  'bos': 'Bosnian',  'pob': 'Brazilian',  'bul': 'Bulgarian',  'cat': 'Catalan',  'eus': 'Basque',  'chi': 'Chinese',  'hrv': 'Croatian',  'cze': 'Czech',  'dan': 'Danish',  'dut': 'Dutch',  'eng': 'English', 'bre': 'British English', 'epo': 'Esperanto',  'est': 'Estonian',  'fin': 'Finnish',  'fre': 'French',  'geo': 'Georgian',  'ger': 'German',  'ell': 'Greek',  'heb': 'Hebrew',  'hun': 'Hungarian',  'ind': 'Indonesian',  'ita': 'Italian',  'jpn': 'Japanese',  'kaz': 'Kazakh',  'kor': 'Korean',  'lav': 'Latvian',  'lit': 'Lithuanian',  'ltz': 'Luxembourgish',  'mac': 'Macedonian',  'nor': 'Norwegian',  'per': 'Persian',  'pol': 'Polish',  'por': 'Portuguese',  'rum': 'Romanian',  'rus': 'Russian',  'scc': 'Serbian',  'slo': 'Slovak',  'slv': 'Slovenian',  'spa': 'Spanish',  'swe': 'Swedish ',  'tha': 'Thai',  'tur': 'Turkish',  'ukr': 'Ukrainian',  'vie': 'Vietnamese', 'sq': 'Albanian',  'ar': 'Arabic',  'hy': 'Armenian', 'ms': 'Malay',  'bs': 'Bosnian',  'pb': 'Brazilian',  'bg': 'Bulgarian',  'ca': 'Catalan',  'eu': 'Basque',  'zh': 'Chinese',  'hrv': 'Croatian',  'cs': 'Czech',  'da': 'Danish',  'nl': 'Dutch',  'en': 'English', 'eo':	'Esperanto', 'et': 'Estonian',  'fi': 'Finnish',  'fr': 'French',  'ka': 'Georgian',  'de': 'German',  'el': 'Greek',  'he': 'Hebrew',  'hu': 'Hungarian',  'id': 'Indonesian',  'it': 'Italian',  'ja': 'Japanese', 'kk': 'Kazakh', 'ko': 'Korean', 'mk': 'Macedonian',  'lv': 'Latvian',  'lt': 'Lithuanian',  'lb': 'Luxembourgish',  'no': 'Norwegian',  'fa': 'Persian',  'pl': 'Polish',  'pt': 'Portuguese',  'ro': 'Romanian',  'ru': 'Russian',  'sr': 'Serbian',  'sk': 'Slovak',  'sl': 'Slovenian',  'es': 'Spanish',  'sv': 'Swedish ',  'th': 'Thai',  'tr': 'Turkish',  'uk': 'Ukrainian',  'vi': 'Vietnamese'}

# ==== Server selection ========================================================
# XML-RPC server domain for opensubtitles.org:
server = ServerProxy('http://api.opensubtitles.org/xml-rpc')

# ==== Check file path & file ==================================================
def checkFile(path):
    """Check mimetype and/or file extension to detect valid video file"""
    if os.path.isfile(path) == False:
        #subprocess.call(['zenity', '--error', '--text=This is not a file:\n- ' + path])
        return False
    
    fileMimeType, encoding = mimetypes.guess_type(path)
    if fileMimeType == None:
        fileExtension = path.rsplit('.', 1)
        if fileExtension[1] not in ['3g2', '3gp', '3gp2', '3gpp', 'ajp', \
        'asf', 'asx', 'avchd', 'avi', 'bik', 'bix', 'box', 'cam', 'dat', \
        'divx', 'dmf', 'dv', 'dvr-ms', 'evo', 'flc', 'fli', 'flic', 'flv', \
        'flx', 'gvi', 'gvp', 'h264', 'm1v', 'm2p', 'm2ts', 'm2v', 'm4e', \
        'm4v', 'mjp', 'mjpeg', 'mjpg', 'mkv', 'moov', 'mov', 'movhd', 'movie', \
        'movx', 'mp4', 'mpe', 'mpeg', 'mpg', 'mpv', 'mpv2', 'mxf', 'nsv', \
        'nut', 'ogg', 'ogm', 'ogv', 'omf', 'ps', 'qt', 'ram', 'rm', 'rmvb', \
        'swf', 'ts', 'vfw', 'vid', 'video', 'viv', 'vivo', 'vob', 'vro', \
        'webm', 'wm', 'wmv', 'wmx', 'wrap', 'wvx', 'wx', 'x264', 'xvid']:
            #subprocess.call(['zenity', '--error', '--text=This file is not a video (unknown mimetype AND invalid file extension):\n- ' + path])
            return False
    else:
        fileMimeType = fileMimeType.split('/', 1)
        if fileMimeType[0] != 'video':
            #subprocess.call(['zenity', '--error', '--text=This file is not a video (unknown mimetype):\n- ' + path])
            return False
    
    return True

# ==== Hashing algorithm =======================================================
# Infos: http://trac.opensubtitles.org/projects/opensubtitles/wiki/HashSourceCodes
# This particular implementation is coming from SubDownloader: http://subdownloader.net/
def hashFile(path):
    """Produce a hash for a video file: size + 64bit chksum of the first and 
    last 64k (even if they overlap because the file is smaller than 128k)"""
    try:
        longlongformat = 'Q' # unsigned long long little endian
        bytesize = struct.calcsize(longlongformat)
        format = "<%d%s" % (65536//bytesize, longlongformat)
        
        f = open(path, "rb")
        
        filesize = os.fstat(f.fileno()).st_size
        hash = filesize
        
        if filesize < 65536 * 2:
            subprocess.call(['zenity', '--error', '--text=File size error while generating hash for this file :\n- ' + path])
            return "SizeError"
        
        buffer = f.read(65536)
        longlongs = struct.unpack(format, buffer)
        hash += sum(longlongs)
        
        f.seek(-65536, os.SEEK_END) # size is always > 131072
        buffer = f.read(65536)
        longlongs = struct.unpack(format, buffer)
        hash += sum(longlongs)
        hash &= 0xFFFFFFFFFFFFFFFF
        
        f.close()
        returnedhash = "%016x" % hash
        return returnedhash
    
    except IOError:
        subprocess.call(['zenity', '--error', '--text=Input/Output error while generating hash for this file :\n- ' + path])
        return "IOError"

# ==== Get file(s) path(s) =====================================================
# Get opensubtitles-download script path, then remove it from argv list
execPath = argv[0]
argv.pop(0)
moviePath = ''

if len(argv) == 0:
    #subprocess.call(['zenity', '--error', '--text=No file selected.'])
    exit(1)
elif argv[0] == '--file':
    moviePath = argv[1]
else:
    filePathList = []
    moviePathList = []
    
    try:
        # Fill filePathList (using nautilus script)
        filePathList = os.environ['NAUTILUS_SCRIPT_SELECTED_FILE_PATHS'].splitlines()
    except Exception:
        # Fill filePathList (using program arguments)
        for i in range(len(argv)):
            filePathList.append(os.path.abspath(argv[i]))
    
    # Check file(s) type
    for i in range(len(filePathList)):
        if checkFile(filePathList[i]):
            moviePathList.append(filePathList[i])
    
    # If moviePathList is empty, abort
    if len(moviePathList) == 0:
        exit(1)
    
    # The first file will be processed immediatly
    moviePath = moviePathList[0]
    moviePathList.pop(0)
    
    # The remaining file(s) are dispatched to new instance(s) of this script
    for i in range(len(moviePathList)):
        process_movieDispatched = subprocess.Popen([execPath, '--file', moviePathList[i]])

# ==== Main program ============================================================
try:
    try:
        # Connection to opensubtitles.org server
        session = server.LogIn('', '', 'en', 'opensubtitles-download 1.1')
        if session['status'] != '200 OK':
            subprocess.call(['zenity', '--error', '--text=Unable to reach opensubtitles.org server: ' + session['status'] + '. Please check:\n- Your internet connection status\n- www.opensubtitles.org availability'])
            exit(1)
        token = session['token']
    except Exception:
        subprocess.call(['zenity', '--error', '--text=Unable to reach opensubtitles.org server. Please check:\n- Your internet connection status\n- www.opensubtitles.org availability'])
        exit(1)
    

    movieHash = hashFile(moviePath)
    movieSize = os.path.getsize(moviePath)
    
    # Search for available subtitles (using file hash and size)
    subNotFound = []
    subFound = []
    for lang in SubLanguageID:
        searchList = []
        searchList.append({'sublanguageid':lang, 'moviehash':movieHash, 'moviebytesize':str(movieSize)}) # Search movie by file hash
       
        # Search for available subtitles (using file name)
        #searchList.append({'sublanguageid':lang, 'query':moviePath}) # Search movie by file name
       
        # Launch the search
        subtitlesList = server.SearchSubtitles(token, searchList)    
        if subtitlesList['data']:
            # Sanitize title strings to avoid parsing errors
            for item in subtitlesList['data']:
                item['MovieName'] = item['MovieName'].replace('"', '\\"')
                item['MovieName'] = item['MovieName'].replace("'", "\'")
           
            # If there are more than one subtitles, let the user decide which  will be downloaded
            if len(subtitlesList['data']) != 1:
                subtitleItems = ''
                for item in subtitlesList['data']:
                    # Give the user some additional information about the subtitles
                    hearingImpaired = ''
                    if item['SubHearingImpaired'] == '1':
                        hearingImpaired += '✓'
                    else: 
                        hearingImpaired += '\'\''
                    CD = ''
                    if int(item['SubSumCD']) > 1:
                        CD += str(item['SubActualCD']) + '/' + str(item['SubSumCD'])
                    else:
                        CD += '\'\''
                    subtitleItems += '"' + item['SubFileName'] + '" ' + item['LanguageName'] + ' ' + hearingImpaired + ' ' + CD + ' '
                process_subtitleSelection = subprocess.Popen('zenity --width=1024 --height=480 --list --title="' + os.path.basename(moviePath) + '" --column="Available subtitles" --column="Language" --column="Hearing impaired" --column="CD" '  + subtitleItems, shell=True, stdout=subprocess.PIPE)
                subtitleSelected = str(process_subtitleSelection.communicate()[0]).strip('\n')
                resp = process_subtitleSelection.returncode
            else:
                subtitleSelected = ''
                resp = 0
           
            if resp == 0:
                # Select subtitle file to download
                index = 0
                subIndex = 0
                for item in subtitlesList['data']:
                    if item['SubFileName'] == subtitleSelected:
                        subIndex = index
                    else:
                        index += 1
               
                subFound.append(subtitlesList['data'][subIndex]['SubLanguageID'])
                subDirName = os.path.dirname(moviePath)
                subURL = subtitlesList['data'][subIndex]['SubDownloadLink']
                subFileName = os.path.basename(moviePath)[:-4] + '_' + subFound[-1] + subtitlesList['data'][subIndex]['SubFileName'][-4:]
                subFileName = subFileName.replace('"', '\\"')
                subFileName = subFileName.replace("'", "\'")

                # Download and unzip selected subtitle (with progressbar)
                process_subDownload = subprocess.call('(wget -O - ' + subURL + ' | gunzip > "' + subDirName + '/' + subFileName + '") 2>&1 | zenity --progress --auto-close --pulsate --title="Downloading subtitle, please wait..." --text="Downloading subtitle for \'' + subtitlesList['data'][0]['MovieName'] + '\' : "', shell=True)

                # If an error occur, say so
                if process_subDownload != 0:
                    subprocess.call(['zenity', '--error', '--text=An error occurred while downloading or writing the selected subtitle.'])
        else:
            langLookedFor = re.split(r"\s*,\s*", lang)
            # Behave nicely if user is searching for multiple languages at once
            for l in langLookedFor:
                subNotFound.append(l)

    # Print a message if some/all subtitles not found
    if subNotFound:
        # Only list languages if more languages are downloaded
        langNotFound = ''
        langFound = ''
        if len(SubLanguageID) > 1 or len(langLookedFor) > 1:
            langNotFound = ' in:\n'
            for lang in subNotFound:
                langNotFound += languages[lang] + '\n'
            if subFound:
                langFound = '\n\nHowever, following subtitles were downloaded:\n'
                for lang in subFound:
                    langFound += languages[lang] + '\n' 
        movieFileName = moviePath.rsplit('/', -1)
        subprocess.call(['zenity', '--info', '--title=No subtitles found', '--text=No subtitles found' + langNotFound + 'for this video:\n' + movieFileName[-1] + langFound])
    
    # Disconnect from opensubtitles.org server, then exit
    server.LogOut(token)
    exit(0)
except Error:
    # If an unknown error occur, say so (and apologize)
    subprocess.call(['zenity', '--error', '--text=An unknown error occurred, sorry about that... Please check:\n- Your internet connection status\n- www.opensubtitles.org availability'])
    exit(1)

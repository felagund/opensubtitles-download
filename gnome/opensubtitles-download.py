#!/usr/bin/python
# -*- coding: utf-8 -*-

#umej mergnout titulky stahnute z titulky com
#postarej se o nove imdb pole

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

import shutil
import os
import sys
import tempfile
import signal
import re
import struct
import subprocess
import mimetypes
import imdb
import chardet
import itertools
import collections
from sys import argv
from xmlrpclib import ServerProxy, Error

# ==== Language selection ======================================================
# You can change the search language here by using either 2-letter (ISO 639-1) 
# or 3-letter (ISO 639-2) language codes.
# Supported ISO codes: http://www.opensubtitles.org/addons/export_languages.php

SubLanguageID = ['eng','cze'] # FIXME if the order is reversed, cze never gets downloaded because searchBy gets to None


# ==== File moving ============================================================
# Specify directory where the resulting matroska file should be moved. 
# Do not forget the trailing slash'
# Turn this of by uncommenting the following line a commenting the next line:

#pathToMoveResultingFileTo = ''
pathToMoveResultingFileTo = '/home/drew/Desktop/Filmy/'

languages = {'alb': 'Albanian',  'ara': 'Arabic',  'arm': 'Armenian', 'may': 'Malay',  'bos': 'Bosnian',  'pob': 'Brazilian',  'bul': 'Bulgarian',  'cat': 'Catalan',  'eus': 'Basque',  'chi': 'Chinese',  'hrv': 'Croatian',  'cze': 'Czech',  'dan': 'Danish',  'dut': 'Dutch',  'eng': 'English', 'bre': 'British English', 'epo': 'Esperanto',  'est': 'Estonian',  'fin': 'Finnish',  'fre': 'French',  'geo': 'Georgian',  'ger': 'German',  'ell': 'Greek',  'heb': 'Hebrew',  'hun': 'Hungarian',  'ind': 'Indonesian',  'ita': 'Italian',  'jpn': 'Japanese',  'kaz': 'Kazakh',  'kor': 'Korean',  'lav': 'Latvian',  'lit': 'Lithuanian',  'ltz': 'Luxembourgish',  'mac': 'Macedonian',  'nor': 'Norwegian',  'per': 'Persian',  'pol': 'Polish',  'por': 'Portuguese',  'rum': 'Romanian',  'rus': 'Russian',  'scc': 'Serbian',  'slo': 'Slovak',  'slv': 'Slovenian',  'spa': 'Spanish',  'swe': 'Swedish',  'tha': 'Thai',  'tur': 'Turkish',  'ukr': 'Ukrainian',  'vie': 'Vietnamese', 'sq': 'Albanian',  'ar': 'Arabic',  'hy': 'Armenian', 'ms': 'Malay',  'bs': 'Bosnian',  'pb': 'Brazilian',  'bg': 'Bulgarian',  'ca': 'Catalan',  'eu': 'Basque',  'zh': 'Chinese',  'hrv': 'Croatian',  'cs': 'Czech',  'da': 'Danish',  'nl': 'Dutch',  'en': 'English', 'eo':	'Esperanto', 'et': 'Estonian',  'fi': 'Finnish',  'fr': 'French',  'ka': 'Georgian',  'de': 'German',  'el': 'Greek',  'he': 'Hebrew',  'hu': 'Hungarian',  'id': 'Indonesian',  'it': 'Italian',  'ja': 'Japanese', 'kk': 'Kazakh', 'ko': 'Korean', 'mk': 'Macedonian',  'lv': 'Latvian',  'lt': 'Lithuanian',  'lb': 'Luxembourgish',  'no': 'Norwegian',  'fa': 'Persian',  'pl': 'Polish',  'pt': 'Portuguese',  'ro': 'Romanian',  'ru': 'Russian',  'sr': 'Serbian',  'sk': 'Slovak',  'sl': 'Slovenian',  'es': 'Spanish',  'sv': 'Swedish',  'th': 'Thai',  'tr': 'Turkish',  'uk': 'Ukrainian',  'vi': 'Vietnamese'}

# ==== Server selection ========================================================
# XML-RPC server domain for opensubtitles.org:
server = ServerProxy('http://api.opensubtitles.org/xml-rpc')

# ==== Put articles where I want it ============================================
def handleArticles(title):
    """ Accepts string as an output, if it starts with the/a/an (case-insensitive), it moves the article to the end. So 'The Title' becomes Title, The"""
    if title.lower()[:4] == 'the ':
        title =  title[4].upper() + title[5:] + ', ' + title[:3]
    if title.lower()[:3] == 'an ':
        title =  title[3].upper() + title[4:] + ', ' + title[:2]
    if title.lower()[:2] == 'a ':
        title =  title[2].upper() + title[3:] + ', ' + title[:1]
    return title

# ==== Display and edit subtitles if something is wrong =======================
def editSubtitles(subsToEdit,zenityTitle):
        tmp = tempfile.TemporaryFile()
        tmp.write(''.join(subsToEdit))
        tmp.seek(0)
        editedSubsString = ''
        editedSubsString = subprocess.Popen(['zenity', '--width=480', '--height=720', '--text-info', '--editable', '--title="' + zenityTitle + '"'],stdin=tmp, stdout=subprocess.PIPE).communicate()[0]
        tmp.close()
        if editedSubsString:
            return [i+ '\n' for i in editedSubsString.split("\n")]
        else: # If user cancels zenity dialog
            return subsToEdit

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
# ==== Repair subtitles =======================================================
# Do various editing to subtitles
def editSubs(subLanguageEdit,subPathEdit,subFormatEdit,moviePathEdit,subPathsEdit):
    # Convert subtitles to unicode
    if subLanguageEdit == 'cze':
        encConv = ' | enconv -L czech -x utf8'
    else:
        encConv = ''
    # And get rid of bad line ends
    subprocess.call('cat "' + subPathEdit + '"'+ encConv + ' | dos2unix | mac2unix  > temp.temp~ ; cp temp.temp~ "' + subPathEdit + '" ;rm temp.temp~', shell=True)

    # Convert English subtitles to unicode (only if the use some special character, otherwise stay ascii which we do not mind)
    if subLanguageEdit == 'eng':
        f = open(subPathEdit,"r").read()
        enc = chardet.detect(f)['encoding']
        tmp = f.decode(enc)
        f = open(subPathEdit, 'w')
        f.write(tmp.encode('utf-8'))
        f.close()
        #subprocess.call('iconv --from-code=' + enc + ' --to=utf-8 "'+ subPathEdit + '" > "' + subPathEdit + 'a"',shell=True) 

    #| sed -e :a -e \'$d;N;2,3ba\' -e \'P;D\'
    # Handle non srt formats
    if subFormatEdit == 'srt':
        pass
    elif subFormatEdit == 'sub':
        # repair {123}{456} blabla {78}{90} blabla\n
        f = open(subPathEdit,"r") 
        allSubs = f.readlines()
        for sub in allSubs[:]:
            splitSub = sub.rsplit('{')
            if len(splitSub) > 4:
                allSubs.insert(allSubs.index(sub),'{'.join(splitSub[:-2]) + '\n')
                allSubs.insert(allSubs.index(sub),'{' + '{'.join(splitSub[-2:]))
                allSubs.remove(sub)
        f = open(subPathEdit,"w")
        f.write(''.join(allSubs))
        f.close()
        # Get fps
        mplayerOutput = subprocess.Popen(("mplayer", "-identify", "-frames", "0", "o-ao", "null", moviePathEdit), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
        pattern = re.compile(r'(\d{2}.\d{3}) fps')
        fps = pattern.search(mplayerOutput).groups()[0]
        subprocess.call(['subconv','-f', fps, subPathEdit, subPathEdit[:-3] + 'srt'])
        subPathEdit = subPathEdit[:-3] + 'srt'
        subPathsEdit[lang]=[subPathEdit,lang]
    else:
        subprocess.call(['zenity', '--error', '--text=Subtitle in format ' + subFormatEdit + '. Expect trouble.'])

    # Edit subtitles
    f = open(subPathEdit,"r")
    allSubs =  f.readlines()

    # Check whether we don't have bad subtitles without timecodes
    delta = 0                
    for i in [i for i in allSubs]:
        if i[:-1].isdigit():
            i = allSubs.index(i)
            if not '-->' in allSubs[i+1]:
                if not '-->' in allSubs[i-1]:
                    i -= delta
                    editedSubsList = editSubtitles(allSubs[i-6:i+7],'Something wrong with the subtitles, please inspect')
                    allSubs = allSubs[:i-6] + editedSubsList + allSubs[i+7:]
                    delta += 13 - len(editedSubsList)

    # Delete some automatically inserted subtitles
    deleteLines = ['Najlepsi zazitok z pozerania - Open Subtitles MKV Player\n','[ENGLISH]\n','Best watched using Open Subtitles MKV Player\n','FDb.cz - navstivte svet filmu\n','Subtitles downloaded from www.OpenSubtitles.org\n','Download Movie Subtitles Searcher from www.OpenSubtitles.org\n','www.titulky.com\n','WWW:TITULKY.COM\n','SDI Media Group\n','De Aldisio, Agence Press.\n','Video SubtitIes By\n','www.OpenSubtitles.org\n','www.OpenSubtitles.org\n']
    deleteLinesDouble = ['SDI Media Group\n','Video Subtitles By\n'] # This is a two line junk subtitle
    deleteLinesIndexes = [allSubs.index(i) for i in allSubs if i in deleteLines]
    delta = 0
    for index in deleteLinesIndexes:
        index -= delta
        if allSubs[index] in deleteLinesDouble:
            oneOrTwo = 1
        else:
            oneOrTwo = 0
        allSubs = allSubs[0 : index-2-oneOrTwo] + allSubs[index+2:]
        delta +=4+oneOrTwo

    # Remove blank lines in the end and in the beginning
    while allSubs[0] == '\n':
        allSubs = allSubs[1:]
    while allSubs[-1] == ['\n']:
        allSubs = allSubs[:-1]

    # Edit beginning and end for signatures and so on
    startEndOfSubs = allSubs[:15] + ['=================<88>=================\n'] + allSubs[-12:]
    editedSubsList = editSubtitles(startEndOfSubs,'Delete cruft from beginning and end')                    
    cutIndex = editedSubsList.index('=================<88>=================\n')
    allSubs = editedSubsList[:cutIndex] + allSubs[15:-12] + editedSubsList[cutIndex+1:]
    f = open(subPathEdit, "w")
    f.write(''.join(allSubs))
    f.close()
    return (subPathEdit,subPathsEdit)

# ==== Download subtitles ======================================================
# Download subtitles
def download_subtitles(token,searchByDown,moviePathDown,movieNameDown,badSubtitlesDown,subNotFoundDown,subPathsDown):
    # Search for available subtitles (using file hash and size)

    imdbIDDown = ''
    movieYearDown = ''
    movieHash = hashFile(moviePathDown)
    movieSize = os.path.getsize(moviePathDown)

    for lang in subNotFoundDown[:]:
        subNotFoundDown = [] # assume we have found all subtitles
        searchList = []
        # Search movie by file hash
        if searchBy[lang] == 'Hash': 
            searchList.append({'sublanguageid':lang, 'moviehash':movieHash, 'moviebytesize':str(movieSize)})
        # Search for available subtitles (using file name)
        elif searchBy[lang] == 'Name':
            searchList.append({'sublanguageid':lang, 'query':movieNameDown}) # Search movie by file name
        # Launch the search
        subtitlesList = server.SearchSubtitles(token, searchList)    
        if subtitlesList['data']:

            # Sanitize title strings to avoid parsing errors
            for item in subtitlesList['data']:
                item['MovieName'] = item['MovieName'].replace('"', '\\"')
                item['MovieName'] = item['MovieName'].replace("'", "\'")
           
            # If there are more than one subtitles, let the user decide which  will be downloaded
                (imdbIDGroupDown,movieNameGroupDown,movieYearGroupDown) = [],[],[]
            for item in subtitlesList['data']:
                imdbIDGroupDown.append(item['IDMovieImdb'])
                movieNameGroupDown.append(item['MovieName'])
                movieYearGroupDown.append(item['MovieYear'])
            imdbIDDown = collections.Counter(imdbIDGroupDown).most_common()[0][0]
            movieNameDown = collections.Counter(movieNameGroupDown).most_common()[0][0]
            movieYearDown = collections.Counter(movieYearGroupDown).most_common()[0][0]
            if len(subtitlesList['data']) != 1:
                subtitleItems = ''
                for item in subtitlesList['data']:
                    if not item['IDSubtitleFile'] in badSubtitlesDown:
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
                        subtitleItems += '"' + item['SubFileName'] + '" ' + item['LanguageName'] + ' ' + hearingImpaired + ' ' + CD + ' ' + item['SubFormat']  + ' ' + item['IDMovieImdb'] + ' ' +item['SubDownloadsCnt'] + ' '

                process_subtitleSelection = subprocess.Popen('zenity --width=1280 --height=480 --list --title="' + os.path.basename(moviePathDown) + '" --column="Available subtitles" --column="Language" --column="Hearing impaired" --column="CD" --column="Format" --column="IMDb ID" --column="Download count" '  + subtitleItems, shell=True, stdout=subprocess.PIPE)
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
               
                badSubtitlesDown.append(subtitlesList['data'][subIndex]['IDSubtitleFile']) # assume the subtitles are bad
                # zpatky bad subtitles. sub found, goodsubs, subdirname? subtitlelistnonempty? subpaths,languages searched, subnotfound
                subURL = subtitlesList['data'][subIndex]['SubDownloadLink']
                subFileName = os.path.basename(moviePathDown[:-4] + '_' +  subtitlesList['data'][subIndex]['SubLanguageID'] + subtitlesList['data'][subIndex]['SubFileName'][-4:])
                subFileName = subFileName.replace('"', '\\"')
                subFileName = subFileName.replace("'", "\'")
                subPath=os.path.dirname(moviePathDown) + '/' + subFileName
                subPathsDown[lang]=[subPath,lang]

                # Download and unzip selected subtitles (with progressbar)
                process_subDownload = subprocess.call('(wget -O - ' + subURL + ' | gunzip  > "' + subPath + '") 2>&1 | zenity --progress --auto-close --pulsate --title="Downloading subtitle, please wait..." --text="Downloading subtitle for \'' + subtitlesList['data'][0]['MovieName'] + '\' : "', shell=True)
                
                # Edit subtitles
                subPathDown,subPathsDown = editSubs(subtitlesList['data'][subIndex]['SubLanguageID'],subPath,subtitlesList['data'][subIndex]['SubFormat'],moviePathDown,subPathsDown)

                # If an error occur, say so
                if process_subDownload != 0:
                    subprocess.call(['zenity', '--error', '--text=An error occurred while downloading or writing the selected subtitle.'])
        else:
            if searchBy[lang] == 'Hash':
                searchBy[lang] = 'Name'
            else:
                searchBy[lang] = None
            subNotFoundDown.append(lang)

            # Behave nicely if user is searching for multiple languages at once
            #langLookedFor = re.split(r"\s*,\s*", lang)
            #for l in langLookedFor:
            # FIXME what happens when none subtitle fits?
    return badSubtitlesDown,subPathsDown,subNotFoundDown,imdbIDDown,movieNameDown,movieYearDown

# ==== Dismantle list in lists =================================================
# [a,b,[a,b,[a,b]]] na [a,b,a,b,a,b]
def get_lang(list):
    a = []
    for i in list:
        if not isinstance(i, list):
            a.append(i)
        else:
            get_lang(i)
    return a


# ==== Get file(s) path(s) =====================================================
# Get opensubtitles-download script path, then remove it from argv list
execPath = argv[0]
argv.pop(0)
moviePath = ''

if len(argv) == 0:
    #subprocess.call(['zenity', '--error', '--text=No file selected.'])
    sys.exit(1)
elif argv[0] == '--file':
    moviePath = os.path.abspath(argv[1])
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
        sys.exit(1)
    
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
            sys.exit(1)
        token = session['token']
    except Exception:
        subprocess.call(['zenity', '--error', '--text=Unable to reach opensubtitles.org server. Please check:\n- Your internet connection status\n- www.opensubtitles.org availability'])
        sys.exit(1)
    searchBy = {}
    for lang in SubLanguageID:
        searchBy[lang] = 'Hash'  
    badSubtitles = []
    badTiming = ''
    badNumber = 2
    
    movieName = ''
    subNotFound = SubLanguageID
    subPaths = {}
    while True:
        badSubtitles,subPaths,subNotFound,imdbIDTemp,movieNameTemp,movieYearTemp = download_subtitles(token,searchBy,moviePath,movieName,badSubtitles,subNotFound,subPaths)
        if imdbIDTemp:
            imdbID = imdbIDTemp
            movieName = movieNameTemp
            movieYear = movieYearTemp

        # Continue if some subtitles were not downloaded and we are not searching by name
        if subNotFound:
            if not None in searchBy.values():
                continue
        
        # Check output and decide what to do next
        subprocess.call(['mplayer', moviePath])
        try:    
            subprocess.check_output('zenity --question --title="Is everything alright?" --text="Were ' + str(len(SubLanguageID)) + ' subtitles downloaded and are they in sync?" --ok-label=Yes --cancel-label=No',stderr=subprocess.STDOUT, shell=True)
            # If everything is alright, this did not raise an exception and we can break while loop
            break
        except subprocess.CalledProcessError:
            try:
                # Only ask which subtitles are out of sync if there are more than one
                if badNumber > 1: 
                    a = []
                    # a are various combinations that can be wrong
                    [a.extend(list(itertools.combinations(subPaths.keys(),i+1))) for i in range(len(subPaths.values()))]
                    b = [list(i) for i in a]
                    d = 'TRUE'
                    # Construct zenity dialog
                    for i in b:
                        d += ' "' + str(i).strip('[]').replace("'","") + '" "'
                        for j in i:
                            y = j.split(',')
                            d += ''.join([languages[x] if x == y[-1] else languages[x] + ' or ' for x in y])
                            if not j == i[-1]:
                                d += ' and '
                            else:
                                d += '" FALSE '
                    badTiming = subprocess.check_output('zenity --width=720 --height=560  --list --text="What is wrong?" --radiolist --column=Pick --column=Combinations --column="Language(s) out of sync" ' + d + 'False "I made a mistake, all subtitles are bad"',stderr=subprocess.STDOUT, shell=True).strip('\n')
                # Some subtitles selected, so we need to go back and pick other subtitles
                if not badTiming == 'False':
                    subNotFound = badTiming.replace(' ','').split(',')
                    badNumber = len(subNotFound)
                    for i in subPaths.keys():
                        if i in subNotFound:
                            del subPaths[i]
                else:
                    subNotFound = SubLanguageID
            except subprocess.CalledProcessError:
                    break
    # Disconnect
    server.LogOut(token)

    # FIXME this does not work:
    # Print a message if some/all subtitles not found
    langFound =[i[1] for i in subPaths.values()]
    if len(langFound) < len(SubLanguageID):
        langFoundStr = ''
        # Only list languages if more languages are downloaded
        langNotFound = ''
        if len(SubLanguageID) > 1 or len(SubLanguageID[0]) > 1:
            langNotFound = ' in:\n'
            for lang in get_lang(subNotFound):
                if lang not in langFound:
                    langNotFound += languages[lang] + '\n'
            if langFound:
                langFoundStr = '\n\nHowever, following subtitles were downloaded:\n'
                for lang in langFound:
                    langFoundStr += languages[lang] + '\n' 
        subprocess.call(['zenity', '--info', '--title=No subtitles found', '--text=No subtitles found' + langNotFound + 'for this video:\n' + moviePath.rsplit('/')[-1] + langFoundStr])
    # Merge subtitle files with the video
    
    # Get movie title and language from IMDB
    # If it takes too long, try again and again and then fail.

    for i in range(3):
        try: 
            imdbMovie = imdb.IMDb(timeout=7,reraiseExceptions=True).get_movie(imdbID)
            movieLanguageFull = imdbMovie.get('languages')[0]
            timedOut = False
            break
        except imdb.IMDbDataAccessError:
            timedOut = True

    # Ask about the language of the movie, since imdbpy stalled
    if timedOut:          
        try:
            # subprocess.call(['zenity', '--error', '--text=Unable to connect to IMDb, aborting. Please check:\n- Your internet connection status\n- www.imdb.com availability and imdbpy status'])
            movieLanguageFull = subprocess.check_output('zenity --width=200 --height=420  --list --text=Pick\ Language --radiolist --column=Pick --column=Languages TRUE eng FALSE fre FALSE cze FALSE ger FALSE chi FALSE ita FALSE jpn FALSE kor FALSE rus FALSE spa FALSE swe FALSE nor FALSE dan FALSE fin',stderr=subprocess.STDOUT, shell=True  )
        except subprocess.CalledProcessError:
            # The user pressed cancel, logout and exit
            server.LogOut(token)
            sys.exit(1)
    
    # Get three-letter ISO code
    for lang in languages:
        if languages[lang] == movieLanguageFull and len(lang) == 3: 
            movieLanguageISO = lang

    
    # Get English title if movie is not in English
    movieNameEng = ''
    movieNameEngTemp = ''
    movieNameMkv = ''
    movieName = handleArticles(movieName)
    if not movieLanguageFull == 'English':
        pickMovieName = 'TRUE "'+ imdbMovie.get('title') + '" "IMDb Title" ' 
        for aka in imdbMovie.get('akas'):
            if 'English' in aka.split('::')[1]:
                movieNameEng = handleArticles(aka.split('::')[0])
                break
            else: 
                pickMovieName +=   'FALSE "' + '" "'.join(aka.split('::')) + '" '
        if not movieNameEng:  
            try:
                movieNameEngTemp = subprocess.check_output('zenity --width=720 --height=560  --list --text=Pick\ English\ title --radiolist --column=Pick --column=Titles --column=IMDd\ descriptions ' + pickMovieName + 'FALSE False "No suitable title found"',stderr=subprocess.STDOUT, shell=True)
            except subprocess.CalledProcessError:
                pass
            if movieNameEngTemp == 'False\n':
                try:
                    movieNameEngTemp = subprocess.check_output('zenity --entry --text="Enter the title of the movie (articles can be in front)"',stderr=subprocess.STDOUT, shell=True)
                except subprocess.CalledProcessError:
                    pass
            movieNameEng = handleArticles(movieNameEngTemp.replace('\n',''))

        if not movieNameEng == movieName:
            movieNameMkv = movieNameEng + '-'

    # Prepare command for subtitles
    mmgLangs = ''
    mmgSubArgs = ''
    trackOrder = '0:0,0:1'
    index = 0
    for lang in langFound:
        for k in subPaths.keys():
            if subPaths[k][1] == lang:
                key = k 
        index += 1
        if lang == langFound[-1]:
            mmgLangs += lang
        else:
            mmgLangs += lang + '_'
        mmgSubArgs += '--language 0:' + lang + ' --forced-track 0:no -s 0 -D -A -T --no-global-tags --no-chapters ' + '"' + subPaths[key][0] + '" '
        trackOrder += ',' + str(index) + ':0' 
    
    # Finally merge the file    
    mkvFileName = os.path.dirname(moviePath) + '/' + movieNameMkv.replace(' ','_').lower() + movieName.replace(' ','_').lower() + '-' + movieYear + '-a_' + movieLanguageISO  + '-s_'+ mmgLangs + '.mkv'
    
    try:
        subprocess.check_output('mkvmerge -o "' + mkvFileName + '" --language 0:' + movieLanguageISO + ' --forced-track 0:no --language 1:' + movieLanguageISO + ' --forced-track 1:no -a 1 -d 0 -S -T --no-global-tags --no-chapters "' + moviePath + '" ' + mmgSubArgs + '--track-order ' + trackOrder + '  | stdbuf -i0 -o0 -e0 tr \'\\r\' \'\\n\' |   stdbuf -i0 -o0 -e0 grep \'Progress:\' | stdbuf -i0 -e0  -o0 sed -e \'s/Progress: //\' -e \'s/%//\' -e \'s/\(....\)\(..\)\(..\)/\1-\^C\3/\' | zenity --width=710 --progress --auto-close --percentage=0 --text="Merging..." --title="Merging ' + moviePath.rsplit('/')[-1] + ' with subtitles, please wait..."',stderr=subprocess.STDOUT,  shell=True)        
        move = True
    except subprocess.CalledProcessError:
        move = False
    
    if move:
        if not movieNameEng:
            movieDirName = movieName
        else:
            movieDirName = movieNameEng + ' - ' + movieName

        # Move resulting file to a specified directory
        newFileDirPath = pathToMoveResultingFileTo + movieDirName + '/'
        if pathToMoveResultingFileTo:
            if not os.path.exists(pathToMoveResultingFileTo):
                os.makedirs(pathToMoveResultingFileTo)
            if not os.path.exists(newFileDirPath):
                os.makedirs(newFileDirPath)
            newFilePath = newFileDirPath + mkvFileName.rsplit('/')[-1]
            if os.path.exists(newFilePath):
                subprocess.call('trash "' + newFilePath  + '"', shell=True)
            shutil.move(mkvFileName,newFileDirPath)
            # Play the file to see whether everything is ok
            """
            # Trash the original directory
            if os.getcwd() == moviePath.rsplit('/')[-1]:
                os.chdir(os.pardir)
            if not os.getcwd() == newFilePath:
                if not moviePath.rsplit('/')[-1] == '/home/drew/Desktop':
                    subprocess.call('trash "' + moviePath.rsplit('/')[-1] + '"', shell=True)
                else:
                    filesToTrash = '"' + '" "'.join([i[0] for i in subPaths.values()]) + '"'
                    if os.path.exists(newFilePath):
                       filesToTrash += ' "' + moviePath + '"'
                    subprocess.call('trash ' + filesToTrash, shell=True)
            """
    #newPath = "".join(['/' + i for i in  subDirName.split("/")[1:-1]]) + '/'
    
    #if not movieNameEng:
    #    os.rename(subDirName,movieName)
    #    newPath += movieName
    #else:
    #    os.rename(subDirName,movieNameEng)
    #    newPath += movieNameEng
    
    sys.exit(0)
    
except Error:
    # If an unknown error occur, say so (and apologize)
    subprocess.call(['zenity', '--error', '--text=An unknown error occurred, sorry about that... Please check:\n- Your internet connection status\n- www.opensubtitles.org availability'])
    sys.exit(1)

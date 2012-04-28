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
import traceback
from sys import argv
from xmlrpclib import ServerProxy, Error

# ==== Language selection ======================================================
# You can change the search language here by using either 2-letter (ISO 639-1) 
# or 3-letter (ISO 639-2) language codes.
# Supported ISO codes: http://www.opensubtitles.org/addons/export_languages.php

SubLanguageID = ['eng','cze']


# ==== File moving ============================================================
# Specify directory where the resulting matroska file should be moved. 
# Do not forget the trailing slash'
# Turn this of by uncommenting the following line a commenting the next line:

#pathToMoveResultingFileTo = ''
pathToMoveResultingFileTo = '/home/drew/Desktop/Filmy/'

languages = {'alb': 'Albanian',  'ara': 'Arabic',  'arm': 'Armenian', 'may': 'Malay',  'bos': 'Bosnian',  'pob': 'Brazilian',  'bul': 'Bulgarian',  'cat': 'Catalan',  'eus': 'Basque',  'chi': 'Chinese',  'hrv': 'Croatian',  'cze': 'Czech',  'dan': 'Danish',  'dut': 'Dutch',  'eng': 'English', 'bre': 'British English', 'epo': 'Esperanto',  'est': 'Estonian',  'fin': 'Finnish',  'fre': 'French',  'geo': 'Georgian',  'ger': 'German',  'ell': 'Greek',  'heb': 'Hebrew',  'hun': 'Hungarian', 'ice':'Icelandic', 'ind': 'Indonesian',  'ita': 'Italian',  'jpn': 'Japanese',  'kaz': 'Kazakh',  'kor': 'Korean',  'lav': 'Latvian',  'lit': 'Lithuanian',  'ltz': 'Luxembourgish',  'mac': 'Macedonian',  'nor': 'Norwegian',  'per': 'Persian',  'pol': 'Polish',  'por': 'Portuguese',  'rum': 'Romanian',  'rus': 'Russian',  'scc': 'Serbian',  'slo': 'Slovak',  'slv': 'Slovenian',  'spa': 'Spanish',  'swe': 'Swedish',  'tha': 'Thai',  'tur': 'Turkish',  'ukr': 'Ukrainian',  'vie': 'Vietnamese', 'sq': 'Albanian',  'ar': 'Arabic',  'hy': 'Armenian', 'ms': 'Malay',  'bs': 'Bosnian',  'pb': 'Brazilian',  'bg': 'Bulgarian',  'ca': 'Catalan',  'eu': 'Basque',  'zh': 'Chinese',  'hrv': 'Croatian',  'cs': 'Czech',  'da': 'Danish',  'nl': 'Dutch',  'en': 'English', 'eo':	'Esperanto', 'et': 'Estonian',  'fi': 'Finnish',  'fr': 'French',  'ka': 'Georgian',  'de': 'German',  'el': 'Greek',  'he': 'Hebrew',  'hu': 'Hungarian', 'is':'Icelandic',  'id': 'Indonesian',  'it': 'Italian',  'ja': 'Japanese', 'kk': 'Kazakh', 'ko': 'Korean', 'mk': 'Macedonian',  'lv': 'Latvian',  'lt': 'Lithuanian',  'lb': 'Luxembourgish',  'no': 'Norwegian',  'fa': 'Persian',  'pl': 'Polish',  'pt': 'Portuguese',  'ro': 'Romanian',  'ru': 'Russian',  'sr': 'Serbian',  'sk': 'Slovak',  'sl': 'Slovenian',  'es': 'Spanish',  'sv': 'Swedish',  'th': 'Thai',  'tr': 'Turkish',  'uk': 'Ukrainian',  'vi': 'Vietnamese'}

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

    fileMimeType = None
    fileMimeType, encoding = mimetypes.guess_type(path)
    if fileMimeType:
        fileMimeType = fileMimeType.split('/', 1)
        if fileMimeType[0] == 'video':
            return 'Video'
    fileExtension = path.rsplit('.', 1)
    if fileExtension[1] in ['3g2', '3gp', '3gp2', '3gpp', 'ajp', \
    'asf', 'asx', 'avchd', 'avi', 'bik', 'bix', 'box', 'cam', 'dat', \
    'divx', 'dmf', 'dv', 'dvr-ms', 'evo', 'flc', 'fli', 'flic', 'flv', \
    'flx', 'gvi', 'gvp', 'h264', 'm1v', 'm2p', 'm2ts', 'm2v', 'm4e', \
    'm4v', 'mjp', 'mjpeg', 'mjpg', 'mkv', 'moov', 'mov', 'movhd', 'movie', \
    'movx', 'mp4', 'mpe', 'mpeg', 'mpg', 'mpv', 'mpv2', 'mxf', 'nsv', \
    'nut', 'ogg', 'ogm', 'ogv', 'omf', 'ps', 'qt', 'ram', 'rm', 'rmvb', \
    'swf', 'ts', 'vfw', 'vid', 'video', 'viv', 'vivo', 'vob', 'vro', \
    'webm', 'wm', 'wmv', 'wmx', 'wrap', 'wvx', 'wx', 'x264', 'xvid']:
        return 'Video'
    elif fileExtension[1] in ['sub','srt']:
        return 'Subs'
    else:
        #subprocess.call(['zenity', '--error', '--text=This file is not a video (unknown mimetype AND invalid file extension):\n- ' + path])
        return False
    

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
    for i in allSubs[:]:
        if i[:-1].isdigit():
            i = allSubs.index(i)
            if not '-->' in allSubs[i+1]:
                if not '-->' in allSubs[i-1]:
                    i -= delta
                    editedSubsList = editSubtitles(allSubs[i-6:i+7],'Something wrong with the subtitles, please inspect')
                    allSubs = allSubs[:i-6] + editedSubsList + allSubs[i+7:]
                    delta += 13 - len(editedSubsList)

    # Delete some automatically inserted subtitles
    deleteLines = ['Najlepsi zazitok z pozerania - Open Subtitles MKV Player\n','[ENGLISH]\n','Best watched using Open Subtitles MKV Player\n','FDb.cz - navstivte svet filmu\n','Subtitles downloaded from www.OpenSubtitles.org\n','Download Movie Subtitles Searcher from www.OpenSubtitles.org\n','www.titulky.com\n','WWW:TITULKY.COM\n','www.Titulky.com\n','SDI Media Group\n','De Aldisio, Agence Press.\n','Video SubtitIes By\n','www.OpenSubtitles.org\n','www.OpenSubtitles.org\n']
    deleteLinesIndexes = [allSubs.index(i) for i in allSubs if i in deleteLines]
    delta = 0
    for index in deleteLinesIndexes:
        index -= delta
        up = index
        down = index
        cont1,cont2 = True,True
        while cont1 or cont2:
            if cont1:
                if ' --> ' in allSubs[down]:
                    indexDown = down-1
                    cont1 = False
                if down < len(allSubs) - 1:
                    down += 1
                else:
                    indexDown = down + 1
                    cont1 = False
            if cont2:
                if ' --> ' in allSubs[up]:
                    indexUp = up-1
                    cont2 = False
                if up > 0:
                    up -= 1
                else:
                    indexUp = up
                    cont2 = False
        allSubs = allSubs[0 : indexUp] + allSubs[indexDown:]
        delta += indexDown-indexUp

    # Remove blank lines in the end and in the beginning
    while allSubs[0] == '\n':
        del allSubs[0]
    while allSubs[-1] == '\n':
        del allSubs[-1]

    # Edit beginning and end for signatures and so on
    startEndOfSubs = allSubs[:15] + ['=================<88>=================\n'] + allSubs[-12:]
    editedSubsList = editSubtitles(startEndOfSubs,'Delete cruft from beginning and end')                    
    cutIndex = editedSubsList.index('=================<88>=================\n')
    allSubs = editedSubsList[:cutIndex] + allSubs[15:-12] + editedSubsList[cutIndex+1:]
    f = open(subPathEdit, "w")
    f.write(''.join(allSubs))
    f.close()
    return subPathsEdit

# ==== Download subtitles ======================================================
# Download subtitles
def download_subtitles(token,searchByDown,moviePathDown,movieNameDown,imdbIDDown,movieYearDown,badSubtitlesDown,subNotFoundDown,subPathsDown):
    # Search for available subtitles (using file hash and size)
    movieHash = hashFile(moviePathDown)
    movieSize = os.path.getsize(moviePathDown)
    #moviePathDown = os.path.abspath(moviePathDown)

    for lang in subNotFoundDown[:]:
        searchList = []
        # Search movie by file hash
        if searchBy[lang] == 'Hash': 
            searchList.append({'sublanguageid':lang, 'moviehash':movieHash, 'moviebytesize':str(movieSize)})
        # Search for available subtitles (using file name)
        elif searchBy[lang] == 'Name':
            print movieNameDown,333
            if len(movieNameDown) > 0: # Search movie by movie name
                print 1
                searchList.append({'sublanguageid':lang, 'query':movieNameDown})
            else: # Search movie by file name
                searchList.append({'sublanguageid':lang, 'query':moviePathDown.rsplit('/')[-1].rsplit('.')[-2]}) 


        # Launch the search
        subtitlesList = server.SearchSubtitles(token, searchList)    
        if subtitlesList['data']:

            # Sanitize title strings to avoid parsing errors
            for item in subtitlesList['data']:
                item['MovieName'] = item['MovieName'].replace('"', '\\"')
                item['MovieName'] = item['MovieName'].replace("'", "\'")
           
            # If there are more than one subtitles, let the user decide which  will be downloaded
            onlyOne = False
            if len(subtitlesList['data']) != 1:
                print 2
                subtitleItems = ''
                for item in subtitlesList['data']:
                    if not item['IDSubtitleFile'] in badSubtitlesDown[lang]:
                        # Give the user some additional information about the subtitles
                        hearingImpaired = ''
                        if item['SubHearingImpaired'] == '1':
                            hearingImpaired += 'Yes' #'✓' # FIXME: This breaks with more then ten subtitles, wait for python3 what it does:
                        else: 
                            hearingImpaired += '\'\''
                        CD = ''
                        if int(item['SubSumCD']) > 1:
                            CD += str(item['SubActualCD']) + '/' + str(item['SubSumCD'])
                        else:
                            CD += '\'\''         
                        subtitleItems += item['IDSubtitleFile'] + ' "' + item['SubFileName'] + '" ' + item['LanguageName'] + ' ' + hearingImpaired + ' ' + CD + ' ' + item['SubFormat']  + ' ' + item['IDMovieImdb'] + ' ' +item['SubDownloadsCnt'] + ' '
                if not len(subtitlesList['data']) == len(badSubtitlesDown[lang]):
                    process_subtitleSelection = subprocess.Popen('zenity --width=1280 --height=480 --list --title="' + os.path.basename(moviePathDown) + ' - ' + searchBy[lang] + '" --column=subID --column="Available subtitles" --column="Language" --column="Hearing impaired" --column="CD" --column="Format" --column="IMDb ID" --column="Download count" '  + subtitleItems, shell=True, stdout=subprocess.PIPE)
                    # FIXME --print-column vrati sloupce co clovek chce, opravit to a poslat do upstreamu u filmu hot fuzz od axxa se to projevuje
                    subtitleSelected = str(process_subtitleSelection.communicate()[0]).strip('\n')
                    resp = process_subtitleSelection.returncode

                else:
                    resp = 'Full'
                (imdbIDGroupDown,movieNameGroupDown,movieYearGroupDown) = [],[],[]
                for item in subtitlesList['data']:
                    imdbIDGroupDown.append(item['IDMovieImdb'])
                    movieNameGroupDown.append(item['MovieName'])
                    movieYearGroupDown.append(item['MovieYear'])
                if searchBy[lang] == 'Hash': # If searching by filename, the results might be bad
                    if imdbIDDown == '':
                        imdbIDDown = collections.Counter(imdbIDGroupDown).most_common()[0][0]
                        movieNameDown = collections.Counter(movieNameGroupDown).most_common()[0][0]
                        movieYearDown = collections.Counter(movieYearGroupDown).most_common()[0][0]
                else:
                    if imdbIDDown == '':
                        try:
                            subprocess.check_output('zenity --question --title="do we have the right movie" --text="Is IMDBID, name and year plausible?" --ok-label=Yes --cancel-label=No',stderr=subprocess.STDOUT, shell=True)
                            imdbIDDown = collections.Counter(imdbIDGroupDown).most_common()[0][0]
                            movieNameDown = collections.Counter(movieNameGroupDown).most_common()[0][0]
                            movieYearDown = collections.Counter(movieYearGroupDown).most_common()[0][0]
                        except subprocess.CalledProcessError:
                            pass
            else:
                subtitleSelected = ''
                resp = 0
                onlyOne = True
                   
            if resp == 0:
                # Select subtitle file to download
                index = 0
                subIndex = 0
                for item in subtitlesList['data']:
                    if item['IDSubtitleFile'] == subtitleSelected:
                        subIndex = index
                    else:
                        index += 1
                 
                badSubtitlesDown[lang].append(subtitlesList['data'][subIndex]['IDSubtitleFile']) # assume the subtitles are bad
                subURL = subtitlesList['data'][subIndex]['SubDownloadLink']
                subFileName = os.path.basename(moviePathDown[:-4] + '_' +  subtitlesList['data'][subIndex]['SubLanguageID'] + subtitlesList['data'][subIndex]['SubFileName'][-4:])
                subFileName = subFileName.replace('"', '\\"')
                subFileName = subFileName.replace("'", "\'")
                subPath=os.path.dirname(moviePathDown) + '/' + subFileName
                subPathsDown[lang]=[subPath,lang]
                subNotFoundDown.remove(lang) 

                # Download and unzip selected subtitles (with progressbar)
                process_subDownload = subprocess.call('(wget -O - ' + subURL + ' | gunzip  > "' + subPath + '") 2>&1 | zenity --progress --auto-close --pulsate --title="Downloading subtitle, please wait..." --text="Downloading subtitle for \'' + subtitlesList['data'][0]['MovieName'] + '\' : "', shell=True)
                
                # Edit subtitles
                subPathsDown = editSubs(subtitlesList['data'][subIndex]['SubLanguageID'],subPath,subtitlesList['data'][subIndex]['SubFormat'],moviePathDown,subPathsDown)

                # If an error occur, say so
                if process_subDownload != 0:
                   subprocess.call(['zenity', '--error', '--text=An error occurred while downloading or writing the selected subtitle.'])
            elif resp == 'Full' or resp == 1:
                if searchBy[lang] == 'Hash':
                    searchBy[lang] = 'Name'
                else:
                    searchBy[lang] = None
                if resp == 'Full':
                    del subPathsDown[lang]
            if onlyOne:
                if searchBy[lang] == 'Hash':
                    searchBy[lang] = 'Name'
                else:
                    searchBy[lang] = None
        else:
            if searchBy[lang] == 'Hash':
                searchBy[lang] = 'Name'
            else:
                if movieNameDown == '': # Ask user about file name
                    try:
                        movieNameDown = subprocess.check_output('zenity --width=600 --text="Just title, I guess" --entry --title="What is the title of the movie?" --entry-text="' + moviePathDown.rsplit('/')[-1].rsplit('.')[-2] + '"',shell=True,stderr=subprocess.STDOUT).strip('\n')
                    except subprocess.CalledProcessError:
                        sys.exit(1)
                else:
                    searchBy[lang] = None

            # Behave nicely if user is searching for multiple languages at once
            #langLookedFor = re.split(r"\s*,\s*", lang)
            #for l in langLookedFor:
    return badSubtitlesDown,subPathsDown,subNotFoundDown,imdbIDDown,movieNameDown,movieYearDown

# ==== Dismantle list in lists =================================================
"""[a,b,[a,b,[a,b]]] na ["a","b","a,b","a,b"]"""
def get_lang(listGlobal):
    list = [i for i in listGlobal]
    a = []
    while list:
        if str(list[0])[0] == '[':
            if str(list[0])[-1] == ']':
                #list.extend(get_lang(list.pop(0))) # Removes all lists and appends it elements
                a.append(','.join(list.pop(0)))
            else:
                a.append(list.pop(0))
        else:
            a.append(list.pop(0))
    return a

# ==== Make list of lists ======================================================
"""['a','b',['a,b']] na [['a'],['b'],['a','b']]"""
def make_list(listGlobal):
    list = [i for i in listGlobal]
    a = []
    while list:
        if str(list[0])[0] == '[':
            if str(list[0])[-1] == ']':
                 a.append(list.pop(0)[0].replace(' ','').split(','))
            else:
                a.append([list.pop(0)])
        else:
            a.append([list.pop(0)])
    return a

# ==== Merge into a matroska file =============================================
# Merge subtitle files with the video
def merge(merged,imdbID,movieName,movieYear,langFound,subPaths,moviePath):
    # Get movie title and language from IMDB
    # If it takes too long, try again and again and then fail.
    if subPathExternalDict:
        for sub in subPathExternalDict:
            subPaths[sub] = [subPathExternalDict[sub][0],sub] 
            langFound.append(sub)
        if merged:
            mkvFileName = moviePath.rsplit('.')[-2].rsplit('-s_')[:-1][0] + '-s_' + '_'.join(langFound) + '.mkv'
            movieLanguageISO = moviePath.rsplit('-a_')[-1][:3]
            movieNameEng = moviePath.split('-')[0].rsplit('/')[-1]
    if not merged:
        movieLanguageFull = ''
        title = ''
        for i in range(3):
            try:
                # Find imdbID when all subtitles have been downloaded manually and we have not ever merged yet
                if not imdbID:
                    if not title:
                        try:
                            title = subprocess.check_output('zenity --width=600 --text="Year is helpful, dots, underscores are ok" --entry --title="What is the title of the movie?" --entry-text="' + moviePath.rsplit('/')[-1] + '"',shell=True,stderr=subprocess.STDOUT).strip('\n')
                        except subprocess.CalledProcessError:
                            sys.exit(1)
                    results = imdb.IMDb(timeout=7,reraiseExceptions=True).search_movie(title)
                    a = u''
                    for movie in results:
                        for movie in results:
                             a += unicode(movie.movieID) + ' "' + movie['title'] + '" '
                             # Year might not be set
                             try:
                                 a += unicode(movie['year'])
                             except KeyError:
                                 a += u'????'
                             a += ' '
                    try:
                        imdbID = subprocess.check_output('zenity --width=800 --height=480  --list --text=Pick\ movie --column=imdbID --column=Title --column=Year --text="Edit title" ' + a  ,stderr=subprocess.STDOUT, shell=True)                            
                    except subprocess.CalledProcessError:
                        sys.exit(1)
                imdbMovie = imdb.IMDb(timeout=7,reraiseExceptions=True).get_movie(imdbID)
                if not movieName:
                    movieName = imdbMovie['title']
                if not movieYear:
                    movieYear = str(imdbMovie['year'])
                movieLanguageFull = imdbMovie.get('languages')[0]
                timedOut = False
                break
            except imdb.IMDbDataAccessError:
                timedOut = True

        # Ask about the language of the movie, since imdbpy stalled
        if timedOut:          
            try:
                # subprocess.call(['zenity', '--error', '--text=Unable to connect to IMDb, aborting. Please check:\n- Your internet connection status\n- www.imdb.com availability and imdbpy status'])
                movieLanguageISO = subprocess.check_output('zenity --width=200 --height=420  --list --text=Pick\ Language --column=Languages  eng  fre cze ger chi ita jpn kor rus spa swe nor dan fin',stderr=subprocess.STDOUT, shell=True  ).strip('\n')

            except subprocess.CalledProcessError:
                # The user pressed cancel, logout and exit
                #server.LogOut(token) # We should log out here, but this situation is so scarce it does not matter probably
                sys.exit(1)
            try:
                if not title:
                    title = moviePath.rsplit('/')[-1] 
                if not movieName:
                    movieName = subprocess.check_output('zenity --width=600  --title=Movie\ title --entry --text="Enter movie title, articles can we anywhere" --entry-text="' + title + '"',stderr=subprocess.STDOUT, shell=True  )
                    if movieLanguageISO == 'eng':
                        movieNameMkv = subprocess.check_output('zenity --width=600  --title=Movie\ title --entry --text="Enter title in original language, do not worry about dash" --entry-text="' + title + '"',stderr=subprocess.STDOUT, shell=True  ).strip('\n')
                        movieNameMkv += '-'

            except subprocess.CalledProcessError:
                sys.exit(1)
            try:
                if not movieYear:
                    movieYear = subprocess.check_output('zenity --width=600  --entry --text="Enter movie year" --title="' + moviePath.rsplit('/')[-1] + '"',stderr=subprocess.STDOUT, shell=True).strip('\n')
            except subprocess.CalledProcessError:
                sys.exit(1)
    
        # Get three-letter ISO code
        if movieLanguageFull:
            for lang in languages:
                if languages[lang] == movieLanguageFull and len(lang) == 3: 
                    movieLanguageISO = lang

    
        # Get English title if movie is not in English
        movieNameEng = ''
        movieNameEngTemp = ''
        movieNameMkv = ''
        movieName = handleArticles(movieName)
        pickMovieName = ''
        if not movieLanguageISO == 'eng' and not timedOut:
            for aka in imdbMovie.get('akas'):
                if 'English' in aka.split('::')[1]:
                    movieNameEng = handleArticles(aka.split('::')[0])
                    break
                else: 
                    pickMovieName += ' "' + '" "'.join(aka.split('::')) + '" '
            if not movieNameEng:  
                try:
                    movieNameEngTemp = subprocess.check_output('zenity --width=720 --height=560  --list --text=Pick\ English\ title --column=Titles --column=IMDd\ descriptions ' + pickMovieName + 'False "No suitable title found"',stderr=subprocess.STDOUT, shell=True)
                except subprocess.CalledProcessError:
                    sys.exit(1)
                if movieNameEngTemp == 'False\n':
                    try:
                        movieNameEngTemp = subprocess.check_output('zenity --entry --text="Enter the title of the movie (articles can be in front)"',stderr=subprocess.STDOUT, shell=True)
                    except subprocess.CalledProcessError:
                        sys.exit(1)
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
    if not merged:
        #FIXME run with ipython3 and see wheter it can handle files with unicode character \xc3 in path
        mkvFileName = os.path.dirname(moviePath) + '/' + movieNameMkv.replace(' ','_').lower() + movieName.replace(' ','_').lower() + '-' + movieYear + '-a_' + movieLanguageISO  + '-s_'+ mmgLangs + '.mkv'
    
    try:
        subprocess.check_output('mkvmerge -o "' + mkvFileName + '" --language 0:' + movieLanguageISO + ' --forced-track 0:no --language 1:' + movieLanguageISO + ' --forced-track 1:no -a 1 -d 0 -S -T --no-global-tags --no-chapters "' + moviePath + '" ' + mmgSubArgs + '--track-order ' + trackOrder + '|tee temp  | stdbuf -i0 -o0 -e0 tr \'\\r\' \'\\n\' |   stdbuf -i0 -o0 -e0 grep \'Progress:\' | stdbuf -i0 -e0  -o0 sed -e \'s/Progress: //\' -e \'s/%//\' -e \'s/\(....\)\(..\)\(..\)/\1-\^C\3/\' | zenity --width=710 --progress --auto-close --percentage=0 --text="Merging..." --title="Merging ' + moviePath.rsplit('/')[-1] + ' with subtitles, please wait..."',stderr=subprocess.STDOUT,  shell=True)        
        subprocess.call('xx=`cat temp` ; if cat temp | grep -q Error || cat temp | grep -q Warning; then zenity --no-markup --info --title="Mkvmerge error" --text "$xx" ; fi ; rm temp',shell=True)
        move = True
    except subprocess.CalledProcessError:
        move = False
        sys.exit(1)
    return mkvFileName,movieNameEng,movieName,move

# ==== Get file(s) path(s) =====================================================
# Get opensubtitles-download script path, then remove it from argv list
execPath = argv[0]
argv.pop(0) 
moviePath = ''
subPathExternalList = []
#subprocess.call(['zenity', '--info', '--text=v'])
if len(argv) == 0:
    #subprocess.call(['zenity', '--error', '--text=No file selected.'])
    sys.exit(1)
breaking = False
index = 0
for a in argv:
    if '--file' == a:
        moviePath = os.path.abspath(argv[index+1])
        breaking = True
        # If another argument is subtitle, we suppose that it is a missing subtitle and that we know the language
    if '--sub' == a:
        subPathExternalList.append(os.path.abspath(argv[index+1]))
        breaking = True
    index += 1

if not breaking:
    filePathList = []
    moviePathList = []
    try:
        # Fill filePathList (using nautilus script)
        filePathList = os.environ['NAUTILUS_SCRIPT_SELECTED_FILE_PATHS'].splitlines()
    except Exception:
        # Fill filePathList (using program arguments)
        for i in argv:
            filePathList.append(os.path.abspath(i))

    # Check file(s) type
    for i in filePathList:
        if checkFile(i) == 'Video':
            moviePathList.append(os.path.abspath(i))
        elif checkFile(i) == 'Subs':
            subPathExternalList.append(os.path.abspath(i))
    
    # If moviePathList is empty, abort
    if len(moviePathList) == 0:
        sys.exit(1)
    
    # The first file will be processed immediatly
    moviePath = moviePathList[0]
    moviePathList.pop(0)
    
    # The remaining file(s) are dispatched to new instance(s) of this script
    for i in moviePathList:
        process_movieDispatched = subprocess.Popen([execPath, '--file', i])
# Error catching (z mmgmerge nejak divertvnout), a vubec projit vsechny try
# ==== Main program ============================================================
try:
    searchBy = {}
    badSubtitles = {}
    for lang in SubLanguageID:
        searchBy[lang] = 'Hash'  
        badSubtitles[lang] = []
    badTiming = ''
    imdbID = ''
    movieName = ''
    movieYear = ''

    
    subPaths = {}
    subNotFound = SubLanguageID

    # ==== Parse external and merged subtitles =================================
    subPathExternalDict = {}
    for sub in subPathExternalList[:]:
        if sub.rsplit('.')[-1] in  ['sub','srt']:
            subLangsPossible = sub.rsplit('.')[-2].rsplit('_')[-1]
            if subLangsPossible in languages.keys():
                subPathExternalDict[subLangsPossible] = [sub,subLangsPossible]
                subNotFound = get_lang([b for b in make_list(subNotFound) if subLangsPossible not in b])
            # Only one possible langueage     
            elif len(subNotFound) <= 1:
                if len(make_list(subNotFound)[0]) == 1:
                    a = subNotFound.pop(0)
                    subNotFound
                    subPathExternalDict[a] = [sub,a]

            else:
                possibleLanguages = ''
                for lang in get_lang(SubLanguageID):
                     possibleLanguages += lang + ' "' + sub.rsplit('/')[-1] + '" '
                try:
                    subLangsPossible  = subprocess.check_output('zenity --width=560 --height=240  --list --title="What is the language of the subtitles?" --column=Language --column="File path" ' + possibleLanguages,stderr=subprocess.STDOUT, shell=True).strip('\n')
                    subPathExternalDict[subLangsPossible] = [sub,subLangsPossible]
                    subNotFound = get_lang([b for b in make_list(subNotFound) if subLangsPossible not in b])
                except subprocess.CalledProcessError:
                    subprocess.call('zenity --error --text="User pressed cancel, aborting"',shell=True)
                    sys.exit(1)
            subPathExternalDict =  editSubs(subLangsPossible,sub,sub.rsplit('.')[-1],moviePath,subPathExternalDict)
    # In the end, check whether we have some subtitles already 
    else:
        alreadyMerged = False
        if  moviePath.rsplit('.')[-1] == 'mkv':
            subLangsPossible = moviePath.rsplit('.')[-2].rsplit('-s_')[-1].split('_')
            for lang in  subLangsPossible:
                if lang in languages.keys():
                    subPathExternalDict[lang] = [moviePath,lang]
                    subNotFound = get_lang([b for b in make_list(subNotFound) if lang not in b])
                    alreadyMerged = True
    badNumber = len(subNotFound)

    # ==== Download subtitles from the net ====================================
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
    movieName = ''
    while subNotFound:
        subLookedFor = list(subNotFound)
        # Did we exhaust all posibilities?
        breaking = True
        for sub in subNotFound:
            if not searchBy[sub] == None:
                breaking = False
        if breaking:
            subLookedFor = []
            break
        badSubtitles,subPaths,subNotFound,imdbIDTemp,movieNameTemp,movieYearTemp = download_subtitles(token,searchBy,moviePath,movieName,imdbID,movieYear,badSubtitles,subNotFound,subPaths)
        print badSubtitles,subPaths,subNotFound,imdbIDTemp,movieNameTemp,movieYearTemp

        if imdbIDTemp or movieNameTemp:
            imdbID = imdbIDTemp
            movieName = movieNameTemp
            movieYear = movieYearTemp
        
        # Continue if some subtitles were not downloaded and we are not searching by name
        if subNotFound:
            if not None in searchBy.values():
                continue
        
        # Check output and decide what to do next
        subprocess.call(['mplayer','-fs','-osdlevel','3', moviePath])
        try:    
            subprocess.check_output('zenity --question --title="Is everything alright?" --text="Are subtitles downloaded and are they in sync?" --ok-label=Yes --cancel-label=No',stderr=subprocess.STDOUT, shell=True)
            # If everything is alright, this did not raise an exception and we can break while loop
            break
        except subprocess.CalledProcessError:
            # Only ask which subtitles are out of sync if there are more than one
            if badNumber > 1: 
                a = []
                # a are various combinations that can be wrong
                [a.extend(list(itertools.combinations(subPaths.keys(),i+1))) for i in range(len(subPaths.values()))]
                b = [list(i) for i in a]
                d = ''
                # Construct zenity dialog
                for i in b:
                    d += ' "' + str(i).strip('[]').replace("'","") + '" "'
                    for j in i:
                        y = j.split(',')
                        d += ''.join([languages[x] if x == y[-1] else languages[x] + ' or ' for x in y])
                        if not j == i[-1]:
                            d += ' and '
                        else:
                            d += '" '
                try:
                    badTiming = subprocess.check_output('zenity --width=720 --height=560  --list --text="What is wrong?" --column=Combinations --column="Language(s) out of sync" ' + d + ' False "I made a mistake, all subtitles are bad" True "I made a mistake, all subtitles are good" Break "Abort whatever we are doing"',stderr=subprocess.STDOUT, shell=True).strip('\n')
                # Assume all is alright when user cancels
                except subprocess.CalledProcessError:
                    break
                            
                # Some subtitles selected, so we need to go back and pick other subtitles
                if badTiming == 'False':
                    # No subtitles fit and none were downloaded, abort and sort manually
                    if len(subPathExternalDict) == len(SubLanguageID):
                        sys.exit(1)
                    else:
                        subNotFound = [lang for lang in SubLanguageID if lang not in subPathExternalDict.keys()]

                elif badTiming == 'True':
                    subNotFound = []
                elif badTiming == 'Break':
                    sys.exit(1)
                else:
                    subNotFound = badTiming.replace(' ','').split(',')
                    badNumber = len(subNotFound)
                    for i in subPaths.keys():
                        if i in subNotFound:
                            del subPaths[i]
            else:
                subNotFound = subLookedFor
            
    # Disconnect
    server.LogOut(token)

    # print a message if some/all subtitles not found
    langFound =[i[1] for i in subPaths.values()]
    if len(langFound) < (len(SubLanguageID)-len(subPathExternalDict)):
        langFoundStr = ''
        # Only list languages if more languages are downloaded
        langNotFound = ''
        if len(SubLanguageID) > 1 or len(SubLanguageID[0]) > 3: # SubLnguageID is a string
            langNotFound = ' in:\n'
            for lang in get_lang(subNotFound):
                if lang not in langFound:
                    langNotFound += languages[lang] + '\n'
            if langFound:
                langFoundStr = '\n\nHowever, following subtitles were downloaded:\n'
                for lang in langFound:
                    langFoundStr += languages[lang] + '\n' 
        subprocess.call(['zenity', '--info', '--title=No subtitles found', '--text=No subtitles found' + langNotFound + 'for this video:\n' + moviePath.rsplit('/')[-1] + langFoundStr])

    # call matroska 
    mkvFileName,movieNameEng,movieName,move = merge(alreadyMerged,imdbID,movieName,movieYear,langFound,subPaths,moviePath)
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
                subprocess.call('trash-put "' + newFilePath  + '"', shell=True)
            shutil.move(mkvFileName,newFileDirPath)
            # Play the file to see whether everything is ok
            subprocess.call(['mplayer','-fs','-osdlevel', '3', newFilePath])
            # Trash the original directory
            if os.getcwd() == moviePath.rsplit('/')[-1]:
                os.chdir(os.pardir)
            if not os.getcwd() == newFilePath:
                if not '/'.join(moviePath.rsplit('/')[:-1]) == '/home/drew/Desktop':
                    subprocess.call('trash-put "' + '/'.join(moviePath.rsplit('/')[:-1]) + '"', shell=True)
                else:
                    filesToTrash = '"' + '" "'.join([i[0] for i in subPaths.values()]) + '"'
                    if os.path.exists(newFilePath):
                       filesToTrash += ' "' + moviePath + '"'
                    subprocess.call('trash-put ' + filesToTrash, shell=True)
    sys.exit(0)
    
except Exception,e:
    a = traceback.format_exc()
    subprocess.call(['zenity','width=1024','--no-markup', '--error', '--text=An unknown error occurred, sorry about that... Please check:\n- Your internet connection status\n- www.opensubtitles.org availability\n\nError was:\n' + str(e) + '\n\nTraceback was:\n' + a])
    sys.exit(1)

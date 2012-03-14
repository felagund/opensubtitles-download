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
import tempfile
import signal
import re
import struct
import subprocess
import mimetypes
import imdb
import chardet
from sys import argv
from xmlrpclib import ServerProxy, Error

# ==== Language selection ======================================================
# You can change the search language here by using either 2-letter (ISO 639-1) 
# or 3-letter (ISO 639-2) language codes.
# Supported ISO codes: http://www.opensubtitles.org/addons/export_languages.php

SubLanguageID = ['eng','cze']
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
    subPaths = {}
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
                    subtitleItems += '"' + item['SubFileName'] + '" ' + item['LanguageName'] + ' ' + hearingImpaired + ' ' + CD + ' ' + item['SubFormat']  + ' ' + item['IDMovieImdb'] + ' ' +item['SubDownloadsCnt'] + ' '
                    #if item['SubFileName'][:-3] == os.path.basename(moviePath)[:-3]:
                    #    subtitleSelected = item['SubFileName']
                    #    break
                    #else:
                    #    subtitleSelected = ''

                #if not subtitleSelected:
                process_subtitleSelection = subprocess.Popen('zenity --width=1024 --height=480 --list --title="' + os.path.basename(moviePath) + '" --column="Available subtitles" --column="Language" --column="Hearing impaired" --column="CD" --column="Format" --column="IMDb ID" --column="Download count" '  + subtitleItems, shell=True, stdout=subprocess.PIPE)
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
                subDirName = os.path.abspath(os.path.dirname(moviePath))
                subURL = subtitlesList['data'][subIndex]['SubDownloadLink']
                subFileName = os.path.basename(moviePath)[:-4] + '_' + subFound[-1] + subtitlesList['data'][subIndex]['SubFileName'][-4:]
                subFileName = subFileName.replace('"', '\\"')
                subFileName = subFileName.replace("'", "\'")
                subPath=subDirName + '/' + subFileName
                subPaths[lang]=subPath

                # Convert subtitles to unicode
                if languages[subFound[-1]] == 'Czech':
                    encConv = '| enconv -L czech -x utf8'
                else:
                    encConv = ''

                # Download and unzip selected subtitle (with progressbar)
                
                process_subDownload = subprocess.call('(wget -O - ' + subURL + ' | gunzip ' + encConv + ' | dos2unix | mac2unix > "' + subPath + '") 2>&1 | zenity --progress --auto-close --pulsate --title="Downloading subtitle, please wait..." --text="Downloading subtitle for \'' + subtitlesList['data'][0]['MovieName'] + '\' : "', shell=True)
                
                # Convert English subtitles to unicode (only if the use some special character, otherwise stay ascii which we do not mind)
                if languages[subFound[-1]] == 'English':
                    f = open(subPath,"r").read()
                    enc = chardet.detect(f)['encoding']
                    tmp = f.decode(enc)
                    f = open(subPath, 'w')
                    f.write(tmp.encode('utf-8'))
                    f.close()
                    #subprocess.call('iconv --from-code=' + enc + ' --to=utf-8 "'+ subPath + '" > "' + subPath + 'a"',shell=True) 


                #| sed -e :a -e \'$d;N;2,3ba\' -e \'P;D\'
                # Handle non srt formats
                subFormat = subtitlesList['data'][subIndex]['SubFormat']
                if subFormat == 'srt':
                    pass
                elif subFormat == 'sub':
                    #subprocess.call(['zenity', '--error', '--text=Subtitle in format ' + 'sub' + '. Check the program.'])
                    mplayerOutput = subprocess.Popen(("mplayer", "-identify", "-frames", "0", "o-ao", "null", moviePath), stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
                    pattern = re.compile(r'(\d{2}.\d{3}) fps')
                    fps = pattern.search(mplayerOutput).groups()[0]
                    subprocess.call(['subconv','-f', fps, subPath, subPath[:-3] + 'srt'])
                    subPath = subPath[:-3] + 'srt'
                    subPaths[lang]=subPath
                else:
                    subprocess.call(['zenity', '--error', '--text=Subtitle in format ' + subFormat + '. Expect trouble.'])

                # Inspect beginning and the end of the subtitle and edit it
                f = open(subPath,"r")
                allSubs =  f.readlines()
                startEndOfSubs = allSubs[:12] + ['=================<88>=================\n'] + allSubs[-12:]
                tmp = tempfile.TemporaryFile()
                tmp.write(''.join(startEndOfSubs))
                tmp.seek(0)
                editedSubsString = subprocess.Popen(['zenity', '--width=480', '--height=720', '--text-info', '--editable', '--title="Delete cruft from beginning and end"'],stdin=tmp, stdout=subprocess.PIPE).communicate()[0]
                editedSubsList = [i+ '\n' for i in editedSubsString.split("\n")]
                cutIndex = editedSubsList.index('=================<88>=================\n')
                allSubs = editedSubsList[:cutIndex] + allSubs[12:-12] + editedSubsList[cutIndex+1:]
                f = open(subPath, "w")
                f.write(''.join(allSubs))
                f.close()
                tmp.close()

                # If an error occur, say so
                if process_subDownload != 0:
                    subprocess.call(['zenity', '--error', '--text=An error occurred while downloading or writing the selected subtitle.'])
        else:
            
            # Behave nicely if user is searching for multiple languages at once
            langLookedFor = re.split(r"\s*,\s*", lang)
            for l in langLookedFor:
                subNotFound.append(l)

    # Print a message if some/all subtitles not found
    if subNotFound:
        langFound = ''
        # Only list languages if more languages are downloaded
        langNotFound = ''
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
    
    # Merge subtitle files with the video
    # Prepare command for subtitles
    mmgLangs = ''
    mmgSubArgs = []
    trackOrder = '0:0,0:1'
    index = 0
    for lang in subFound:
        index += 1
        if lang == subFound[-1]:
            mmgLangs += lang
        else:
            mmgLangs += lang + '_'
        mmgSubArgs += ['--language', '0:' + lang, '--forced-track', '0:no', '-s', '0', '-D', '-A', '-T', '--no-global-tags', '--no-chapters', subPaths[lang]]
        trackOrder += ',' + str(index) + ':0' 
    
    # Ask about the language of the movie
    #try:
    #    movieLanguage = subprocess.check_output('zenity --width=200 --height=420  --list --text=Pick\ Language --radiolist --column=Pick --column=Languages TRUE eng FALSE fre FALSE cze FALSE ger FALSE chi FALSE ita FALSE jpn FALSE kor FALSE rus FALSE spa FALSE swe FALSE nor FALSE dan FALSE fin',stderr=subprocess.STDOUT, shell=True  )
    #except subprocess.CalledProcessError:
    
    # Get movie title and language from IMDB
    # If it takes too long ,try again and again and then fail.
    def handler(signum, frame):
        raise IOError("IMDb is taking too long")
    signal.signal(signal.SIGALRM, handler)
    
    imdbMovie = None
    for i in range(3):
        if imdbMovie:
            break
        try:
         try:
          try:
           try:
            try:
             try: # for some reason, just one try is not enough
                    signal.alarm(7)
                    imdbMovie = imdb.IMDb().get_movie(subtitlesList['data'][0]['IDMovieImdb'])
           
             except:
                 pass
            except:
                pass
           except:
               pass
          except:
              pass
         except:
             pass
        except:
            pass
        signal.alarm(0)   
    if not imdbMovie:
        subprocess.call(['zenity', '--error', '--text=Unable to connect to IMDb, aborting. Please check:\n- Your internet connection status\n- www.imdb.com availability and imdbpy status'])
    
    movieLanguageFull = imdbMovie.get('languages')[0]
    
    # Get three-letter ISO code
    for lang in languages:
        if languages[lang] == movieLanguageFull and len(lang) == 3: 
            movieLanguageISO = lang

    
    # Get English title if movie is not in English
    engMovieName = ''
    mkvMovieName = ''
    movieName = handleArticles(subtitlesList['data'][0]['MovieName'])
    if not movieLanguageFull == 'English':
        pickMovieName = 'TRUE "'+ imdbMovie.get('title') + '" "IMDb Title" ' 
        for aka in imdbMovie.get('akas'):
            if 'English' in aka.split('::')[1]:
                engMovieName = handleArticles(aka.split('::')[0])
                break
            else: 
                pickMovieName +=   'FALSE "' + '" "'.join(aka.split('::')) + '" '
        if not engMovieName:  
            try:
                engMovieNameTemp = subprocess.check_output('zenity --width=720 --height=560  --list --text=Pick\ English\ title --radiolist --column=Pick --column=Titles --column=IMDd\ descriptions ' + pickMovieName,stderr=subprocess.STDOUT, shell=True)
            except subprocess.CalledProcessError:
                pass
            engMovieName = handleArticles(engMovieNameTemp.replace('\n',''))
        if not engMovieName == movieName:
            mkvMovieName = engMovieName + '-'
    
    # Finally merge the file    
    mkvFileName = ['mkvmerge', '-o', subDirName + '/' + mkvMovieName.replace(' ','_').lower() + movieName.replace(' ','_').lower() + '-' + subtitlesList['data'][0]['MovieYear'] + '-a_' + movieLanguageISO  + '-s_'+ mmgLangs + '.mkv']
    subprocess.call(mkvFileName + ['--language', '0:' + movieLanguageISO, '--forced-track', '0:no', '--language', '1:' + movieLanguageISO, '--forced-track', '1:no', '-a', '1', '-d', '0', '-S', '-T', '--no-global-tags', '--no-chapters', moviePath] + mmgSubArgs + ['--track-order', trackOrder])
    
    # Rename parent directory
    if os.getcwd() == subDirName:
        os.chdir(os.pardir)
    if not engMovieName:
        os.rename(subDirName,movieName)
    else:
        os.rename(subDirName,engMovieName)

    # Disconnect from opensubtitles.org server, then exit
    server.LogOut(token)
    exit(0)
except Error:

    # If an unknown error occur, say so (and apologize)
    subprocess.call(['zenity', '--error', '--text=An unknown error occurred, sorry about that... Please check:\n- Your internet connection status\n- www.opensubtitles.org availability'])
    exit(1)

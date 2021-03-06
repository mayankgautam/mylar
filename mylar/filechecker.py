#/usr/bin/env python
#  This file is part of Mylar.
#
#  Mylar is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Mylar is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Mylar.  If not, see <http://www.gnu.org/licenses/>.

import os
import os.path
import pprint
import subprocess
import re
import logger
import mylar
import sys

def file2comicmatch(watchmatch):
    #print ("match: " + str(watchmatch))
    pass

def listFiles(dir,watchcomic,Publisher,AlternateSearch=None,manual=None,sarc=None):

    # use AlternateSearch to check for filenames that follow that naming pattern
    # ie. Star Trek TNG Doctor Who Assimilation won't get hits as the 
    # checker looks for Star Trek TNG Doctor Who Assimilation2 (according to CV)
    
    # we need to convert to ascii, as watchcomic is utf-8 and special chars f'it up
    u_watchcomic = watchcomic.encode('ascii', 'ignore').strip()    
    logger.fdebug('[FILECHECKER] comic: ' + watchcomic)
    basedir = dir
    logger.fdebug('[FILECHECKER] Looking in: ' + dir)
    watchmatch = {}
    comiclist = []
    comiccnt = 0
    not_these = ['#',
               ',',
               '\/',
               ':',
               '\;',
               '.',
               '-',
               '!',
               '\$',
               '\%',
               '\+',
               '\'',
               '\?',
               '\@']

    issue_exceptions = ['AU',
                      '.INH',
                      '.NOW',
                      'AI', 
                      'A',
                      'B',
                      'C']

    extensions = ('.cbr', '.cbz')

    for item in os.listdir(basedir):
        if item == 'cover.jpg' or item == 'cvinfo': continue
        if not item.endswith(extensions):
            logger.fdebug('[FILECHECKER] filename not a valid cbr/cbz - ignoring: ' + item)
            continue

        #print item
        #subname = os.path.join(basedir, item)
        subname = item

        #versioning - remove it
        subsplit = subname.replace('_', ' ').split()
        volrem = None
        for subit in subsplit:
            if subit[0].lower() == 'v':
                vfull = 0
                if subit[1:].isdigit():
                    #if in format v1, v2009 etc...
                    if len(subit) > 3:
                        # if it's greater than 3 in length, then the format is Vyyyy
                        vfull = 1 # add on 1 character length to account for extra space
                    subname = re.sub(subit, '', subname)
                    volrem = subit
                elif subit.lower()[:3] == 'vol':
                    #if in format vol.2013 etc
                    #because the '.' in Vol. gets removed, let's loop thru again after the Vol hit to remove it entirely
                    logger.fdebug('[FILECHECKER] volume indicator detected as version #:' + str(subit))
                    subname = re.sub(subit, '', subname)
                    volrem = subit

        #check if a year is present in series title (ie. spider-man 2099)
        numberinseries = 'False'

        for i in watchcomic.split():
            if ('20' in i or '19' in i):
                if i.isdigit():
                    numberinseries = 'True'
                else:
                    find20 = i.find('20')
                    if find20:
                        stf = i[find20:4].strip()
                    find19 = i.find('19')
                    if find19:
                        stf = i[find19:4].strip()
                    logger.fdebug('[FILECHECKER] stf is : ' + str(stf))
                    if stf.isdigit():
                        numberinseries = 'True'
 
        logger.fdebug('[FILECHECKER] numberinseries: ' + numberinseries)

        #remove the brackets..
        subnm = re.findall('[^()]+', subname)
        logger.fdebug('[FILECHECKER] subnm len : ' + str(len(subnm)))
        if len(subnm) == 1:
            logger.fdebug('[FILECHECKER] ' + str(len(subnm)) + ': detected invalid filename - attempting to detect year to continue')
            #if the series has digits this f's it up.
            if numberinseries == 'True':
                #we need to remove the series from the subname and then search the remainder.
                watchname = re.sub('[-\:\;\!\'\/\?\+\=\_\%\.]', '', watchcomic)   #remove spec chars for watchcomic match.
                logger.fdebug('[FILECHECKER] watch-cleaned: ' + str(watchname))
                subthis = re.sub('.cbr', '', subname)
                subthis = re.sub('.cbz', '', subthis)
                subthis = re.sub('[-\:\;\!\'\/\?\+\=\_\%\.]', '', subthis)
                logger.fdebug('[FILECHECKER] sub-cleaned: ' + str(subthis))
                subthis = subthis[len(watchname):]  #remove watchcomic
                #we need to now check the remainder of the string for digits assuming it's a possible year
                logger.fdebug('[FILECHECKER] new subname: ' + str(subthis))
                subname = re.sub('(.*)\s+(19\d{2}|20\d{2})(.*)', '\\1 (\\2) \\3', subthis)
                subname = watchcomic + subname
                subnm = re.findall('[^()]+', subname)
            else:
                subit = re.sub('(.*)\s+(19\d{2}|20\d{2})(.*)', '\\1 (\\2) \\3', subname)
                subthis2 = re.sub('.cbr', '', subit)
                subthis1 = re.sub('.cbz', '', subthis2)
                subname = re.sub('[-\:\;\!\'\/\?\+\=\_\%\.]', '', subthis1)
                subnm = re.findall('[^()]+', subname)
        if Publisher.lower() in subname.lower():
            #if the Publisher is given within the title or filename even (for some reason, some people
            #have this to distinguish different titles), let's remove it entirely.
            lenm = len(subnm)

            cnt = 0
            pub_removed = None

            while (cnt < lenm):
                if subnm[cnt] is None: break
                if subnm[cnt] == ' ':
                    pass
                else:
                    logger.fdebug(str(cnt) + ". Bracket Word: " + str(subnm[cnt]))

                if Publisher.lower() in subnm[cnt].lower() and cnt >= 1:
                    logger.fdebug('Publisher detected within title : ' + str(subnm[cnt]))
                    logger.fdebug('cnt is : ' + str(cnt) + ' --- Publisher is: ' + Publisher)
                    pub_removed = subnm[cnt]
                    #-strip publisher if exists here-
                    logger.fdebug('removing publisher from title')
                    subname_pubremoved = re.sub(pub_removed, '', subname)
                    logger.fdebug('pubremoved : ' + str(subname_pubremoved))
                    subname_pubremoved = re.sub('\(\)', '', subname_pubremoved) #remove empty brackets
                    subname_pubremoved = re.sub('\s+', ' ', subname_pubremoved) #remove spaces > 1
                    logger.fdebug('blank brackets removed: ' + str(subname_pubremoved))
                    subnm = re.findall('[^()]+', subname_pubremoved)
                    break
                cnt+=1
        subname = subnm[0]

        if len(subnm):
            # if it still has no year (brackets), check setting and either assume no year needed.
            subname = subname                
        logger.fdebug('[FILECHECKER] subname no brackets: ' + str(subname))
        subname = re.sub('\_', ' ', subname)
        nonocount = 0
        charpos = 0
        detneg = "no"
        leavehyphen = False
        should_restart = True
        while should_restart:
            should_restart = False
            for nono in not_these:
                if nono in subname:
                    subcnt = subname.count(nono)
                    charpos = indices(subname,nono) # will return a list of char positions in subname
                    #print "charpos: " + str(charpos)
                    if nono == '-':
                        i=0
                        while (i < len(charpos)):
                            for i,j in enumerate(charpos):
                                if j+2 > len(subname): 
                                    sublimit = subname[j+1:]
                                else:
                                    sublimit = subname[j+1:j+2]
                                if sublimit.isdigit():
                                    logger.fdebug('[FILECHECKER] possible negative issue detected.')
                                    nonocount = nonocount + subcnt - 1
                                    detneg = "yes"                                
                                elif '-' in watchcomic and i < len(watchcomic):
                                    logger.fdebug('[FILECHECKER] - appears in series title.')
                                    logger.fdebug('[FILECHECKER] up to - :' + subname[:j+1].replace('-', ' '))
                                    logger.fdebug('[FILECHECKER] after -  :' + subname[j+1:])
                                    subname = subname[:j+1].replace('-', ' ') + subname[j+1:]
                                    logger.fdebug('[FILECHECKER] new subname is : ' +  str(subname))
                                    should_restart = True
                                    leavehyphen = True
                            i+=1
                        if detneg == "no" or leavehyphen == False: 
                            subname = re.sub(str(nono), ' ', subname)
                            nonocount = nonocount + subcnt
                #logger.fdebug('[FILECHECKER] (str(nono) + " detected " + str(subcnt) + " times.")
                # segment '.' having a . by itself will denote the entire string which we don't want
                    elif nono == '.':
                        x = 0
                        fndit = 0
                        dcspace = 0
                        while x < subcnt:
                            fndit = subname.find(nono, fndit)
                            if subname[fndit-1:fndit].isdigit() and subname[fndit+1:fndit+2].isdigit():
                                logger.fdebug('[FILECHECKER] decimal issue detected.')
                                dcspace+=1
                            x+=1
                        if dcspace == 1:
                            nonocount = nonocount + subcnt + dcspace                    
                        else:
                            subname = re.sub('\.', ' ', subname)
                            nonocount = nonocount + subcnt - 1 #(remove the extension from the length)
                    else:
                        #this is new - if it's a symbol seperated by a space on each side it drags in an extra char.
                        x = 0
                        fndit = 0
                        blspc = 0
                        while x < subcnt:
                            fndit = subname.find(nono, fndit)
                            #print ("space before check: " + str(subname[fndit-1:fndit]))
                            #print ("space after check: " + str(subname[fndit+1:fndit+2]))
                            if subname[fndit-1:fndit] == ' ' and subname[fndit+1:fndit+2] == ' ':
                                logger.fdebug('[FILECHECKER] blankspace detected before and after ' + str(nono))
                                blspc+=1
                            x+=1
                        subname = re.sub(str(nono), ' ', subname)
                        nonocount = nonocount + subcnt + blspc
        #subname = re.sub('[\_\#\,\/\:\;\.\-\!\$\%\+\'\?\@]',' ', subname)

        modwatchcomic = re.sub('[\_\#\,\/\:\;\.\!\$\%\'\?\@\-]', ' ', u_watchcomic)
        #if leavehyphen == False:
        #    logger.fdebug('[FILECHECKER] ('removing hyphen for comparisons')
        #    modwatchcomic = re.sub('-', ' ', modwatchcomic)
        #    subname = re.sub('-', ' ', subname)
        detectand = False
        detectthe = False
        modwatchcomic = re.sub('\&', ' and ', modwatchcomic)
        if ' the ' in modwatchcomic.lower():
            modwatchcomic = re.sub("\\bthe\\b", "", modwatchcomic.lower())
            logger.fdebug('[FILECHECKER] new modwatchcomic: ' + str(modwatchcomic))
            detectthe = True
        modwatchcomic = re.sub('\s+', ' ', str(modwatchcomic)).strip()
        if '&' in subname:
            subname = re.sub('\&', ' and ', subname) 
            detectand = True
        if ' the ' in subname.lower():
            subname = re.sub("\\bthe\\b", "", subname.lower())
            detectthe = True
        subname = re.sub('\s+', ' ', str(subname)).strip()

        AS_Alt = []
        if AlternateSearch is not None:
            chkthealt = AlternateSearch.split('##')
            if chkthealt == 0:
                AS_Alternate = AlternateSearch
            for calt in chkthealt:
                AS_Alternate = re.sub('##','',calt)
                #same = encode.
                u_altsearchcomic = AS_Alternate.encode('ascii', 'ignore').strip()
                altsearchcomic = re.sub('[\_\#\,\/\:\;\.\-\!\$\%\+\'\?\@]', ' ', u_altsearchcomic)
                altsearchcomic = re.sub('\&', ' and ', altsearchcomic)
                altsearchcomic = re.sub('\s+', ' ', str(altsearchcomic)).strip()       
                AS_Alt.append(altsearchcomic)
        else:
            #create random characters so it will never match.
            altsearchcomic = "127372873872871091383 abdkhjhskjhkjdhakajhf"
            AS_Alt.append(altsearchcomic)
        #if '_' in subname:
        #    subname = subname.replace('_', ' ')
        logger.fdebug('[FILECHECKER] watchcomic:' + str(modwatchcomic) + ' ..comparing to found file: ' + str(subname))
        if modwatchcomic.lower() in subname.lower() or any(x.lower() in subname.lower() for x in AS_Alt):#altsearchcomic.lower() in subname.lower():
            comicpath = os.path.join(basedir, item)
            logger.fdebug('[FILECHECKER] ' + modwatchcomic + ' - watchlist match on : ' + comicpath)
            comicsize = os.path.getsize(comicpath)
            #print ("Comicsize:" + str(comicsize))
            comiccnt+=1

            stann = 0
            if 'annual' in subname.lower():
                logger.fdebug('[FILECHECKER] Annual detected - proceeding')
                jtd_len = subname.lower().find('annual')
                cchk = modwatchcomic
            else:
                if modwatchcomic.lower() in subname.lower():
                    cchk = modwatchcomic
                else:
                    cchk_ls = [x for x in AS_Alt if x.lower() in subname.lower()]
                    cchk = cchk_ls[0]
                    #print "something: " + str(cchk)

                logger.fdebug('[FILECHECKER] we should remove ' + str(nonocount) + ' characters')                

                findtitlepos = subname.find('-')
                if charpos != 0:
                    logger.fdebug('[FILECHECKER] detected ' + str(len(charpos)) + ' special characters')
                    i=0
                    while (i < len(charpos)):
                        for i,j in enumerate(charpos):
                            #print i,j
                            #print subname
                            #print "digitchk: " + str(subname[j:])
                            if j >= len(subname):
                                logger.fdebug('[FILECHECKER] end reached. ignoring remainder.')
                                break
                            elif subname[j:] == '-':
                                if i <= len(subname) and subname[i+1].isdigit():
                                    logger.fdebug('[FILECHECKER] negative issue detected.')
                                    #detneg = "yes"
                            elif j > findtitlepos:
                                if subname[j:] == '#':
                                   if subname[i+1].isdigit():
                                        logger.fdebug('[FILECHECKER] # detected denoting issue#, ignoring.')
                                   else: 
                                        nonocount-=1
                                elif '-' in watchcomic and i < len(watchcomic):
                                   logger.fdebug('[FILECHECKER] - appears in series title, ignoring.')
                                else:                             
                                   logger.fdebug('[FILECHECKER] special character appears outside of title - ignoring @ position: ' + str(charpos[i]))
                                   nonocount-=1
                        i+=1

            #remove versioning here
            if volrem != None:
                jtd_len = len(cchk)# + len(volrem)# + nonocount + 1 #1 is to account for space btwn comic and vol #
            else:
                jtd_len = len(cchk)# + nonocount

            if sarc and mylar.READ2FILENAME:
                removest = subname.find(' ') # the - gets removed above so we test for the first blank space...
                if subname[:removest].isdigit():
                    jtd_len += removest + 1  # +1 to account for space in place of - 
                    logger.fdebug('[FILECHECKER] adjusted jtd_len to : ' + str(removest) + ' because of story-arc reading order tags')

            logger.fdebug('[FILECHECKER] nonocount [' + str(nonocount) + '] cchk [' + cchk + '] length [' + str(len(cchk)) + ']')

            #if detectand:
            #    jtd_len = jtd_len - 2 # char substitution diff between & and 'and' = 2 chars
            #if detectthe:
            #    jtd_len = jtd_len - 3  # char subsitiution diff between 'the' and '' = 3 chars

            #justthedigits = item[jtd_len:]

            logger.fdebug('[FILECHECKER] final jtd_len to prune [' + str(jtd_len) + ']')
            logger.fdebug('[FILECHECKER] before title removed from FILENAME [' + str(item) + ']')
            logger.fdebug('[FILECHECKER] after title removed from FILENAME [' + str(item[jtd_len:]) + ']')
            logger.fdebug('[FILECHECKER] creating just the digits using SUBNAME, pruning first [' + str(jtd_len) + '] chars from [' + subname + ']')

            justthedigits_1 = subname[jtd_len:].strip()

            logger.fdebug('[FILECHECKER] after title removed from SUBNAME [' + justthedigits_1 + ']')

            #remove the title if it appears
            #findtitle = justthedigits.find('-')
            #if findtitle > 0 and detneg == "no":
            #    justthedigits = justthedigits[:findtitle]
            #    logger.fdebug('[FILECHECKER] ("removed title from name - is now : " + str(justthedigits))

            justthedigits = justthedigits_1.split(' ', 1)[0]
            
            digitsvalid = "false"

            for jdc in list(justthedigits):
                #logger.fdebug('[FILECHECKER] ('jdc:' + str(jdc))
                if not jdc.isdigit():
                    #logger.fdebug('[FILECHECKER] ('alpha')
                    jdc_start = justthedigits.find(jdc)
                    alpha_isschk = justthedigits[jdc_start:]
                    #logger.fdebug('[FILECHECKER] ('alpha_isschk:' + str(alpha_isschk))
                    for issexcept in issue_exceptions:
                        if issexcept.lower() in alpha_isschk.lower() and len(alpha_isschk) <= len(issexcept):
                            logger.fdebug('[FILECHECKER] ALPHANUMERIC EXCEPTION : [' + justthedigits + ']')
                            digitsvalid = "true"
                            break
                if digitsvalid == "true": break

            try:
                tmpthedigits = justthedigits_1.split(' ', 1)[1]
                logger.fdebug('[FILECHECKER] If the series has a decimal, this should be a number [' + tmpthedigits + ']')
                if 'cbr' in tmpthedigits.lower() or 'cbz' in tmpthedigits.lower():
                    tmpthedigits = tmpthedigits[:-3].strip()
                    logger.fdebug('[FILECHECKER] Removed extension - now we should just have a number [' + tmpthedigits + ']')
                poss_alpha = tmpthedigits
                if poss_alpha.isdigit():
                    digitsvalid = "true"
                    if justthedigits.lower() == 'annual':
                        logger.fdebug('[FILECHECKER] ANNUAL DETECTED ['  + poss_alpha + ']')
                        justthedigits += ' ' + poss_alpha
                    else:
                        justthedigits += '.' + poss_alpha
                        logger.fdebug('[FILECHECKER] DECIMAL ISSUE DETECTED [' + justthedigits + ']')
                else:
                    for issexcept in issue_exceptions:
                        decimalexcept = False
                        if '.' in issexcept:
                            decimalexcept = True
                            issexcept = issexcept[1:] #remove the '.' from comparison...
                        if issexcept.lower() in poss_alpha.lower() and len(poss_alpha) <= len(issexcept):
                            if decimalexcept:
                                issexcept = '.' + issexcept
                            justthedigits += issexcept #poss_alpha
                            logger.fdebug('[FILECHECKER] ALPHANUMERIC EXCEPTION. COMBINING : [' + justthedigits + ']')
                            digitsvalid = "true"
                            break
            except:
                tmpthedigits = None

#            justthedigits = justthedigits.split(' ', 1)[0]

            #if the issue has an alphanumeric (issue_exceptions, join it and push it through)
            logger.fdebug('[FILECHECKER] JUSTTHEDIGITS [' + justthedigits + ']' )
            if digitsvalid == "true":
                pass
            else:
                if justthedigits.isdigit():
                    digitsvalid = "true"
                else:
                    if '.' in justthedigits:
                        tmpdec = justthedigits.find('.')
                        b4dec = justthedigits[:tmpdec]
                        a4dec = justthedigits[tmpdec+1:]
                        if a4dec.isdigit() and b4dec.isdigit():
                            logger.fdebug('[FILECHECKER] DECIMAL ISSUE DETECTED')
                            digitsvalid = "true"
                    else:
                        try:
                            x = float(justthedigits)
                            #validity check
                            if x < 0:
                                logger.info("I've encountered a negative issue #: " + str(justthedigits) + ". Trying to accomodate.")
                                digitsvalid = "true"
                            else: raise ValueError
                        except ValueError, e:
                                logger.info('Cannot determine issue number from given issue #: ' + str(justthedigits))


#                else:
#                    logger.fdebug('[FILECHECKER] NO DECIMALS DETECTED')
#                    digitsvalid = "false"

#            if justthedigits.lower() == 'annual':
#                logger.fdebug('[FILECHECKER] ANNUAL ['  + tmpthedigits.split(' ', 1)[1] + ']')
#                justthedigits += ' ' + tmpthedigits.split(' ', 1)[1]
#                digitsvalid = "true"
#            else:               
#                try:
#                    if tmpthedigits.isdigit(): #.split(' ', 1)[1] is not None:
#                        poss_alpha = tmpthedigits#.split(' ', 1)[1]
#                        if poss_alpha.isdigit():
#                            digitsvalid = "true"
#                            justthedigits += '.' + poss_alpha
#                            logger.fdebug('[FILECHECKER] DECIMAL ISSUE DETECTED [' + justthedigits + ']')
#                        for issexcept in issue_exceptions:
#                            if issexcept.lower() in poss_alpha.lower() and len(poss_alpha) <= len(issexcept):
#                                justthedigits += poss_alpha
#                                logger.fdebug('[FILECHECKER] ALPHANUMERIC EXCEPTION. COMBINING : [' + justthedigits + ']')
#                                digitsvalid = "true"
#                                break
#                except:
#                    pass

            logger.fdebug('[FILECHECKER] final justthedigits [' + justthedigits + ']')
            if digitsvalid == "false": 
                logger.fdebug('[FILECHECKER] Issue number not properly detected...ignoring.')
                comiccnt -=1  # remove the entry from the list count as it was incorrrectly tallied.
                continue            
            

            if manual is not None:
                #this is needed for Manual Run to determine matches
                #without this Batman will match on Batman Incorporated, and Batman and Robin, etc..

                # in case it matches on an Alternate Search pattern, set modwatchcomic to the cchk value
                modwatchcomic = cchk
                logger.fdebug('[FILECHECKER] cchk = ' + cchk.lower())
                logger.fdebug('[FILECHECKER] modwatchcomic = ' + modwatchcomic.lower())
                logger.fdebug('[FILECHECKER] subname = ' + subname.lower())
                comyear = manual['SeriesYear']
                issuetotal = manual['Total']
                comicvolume = manual['ComicVersion']
                logger.fdebug('[FILECHECKER] SeriesYear: ' + str(comyear))
                logger.fdebug('[FILECHECKER] IssueTotal: ' + str(issuetotal))
                logger.fdebug('[FILECHECKER] Comic Volume: ' + str(comicvolume))
                logger.fdebug('[FILECHECKER] volume detected: ' + str(volrem))

                if comicvolume:
                   ComVersChk = re.sub("[^0-9]", "", comicvolume)
                   if ComVersChk == '' or ComVersChk == '1':
                       ComVersChk = 0
                else:
                   ComVersChk = 0

                # even if it's a V1, we need to pull the date for the given issue ID and get the publication year
                # for the issue. Because even if it's a V1, if there are additional Volumes then it's possible that
                # it will take the incorrect series. (ie. Detective Comics (1937) & Detective Comics (2011). 
                # If issue #28 (2013) is found, it exists in both series, and because DC 1937 is a V1, it will bypass 
                # the year check which will result in the incorrect series being picked (1937)


                #set the issue/year threshold here.
                #  2013 - (24issues/12) = 2011.
                #minyear = int(comyear) - (int(issuetotal) / 12)

                maxyear = manual['LatestDate'][:4]  # yyyy-mm-dd

                #subnm defined at being of module.
                len_sm = len(subnm)

                #print ("there are " + str(lenm) + " words.")
                cnt = 0
                yearmatch = "none"
                vers4year = "no"
                vers4vol = "no"

                for ct in subsplit:
                    if ct.lower().startswith('v') and ct[1:].isdigit():
                        logger.fdebug('[FILECHECKER] possible versioning..checking')
                        #we hit a versioning # - account for it
                        if ct[1:].isdigit():
                            if len(ct[1:]) == 4:  #v2013
                                logger.fdebug('[FILECHECKER] Version detected as ' + str(ct))
                                vers4year = "yes" #re.sub("[^0-9]", " ", str(ct)) #remove the v
                                break
                            else:
                                if len(ct) < 4:
                                    logger.fdebug('[FILECHECKER] Version detected as ' + str(ct))
                                    vers4vol = str(ct)
                                    break
                        logger.fdebug('[FILECHECKER] false version detection..ignoring.')

                versionmatch = "false"
                if vers4year is not "no" or vers4vol is not "no":

                    if comicvolume: #is not "None" and comicvolume is not None:
                        D_ComicVersion = re.sub("[^0-9]", "", comicvolume)
                        if D_ComicVersion == '':
                            D_ComicVersion = 0
                    else:
                        D_ComicVersion = 0

                    F_ComicVersion = re.sub("[^0-9]", "", volrem)
                    S_ComicVersion = str(comyear)
                    logger.fdebug('[FILECHECKER] FCVersion: ' + str(F_ComicVersion))
                    logger.fdebug('[FILECHECKER] DCVersion: ' + str(D_ComicVersion))
                    logger.fdebug('[FILECHECKER] SCVersion: ' + str(S_ComicVersion))

                    #if annualize == "true" and int(ComicYear) == int(F_ComicVersion):
                    #    logger.fdebug('[FILECHECKER] ("We matched on versions for annuals " + str(volrem))

                    if int(F_ComicVersion) == int(D_ComicVersion) or int(F_ComicVersion) == int(S_ComicVersion):
                        logger.fdebug('[FILECHECKER] We matched on versions...' + str(volrem))
                        versionmatch = "true"
                    else:
                        logger.fdebug('[FILECHECKER] Versions wrong. Ignoring possible match.')

                #else:
                while (cnt < len_sm):
                    if subnm[cnt] is None: break
                    if subnm[cnt] == ' ':
                        pass
                    else:
                        logger.fdebug('[FILECHECKER] ' + str(cnt) + ' Bracket Word: ' + str(subnm[cnt]))

                        #if ComVersChk == 0:
                        #    logger.fdebug('[FILECHECKER] Series version detected as V1 (only series in existance with that title). Bypassing year check')
                        #    yearmatch = "true"
                        #    break
                    if subnm[cnt][:-2] == '19' or subnm[cnt][:-2] == '20':
                        logger.fdebug('[FILECHECKER] year detected: ' + str(subnm[cnt]))
                        result_comyear = subnm[cnt]
                        if int(result_comyear) <= int(maxyear):
                            logger.fdebug('[FILECHECKER] ' + str(result_comyear) + ' is within the series range of ' + str(comyear) + '-' + str(maxyear))
                            #still possible for incorrect match if multiple reboots of series end/start in same year
                            yearmatch = "true"
                            break
                        else:
                            logger.fdebug('[FILECHECKER] ' + str(result_comyear) + ' - not right - year not within series range of ' + str(comyear) + '-' + str(maxyear))
                            yearmatch = "false"
                            break
                    cnt+=1
                if versionmatch == "false":
                    if yearmatch == "false":
                        logger.fdebug('[FILECHECKER] Failed to match on both version and issue year.')
                        continue
                    else:
                        logger.fdebug('[FILECHECKER] Matched on versions, not on year - continuing.')
                else:
                     if yearmatch == "false":
                        logger.fdebug('[FILECHECKER] Matched on version, but not on year - continuing.')
                     else:
                        logger.fdebug('[FILECHECKER] Matched on both version, and issue year - continuing.')

                if yearmatch == "none":
                    if ComVersChk == 0:
                        logger.fdebug('[FILECHECKER] Series version detected as V1 (only series in existance with that title). Bypassing year check.')
                        yearmatch = "true"
                    else:
                        continue

                if 'annual' in subname.lower():
                    subname = re.sub('annual', '', subname.lower())
                    subname = re.sub('\s+', ' ', subname)

                #tmpitem = item[:jtd_len]
                # if it's an alphanumeric with a space, rejoin, so we can remove it cleanly just below this.
                substring_removal = None
                poss_alpha = subname.split(' ')[-1:]
                logger.fdebug('[FILECHECKER] poss_alpha: ' + str(poss_alpha))
                logger.fdebug('[FILECHECKER] lenalpha: ' + str(len(''.join(poss_alpha))))
                for issexcept in issue_exceptions:
                    if issexcept.lower()in str(poss_alpha).lower() and len(''.join(poss_alpha)) <= len(issexcept):
                        #get the last 2 words so that we can remove them cleanly
                        substring_removal = ' '.join(subname.split(' ')[-2:])
                        substring_join = ''.join(subname.split(' ')[-2:])
                        logger.fdebug('[FILECHECKER] substring_removal: ' + str(substring_removal))
                        logger.fdebug('[FILECHECKER] substring_join: ' + str(substring_join))
                        break

                if substring_removal is not None:
                    sub_removed = subname.replace('_', ' ').replace(substring_removal, substring_join)
                else:
                    sub_removed = subname.replace('_', ' ')
                logger.fdebug('[FILECHECKER] sub_removed: ' + str(sub_removed))
                split_sub = sub_removed.rsplit(' ',1)[0].split(' ')  #removes last word (assuming it's the issue#)
                split_mod = modwatchcomic.replace('_', ' ').split()   #batman
                logger.fdebug('[FILECHECKER] split_sub: ' + str(split_sub))
                logger.fdebug('[FILECHECKER] split_mod: ' + str(split_mod))

                x = len(split_sub)-1
                scnt = 0
                if x > len(split_mod)-1:
                    logger.fdebug('[FILECHECKER] number of words do not match...aborting.')
                else:
                    while ( x > -1 ):
                        print str(split_sub[x]) + ' comparing to ' + str(split_mod[x])
                        if str(split_sub[x]).lower() == str(split_mod[x]).lower():
                            scnt+=1
                            logger.fdebug('[FILECHECKER] word match exact. ' + str(scnt) + '/' + str(len(split_mod)))
                        x-=1

                wordcnt = int(scnt)
                logger.fdebug('[FILECHECKER] scnt:' + str(scnt))
                totalcnt = int(len(split_mod))
                logger.fdebug('[FILECHECKER] split_mod length:' + str(totalcnt))
                try:
                    spercent = (wordcnt/totalcnt) * 100
                except ZeroDivisionError:
                    spercent = 0
                logger.fdebug('[FILECHECKER] we got ' + str(spercent) + ' percent.')
                if int(spercent) >= 80:
                    logger.fdebug('[FILECHECKER] this should be considered an exact match.Justthedigits:' + justthedigits)
                else:
                    logger.fdebug('[FILECHECKER] failure - not an exact match.')
                    continue

            if manual:
                print item
                print comicpath
                print comicsize
                print result_comyear
                print justthedigits
                comiclist.append({
                     'ComicFilename':           item,
                     'ComicLocation':           comicpath,
                     'ComicSize':               comicsize,
                     'ComicYear':               result_comyear,
                     'JusttheDigits':           justthedigits
                     })
                print('appended.')
            else:
                comiclist.append({
                     'ComicFilename':           item,
                     'ComicLocation':           comicpath,
                     'ComicSize':               comicsize,
                     'JusttheDigits':           justthedigits
                     })
            watchmatch['comiclist'] = comiclist
        else:
            pass
            #print ("directory found - ignoring")

    logger.fdebug('[FILECHECKER] you have a total of ' + str(comiccnt) + ' ' + watchcomic + ' comics')
    watchmatch['comiccount'] = comiccnt
    return watchmatch

def validateAndCreateDirectory(dir, create=False):
    if os.path.exists(dir):
        logger.info('Found comic directory: ' + dir)
        return True
    else:
        logger.warn('Could not find comic directory: ' + dir)
        if create:
            if dir.strip():
                logger.info('Creating comic directory (' + str(mylar.CHMOD_DIR) + ') : ' + dir)
                try:
                    permission = int(mylar.CHMOD_DIR, 8)
                    os.umask(0) # this is probably redudant, but it doesn't hurt to clear the umask here.
                    os.makedirs(dir, permission )
                except OSError:
                    raise SystemExit('Could not create data directory: ' + mylar.DATA_DIR + '. Exiting....')
                return True
            else:
                logger.warn('Provided directory is blank, aborting')
                return False
    return False


def indices(string, char):
    return [ i for i,c in enumerate(string) if c == char ]


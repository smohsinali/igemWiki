
#!/usr/bin/python
import cgi
form = cgi.FieldStorage() # instantiate only once!

dwsite = form.getfirst('dwsite', 'empty')
#dwsite = 'labjournal:ilab'

isrmheaderlinks=form.getfirst('rmheaderlink', False)
ischangepicurl=form.getfirst('changepicurl', False)
appendtextbefore=form.getfirst('appendtextbefore', False)
appendtextafter=form.getfirst('appendtextafter', False)
ischangeprotocols=form.getfirst('changeprotocols', False)
isregistry=form.getfirst('changeregistry', False)

# isrmheaderlinks=True
# ischangepicurl=True
# appendtextbefore=True
# appendtextafter=True
# ischangeprotocols=True
# isregistry=True

# textbefore='some text before'
# textafter='some text after'

textbefore = form.getfirst('textbefore', '')
textafter = form.getfirst('textafter', '')

# Avoid script injection escaping the user input
dwsite = cgi.escape(dwsite)

from bs4 import BeautifulSoup # parse raw html and extract elements
import urllib3 # read html-text from url
import requests
from requests.auth import HTTPBasicAuth
import sys
from cStringIO import StringIO
import csv
# import html

old_stdout = sys.stdout
sys.stdout = mystdout = StringIO()

# read in the dict with internal and external protocol names
protocolsdic = {}
reader = csv.DictReader(open('protocols_names.csv', 'r'))
for row in reader:
    protocolsdic[row['internal']] = row['external']

# remove empty dict entries
protocolsdic.pop('', None)

# read in the dict with registry entries to replace
registrydic = {}
reader = csv.DictReader(open('registry_links.csv', 'r'))
for row in reader:
    registrydic[row['internal']] = '<a href=%(x)s>%(y)s</a>' % {'x': '"{}"'.format(row['external']), 'y': row['internal']}


################
# BEGIN DEFINITIONS
################
def getdwsource(dwsite):
    # get the subsite of the internal wiki specified as site
    # use the dummy usre to provide access to the wiki
    dokuwiki=requests.get('https://wiki.uni-freiburg.de/igem2016/doku.php?id=%s&do=export_xhtmlbody'%dwsite, auth=HTTPBasicAuth('alis', 'igem2016'))
    # extract the html of the requests-object by using beautifulsoup
    soup=BeautifulSoup(dokuwiki.text, 'html.parser')
    # print('https://wiki.uni-freiburg.de/igem2016/doku.php?id=%s&do=export_xhtmlbody'%site)
    return soup


def sfah(source):
    # return the soup-objects of all headers
    return source.findAll('h1') + source.findAll('h2') + source.findAll('h3') + source.findAll('h4') + source.findAll('h5') + source.findAll('h6')


def rmheaderlinks(soup):
    ########
    # removes the a-href links from the headers of an internal dw-file
    ########
    rmheaderlinksdic={}
    for header in sfah(soup):
        rmheaderlinksdic[unicode(header.a)] = header.a.text
    return rmheaderlinksdic


def getdwpicnames(source):
    ########
    # returns a dict of the the names of all images in the source code as keys with the corresponding links to the image
    #  and the info-page
    ########
    picnamesdic = {}
    for img in source.find_all('img'):
        # extract the name of all pictures from the src-string
        try:
            # get the name of the picnamesdic
            dwname=img.get('src').split('media=')[1]
            # use the name as key for a dict to store the links for src and href
            picnamesdic[dwname] = [img.get('src')]
            picnamesdic[dwname].append(img.parent.get('href'))
            print('+ \t %s ' % img.get('src').split('media=')[1])
            # print('dwlink=%s'%picnamesdic[dwname])
        except:
            print('- \t\t %s ' % img.get('src').split('/')[-1])
        return picnamesdic


def getpicurl(picname):
    # input: The name of a file uploaded on the iGEM 2016 Wiki-Server #
    # IMPORTANT: The picture has to be uploaded before running the script! #
    # picname=input('please paste the name of an uploaded iGEM-wiki file:\n')

    # correct picname for changes the iGEM-Server needs
    picname=picname.replace(':', '-')

    # define fix url for Wiki-Sever #
    url = 'http://2016.igem.org/File:Freiburg_%s' % picname
    # print('the url I looked for was:\n%s' %url)

    # get raw_html from url as specified here:
    #  http://stackoverflow.com/questions/17257912/how-to-print-raw-html-string-using-urllib3 #

    http_pool = urllib3.connection_from_url(url)
    r = http_pool.urlopen('GET', url)
    raw_html=r.data.decode('utf-8')

    # initialise bs-object '
    soup = BeautifulSoup(raw_html, 'html.parser')

    # find the href-link in an a-object in a div with id=file #
    try:
        serverlink = 'http://2016.igem.org'+soup.find(id='file').find('a').get('href')
        # return the link #
        return serverlink
    except:
        return None


def unescape(s):
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    # this has to be last:
    s = s.replace("&amp;", "&")
    return s


def changeprotocols(soup):
    returndic = {}
    for link in soup.findAll('a'):
        linksource = link.get('href')
        for name in protocolsdic:
            if linksource != None:
                if unicode(name) in linksource :
                    print(unicode(name))
                # generate pairs for replacement using the absolute path for the iGEM server protocols section
                returndic[linksource] = unicode('http://2016.igem.org/Team:Freiburg/Protocols/')+protocolsdic[name]
    return returndic


##########################
# BEGIN PROGRAMME
##########################
if __name__ == "__main__":
    print("hi")
    # set the subprogramcounter
    prog_count = 0

    # get the source code
    dwsource=getdwsource(dwsite)

    # convert it to replaceable text
    exthtml=unicode(dwsource)

    # initialize dic to replace elements
    rpdic = {}

    # ## is rmheaderlinks ###
    if isrmheaderlinks:
        # compute dic to replace headerlinks
        rpdic.update(rmheaderlinks(dwsource))
        prog_count += 1

    # ## is changeprotocols ###
    if ischangeprotocols:
        rpdic.update(changeprotocols(dwsource))
        prog_count += 1

    # ## is changepicurl ###
    missingimage = False

    if ischangepicurl:
        picnamesdic=getdwpicnames(dwsource)

    for key in picnamesdic:
        serverlink=getpicurl(key)

    if serverlink != None:
        rpdic.update({cgi.escape(picnamesdic[key][0]):serverlink})
    else:
        missingimage = True

    if picnamesdic[key][1]:
        rpdic.update({cgi.escape(picnamesdic[key][1]):serverlink})
        prog_count+=1

    # ## is registry ###
    if isregistry:
        rpdic.update(registrydic)
        prog_count+=1

    # ## cancel output if no program was called ###
    if prog_count == 0:
        sys.exit(0)

    # ## replacing ###
    exthtmlold = exthtml
    for text in rpdic.keys():
        # exthtml = exthtml.replace(cgi.escape(text),unescape(rpdic[text]))
        exthtml = exthtml.replace(text,rpdic[text])

    sys.stdout=old_stdout

    if not missingimage:

        print "Content-Disposition: attachment; filename=\"%s.html\"\r\n\n"%dwsite

    if appendtextbefore:
        print(textbefore.encode('utf8'))
        print(exthtml.encode('utf8'))
    if appendtextafter:
        print(textafter.encode('utf8'))
    else:
        print "Content-type: text/html \n"

        print('There is an image missing!!')
        # info

#!/usr/bin/env python

from bs4 import BeautifulSoup  # parse raw html and extract elements
import requests
from requests.auth import HTTPBasicAuth
import cgi
import urllib3
import sys

##################
# DEFINITIONS
##################

def getdwsource(dwsite):

    # get the subsite of the internal wiki specified as site
    # use the dummy usre to provide access to the wiki
    dokuwiki = requests.get('https://wiki.uni-freiburg.de/igem2016/doku.php?id=%s&do=export_xhtmlbody' % dwsite,
                            auth=HTTPBasicAuth('alis', 'igem2016'))
    # extract the html of the requests-object by using beautifulsoup
    soup = BeautifulSoup(dokuwiki.text, 'html.parser')
    print('https://wiki.uni-freiburg.de/igem2016/doku.php?id=%s&do=export_xhtmlbody'%dwsite)
    return soup


def getdwpicnames(source):

    ########
    # returns a dict of the the names of all images in the source code as keys with the corresponding links to the image
    # and the info-page
    ########
    picnamesdic = {}
    for img in source.find_all('img'):
        # extract the name of all pictures from the src-string
        try:
            # get the name of the picnamesdic
            dwname = img.get('src').split('media=')[1]
            # use the name as key for a dict to store the links for src and href
            picnamesdic[dwname] = [img.get('src')]
            picnamesdic[dwname].append(img.parent.get('href'))
            print('+ \t %s ' % img.get('src').split('media=')[1])
            return picnamesdic
            # print('dwlink=%s'%picnamesdic[dwname])
        except:
            print('- \t\t %s ' % img.get('src').split('/')[-1])
            return picnamesdic


def unescape(s):
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("%3A", ":")
    # this has to be last:
    s = s.replace("&amp;", "&")
    return s


def getpicurl(picname):

    # input: The name of a file uploaded on the iGEM 2016 Wiki-Server #
    # IMPOARTNT: The picture has to be uploaded before running the script! #
    # picname=input('please paste the name of an uploaded iGEM-wiki file:\n')

    # correct picname for changes the iGEM-Server needs
    picname = picname.replace(':', '-')

    # define fix url for Wiki-Sever #
    url = 'http://2016.igem.org/File:Freiburg_%s' % picname
    print('the url I looked for was:\n%s' % url)

    # get raw_html from url as specified here:
    # http://stackoverflow.com/questions/17257912/how-to-print-raw-html-string-using-urllib3 #

    http_pool = urllib3.connection_from_url(url)
    r = http_pool.urlopen('GET', url)
    raw_html = r.data.decode('utf-8')

    # initialise bs-object '
    soup = BeautifulSoup(raw_html, 'html.parser')

    # find the href-link in an a-object in a div with id=file #
    try:
        serverlink = 'http://2016.igem.org' + soup.find(id='file').find('a').get('href')
        # return the link #
        return '%(x)s, %(y)s' % {'x': picname, 'y': serverlink}
    except:
        return None


###################
# BEGIN PROGRAMME
###################
if __name__ == "__main__":
    # ask for internal wiki site to read
    # dwsite = input('dwsite (in please in quotations):\t')
    dwsite = sys.argv[1]
    # get sourcecode
    dwsource = getdwsource(dwsite)
    # get all picture names within a href
    picnamesdic = getdwpicnames(dwsource)
    # initialize list of urls to download
    urldic = {}
    # fill the list
    for key in picnamesdic:
        if getpicurl(key) == None:
            urldic[key] = '/igem2016/lib/exe/fetch.php?media=' + key

    # download the images in the current directory (replace non usable syntax and append Freiburg_)
    for url in urldic:
        r = requests.get('http://wiki.uni-freiburg.de' + urldic[url], auth=HTTPBasicAuth('alis', 'igem2016'), stream=True)
        if r.status_code == 200:
            f = open('images/Freiburg_' + url.replace(':', '-'), 'wb')
            f.write(r.content)

        f.close()
        f = open('files.txt', 'a')
        for key in urldic.keys():
            f.write('"{}"'.format(key.replace(':', '-')))
            f.write(', ')
        f.close()

import shelve
import re
from django.utils.encoding import smart_str
# smart_str: Forces byte, int ve float typr objects to be string type.
import urllib.request as urllib2
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

# We wont count this words:
ignorewords = set(['lang','html','the', 'of', 'to', 'and', 'a', 'in', 'is', 'it', 'if'])

class crawler:    
    # Initialize the crawler with the name of database tabs
    def __init__(self, dbtables):
        ''' dbtables bir sozluk olmali:
        
            'urllist': 'urllist.db',
            'wordlocation':'wordlocation.db'}
        '''
        self.dbtables = dbtables
        self.lessoncodelist = []
    
    # Create the database tables
    def createindextables(self):
        # {url:outgoing_link_count}
        self.urllist = shelve.open(self.dbtables['urllist'], writeback=True, flag='c')
        #{word:{url:[loc1, loc2, ..., locN]}}
        self.wordlocation = shelve.open(self.dbtables['wordlocation'], writeback=True, flag='c')
    
    # Opens the database tables with 'r' flag
    def openindextables(self):
        # {url:outgoing_link_count}
        self.urllist = shelve.open(self.dbtables['urllist'], flag='r')
        #{word:{url:[loc1, loc2, ..., locN]}}
        self.wordlocation = shelve.open(self.dbtables['wordlocation'], flag='r')
        
    def close(self):
        if hasattr(self, 'urllist'): self.urllist.close()
        if hasattr(self, 'wordlocation'): self.wordlocation.close()

    # Extract the text from an HTML page (no tags)
    def gettextonly(self, soup):
        v = soup.string
        if v == None:
            c = soup.contents
            resulttext = ''
            for t in c:
                subtext = self.gettextonly(t)
                resulttext += subtext + '\n'
            return resulttext
        else:
            return v.strip()

    # Separate the words by any non-whitespace character
    def separatewords(self, text):
        splitter = re.compile('\\W+')
        return [s.lower() for s in splitter.split(text) if s != '']

    def isadded(self, lesson_code):
        if not lesson_code in self.lessoncodelist:
            return False
        else:
            return True
    
    # Index an individual page
    def addtoindex(self, url, soup):
        print ('Indexing ' + url)
        url = smart_str(url)
        # Get the individual words
        text = self.gettextonly(soup)
        words = self.separatewords(text)
        
        # Record each word found on this page
        for i in range(len(words)):
            word = smart_str(words[i])

            if word in ignorewords:
                continue

            self.wordlocation.setdefault(word, {})

            self.wordlocation[word].setdefault(url, [])
            self.wordlocation[word][url].append(i)

        return True
    
    # Starting with a list of pages, do a breadth
    # first search to the given depth, indexing pages
    # as we go
    def crawl(self, pages, depth=2):
        for i in range(depth):
            newpages = set()
            for page in pages:
                try:
                    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                           'Accept-Encoding': 'none',
                           'Accept-Language': 'en-US,en;q=0.8',
                           'Connection': 'keep-alive'}
                    req = urllib2.Request(page, headers=hdr)
                    c = urllib2.urlopen(req)
                except Exception as e:
                    print ("Could not open {}, {}".format(page, e))
                    continue
                soup = BeautifulSoup(c.read(), 'html.parser')
                self.addtoindex(page, soup)
 
                links = soup('a')
                for link in links:
                    if 'href' in link.attrs:
                        url = urljoin(page, link['href'])
                        #os.path.join()
                        if url.find("'") != -1:
                            continue
                            # The fragment identifier introduced
                            # by a hash mark (#) is the optional last
                            # part of a URL for a document. It is typically
                            # used to identify a portion of that document.
                        url = url.split('#')[0]  # remove location portion
                        link = str(link)
                        lesson_code = link.split(">")[1]
                        lesson_code = lesson_code.split("<")[0]
                        if url[0:4] == 'http' and not self.isadded(lesson_code):
                            newpages.add(url)
                            self.lessoncodelist.append(lesson_code)
                            self.urllist[smart_str(url)] = lesson_code
            pages = newpages

pagelist=['https://ois.istinye.edu.tr/bilgipaketi/eobsakts/ogrenimprogrami/program_kodu/0401001/menu_id/p_38/tip/L/submenuheader/2/ln/tr/print/1']
folder_name = os.path.join(os.getcwd(), 'materials')

dbtables = {'urllist': os.path.join(folder_name, 'urllist_ders.db'),
            'wordlocation': os.path.join(folder_name, 'wordlocation_ders.db')}


class searcher:
    def __init__(self, urls, words):
        self.urllist = urls
        self.wordlocation = words
        self.data = []

    def __del__(self):
        crawler(dbtables).close()

    def getmatchingpages(self,q):
        results = {}
        # Split the words by spaces
        words = [(smart_str(word).lower()) for word in q.split()]
        if words[0] not in self.wordlocation:
                return results, words

        url_set = set(self.wordlocation[words[0]].keys())

        for word in words[1:]:
            if word not in self.wordlocation:
                return results, words
            url_set = url_set.intersection(self.wordlocation[word].keys())

        for url in url_set:
            results[url] = []
            for word in words:
                results[url].append(self.wordlocation[word][url])

        return results, words
    
    def getscoredlist(self, results, words):
        totalscores = dict([(url, 0) for url in results])
    
        # word frequency scoring
        weights = [(0.4, self.frequencyscore(results)),
                   (0.3, self.locationscore(results)),
                   (0.3, self.worddistancescore(results))]
        

        for (weight,scores) in weights:
            for url in totalscores:
                totalscores[url] += weight*scores.get(url, 0)

        return totalscores

    def query(self,q):
        results, words = self.getmatchingpages(q)
        if len(results) == 0:
            string = 'No matching pages found!'
            return string

        scores = self.getscoredlist(results,words)
        rankedscores = sorted([(score,url) for (url,score) in scores.items()],reverse=True)
        for (score,url) in rankedscores[0:10]:
            if url == "https://ois.istinye.edu.tr/bilgipaketi/eobsakts/ogrenimprogrami/program_kodu/0401001/menu_id/p_38/tip/L/submenuheader/2/ln/tr/print/1":
                continue
            list0 = []
            list0.append(score)
            list0.append(self.urllist[url])
            self.data.append(list0)
        return self.data

    def normalizescores(self,scores,smallIsBetter=0):
        vsmall = 0.00001 # Avoid division by zero errors
        if smallIsBetter:
            minscore=min(scores.values())
            minscore=max(minscore, vsmall)
            return dict([(u,float(minscore)/max(vsmall,l)) for (u,l) \
                         in scores.items()])
        else:
            maxscore = max(scores.values())
            if maxscore == 0:
                maxscore = vsmall
            return dict([(u,float(c)/maxscore) for (u,c) in scores.items()])

    def frequencyscore(self, results):
        counts = {}
        for url in results:
            score = 1
            for wordlocations in results[url]:
                score *= len(wordlocations)
            counts[url] = score
        return self.normalizescores(counts, smallIsBetter=False) 
    
    
    def locationscore(self, results):
        locations=dict([(url, 1000000) for url in results])
        for url in results:
            score = 0
            for wordlocations in results[url]:
                score += min(wordlocations)
            locations[url] = score
        return self.normalizescores(locations, smallIsBetter=True)
    
    def worddistancescore(self, result):
        urller = result.keys()
        listoflist = result.values()
        counts = {}
        distance = 1000000
        if (len(listoflist)) < 2 or (len(urller)) < 2:
            for url in result:
                counts[url] = 1.0
            return counts

        for url in urller:
            for i in range(len(result[url])-1):
                for j in range(len(result[url][i])):
                    for k in range(len(result[url][i+1])):
                        if distance > abs(result[url][i][j]-result[url][i+1][k]):
                            distance = abs(result[url][i][j]-result[url][i+1][k])

            counts[url]=distance

        return self.normalizescores(counts, smallIsBetter=1)
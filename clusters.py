import random
import string
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from scipy.sparse import csr_matrix
import numpy as np
import re

x = re.compile("^(yaz)...")
y = re.compile(".")
stopwords = [x, y,"ve","ile","de","ki","ise","ehea","eqf","lll","btn","ffffff","2f292b","000000"]

def data_creation(database): # Turnds the words from wordlocation database into array.
    list0 = []
    for key in database.keys():
        list0.append(key)
    return list0

def clean_string(text): # Cleans the data.
    text = ''.join([word for word in text if word not in string.punctuation])
    text = text.lower()
    text = ' '.join([word for word in text.split() if word not in stopwords])
    return text

def cosine_sim_vectors(v1,v2): # Used to calculate the similarity of strings.
    v1 = np.array(v1)
    v2 = np.array(v2)
    v1 = v1.reshape(1, -1)
    v2 = v2.reshape(1, -1)
    return cosine_similarity(v1,v2)[0][0]


# https://towardsdatascience.com/calculating-string-similarity-in-python-276e18a7d33a.
def kcluster(data,distance=cosine_sim_vectors,k=4):
    cleaned = list(map(clean_string, data))
    vectorizer = CountVectorizer().fit_transform(cleaned)
    rows = vectorizer.toarray()
    rows = np.array(rows)

    # Determine the minimum and maximum values for each point
    ranges=[(min([row[i] for row in rows]),max([row[i] for row in rows]))
            for i in range(len(rows[0]))]

    # Create k randomly placed centroids
    clusters=[[random.random()*(ranges[i][1]-ranges[i][0])+ranges[i][0] 
            for i in range(len(rows[0]))] for j in range(k)]

    lastmatches=None
    for t in range(100):
        #print ('Iteration {}'.format(t))
        bestmatches=[[] for i in range(k)]

    # Find which centroid is the closest for each row
    for j in range(len(rows)):
        row=rows[j]
        bestmatch=1
        for i in range(k):
            d=distance(clusters[i],row)
            if d<distance(clusters[bestmatch],row): bestmatch=i
        bestmatches[bestmatch].append(j)

    # If the results are the same as last time, this is complete
    if bestmatches==lastmatches: return bestmatches

    lastmatches=bestmatches
    # Move the centroids to the average of their members
    for i in range(k):
        avgs=[0.0]*len(rows[0])
        if len(bestmatches[i])>0:
            for rowid in bestmatches[i]:
                for m in range(len(rows[rowid])):
                    avgs[m]+=rows[rowid][m]
            for j in range(len(avgs)):
                avgs[j]/=len(bestmatches[i])
            clusters[i]=avgs

    return bestmatches
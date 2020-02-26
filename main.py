import logging as log

import gensim.downloader as api

log.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', datefmt="%d/%m - %H:%M:%S",
                filename="main-log.txt", level=log.DEBUG)

log.info("Program started")

log.info("Loading word models...")
log.info("Loading ConceptNet NumberBatch")
cnetModel = api.load('conceptnet-numberbatch-17-06-300')
log.info("Loading Wiki")
wikiModel = api.load('glove-wiki-gigaword-300')
log.info("Loading Google News")
gnewsNews = api.load('word2vec-google-news-300')

log.info("Done")

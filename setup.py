import logging as log
import pprint as pp

import gensim.downloader as api

log.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', datefmt="%d/%m - %H:%M:%S",
                filename="setup-log.txt", level=log.DEBUG)

pp.pprint(api.info())

log.info("Program started")

log.info("Loading word models...")
log.info("Loading ConceptNet NumberBatch")
print(api.load('conceptnet-numberbatch-17-06-300', return_path=True))
log.info("Loading Wiki")
print(api.load('glove-wiki-gigaword-300', return_path=True))
log.info("Loading Google News")
print(api.load('word2vec-google-news-300', return_path=True))

log.info("Done")

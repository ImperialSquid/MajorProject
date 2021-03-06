import logging as log
import os

from gensim.models import KeyedVectors
from gensim.similarities.index import AnnoyIndexer

log.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', datefmt="%d/%m - %H:%M:%S",
                filename="logs/setup-log.txt", level=log.DEBUG)

"""
Just some code used to setup up word model files, not needed for operation but kept for posterity
"""

# pp.pprint(api.info())

log.info("Program started")

# log.info("Loading word models...")
# log.info("Loading ConceptNet NumberBatch")
# print(api.load('conceptnet-numberbatch-17-06-300', return_path=True))
# log.info("Loading Wiki 300")
# print(api.load('glove-wiki-gigaword-300', return_path=True))
# log.info("Loading Google News 300")
# print(api.load('word2vec-google-news-300', return_path=True))
# log.info("Loading Twitter 200")
# print(api.load('glove-twitter-200', return_path=True))
# log.info("Loading Wiki 100")
# print(api.load('glove-wiki-gigaword-100', return_path=True))
# log.info("Loading Twitter 100")
# print(api.load('glove-twitter-100', return_path=True))

# log.info("Loading model...")
# word_model = KeyedVectors.load_word2vec_format(
#                 r"C:\Users\benja\gensim-data\glove-wiki-gigaword-100\glove-wiki-gigaword-100.gz")
# log.info("Done")
# log.info("Saving as binary...")
# word_model.save("glove-wiki-100.bin")
# log.info("Done")
# log.info("Loading binary model")
# word_model = KeyedVectors.load(
#     r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3\CS39440\MajorProject\glove-wiki-100.bin")
# log.info("Done!")
#
# log.info("Loading model...")
# word_model = KeyedVectors.load_word2vec_format(
#                 r"C:\Users\benja\gensim-data\glove-wiki-gigaword-300\glove-wiki-gigaword-300.gz")
# log.info("Done")
# log.info("Saving as binary...")
# word_model.save("glove-wiki-300.bin")
# log.info("Done")
# log.info("Loading binary model")
# word_model = KeyedVectors.load(
#     r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3\CS39440\MajorProject\glove-wiki-300.bin")
# log.info("Done!")
#
# log.info("Loading model...")
# word_model = KeyedVectors.load_word2vec_format(
#                 r"C:\Users\benja\gensim-data\glove-twitter-100\glove-twitter-100.gz")
# log.info("Done")
# log.info("Saving as binary...")
# word_model.save("glove-twitter-100.bin")
# log.info("Done")
# log.info("Loading binary model")
# word_model = KeyedVectors.load(
#     r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3\CS39440\MajorProject\glove-twitter-100.bin")
# log.info("Done!")

# log.info("Loading model...")
# word_model = KeyedVectors.load_word2vec_format(
#                 r"C:\Users\benja\gensim-data\glove-twitter-200\glove-twitter-200.gz")
# log.info("Done")
# log.info("Saving as binary...")
# word_model.save("glove-twitter-200.bin")
# log.info("Done")
# log.info("Loading binary model")
# word_model = KeyedVectors.load(
#     r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3\CS39440\MajorProject\glove-twitter-200.bin")
# log.info("Done!")

# log.info("Loading model...")
# word_model = KeyedVectors.load_word2vec_format(
#                 r"C:\Users\benja\gensim-data\word2vec-google-news-300\word2vec-google-news-300.gz", binary=True)
# log.info("Done")
# log.info("Saving as binary...")
# word_model.save("word2vec-gnews-300.bin")
# log.info("Done")
# log.info("Loading binary model")
# word_model = KeyedVectors.load(
#     r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3\CS39440\MajorProject\word2vec-gnews-300.bin")
# log.info("Done!")

# for filename in os.listdir(r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3\CS39440\MajorProject\models"):
#     if filename[-4:] == ".bin" and filename != "word2vec-gnews-300.bin":
#         log.info("Loading {0}".format(filename))
#         wm = KeyedVectors.load(r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3" +
#                                r"\CS39440\MajorProject\models\{0}".format(filename))
#         log.info("Loaded, preprocessing L2 norms...")
#         wm.init_sims(replace=True)
#         log.info("Preprocessed, saving")
#         wm.save(filename)

for filename in os.listdir(r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3\CS39440\MajorProject\models"):
    if filename[-4:] == ".bin" and filename != "word2vec-gnews-300.bin":
        log.info("Loading {0}".format(filename))
        wm = KeyedVectors.load(r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3" +
                               r"\CS39440\MajorProject\models\{0}".format(filename))
        log.info("Building annoy indexer")
        indexer = AnnoyIndexer(wm, 5)
        log.info("Saving")
        indexer.save(r"models\{0}-5-trees.ann".format(filename.split(".")[0]))

log.info("All Done")

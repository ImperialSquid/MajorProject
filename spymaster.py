import logging as log
import pprint as pp
from random import shuffle

from gensim.models import KeyedVectors

log.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', datefmt="%d/%m - %H:%M:%S",
                filename="spymaster-log.txt", level=log.DEBUG)

log.info("##### - Program started - #####")

log.info("Loading word models...")
log.debug("Loading Google News")
wordModel = KeyedVectors.load_word2vec_format(r"C:\Users\benja\gensim-data\word2vec-google-news-300\word2vec-google-news-300.gz", binary=True, limit=500000)
log.info("Done loading models")

log.info("Loading words and settings")
log.debug("Loading words")
targetWords = [w.strip() for w in open("targets.txt", "r").readlines()]
targetWords = [w for w in targetWords if w in wordModel.vocab]
print(len(targetWords), targetWords)
log.debug("Done loading words")

log.debug("Loading settings")
teamSizes = [line.strip() for line in open("teams.txt").readlines()]
teamSizes = {t.split(":")[0]: t.split(":")[1] for t in teamSizes}
teamSizes = {k: int(teamSizes[k]) for k in teamSizes.keys()}
teamSizes["grey"] = max(0, 25-sum(teamSizes.values()))
pp.pprint(teamSizes)
log.debug("Done loading settings")
log.info("Done loading words and settings")

gameRuns = 1
log.info("Running {0} games".format(gameRuns))
for i in range(gameRuns):
    log.debug("Game {0}:".format(i))
    shuffle(targetWords)
    nameGen = iter(targetWords)
    teamNames = dict()
    for team in teamSizes.keys():
        teamNames[team] = [next(nameGen) for i in range(teamSizes[team])]
        log.debug("Team {0}: {1}".format(team, ", ".join(teamNames[team])))

    hints = dict()
    for red in teamNames["red"]:
        hints[red] = wordModel.most_similar(positive=[[red, 10]],
                                            negative=[[word, -1.0] for word in teamNames["grey"]] +
                                                     [[word, -3.0] for word in teamNames["blue"]] +
                                                     [[word, -7.0] for word in teamNames["black"]],
                                            topn=5)
    log.debug("Hints:")
    for red in teamNames["red"]:
        log.debug("{0}: {1}".format(red, "//".join([" - ".join([h[0], "{0:3.3f}".format(h[1])]) for h in hints[red]])))
    print("Hints: ")
    pp.pprint(hints)

log.info("##### - Program ended - #####")

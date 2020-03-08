import logging as log

from gensim.models import KeyedVectors


class SpyMaster:
    def __init__(self, teams_file="teams.txt", words_file="game_words.txt"):
        log.info("SpyMaster Initialised")
        self.team_sizes, self.team_weights = self.load_teams(teams_file)
        self.word_model = self.load_word_model(model_name="")
        self.game_words = self.load_game_words(words_file)

    def load_teams(self, teams_file="teams.txt"):
        log.info("Getting teams sizes and weights...")

        setts = {"size_red": 1, "size_blue": 1, "size_black": 0,
                 "weight_red": 30, "weight_grey": -1, "weight_blue": -3, "weight_black": -10}  # sets default settings
        lines = [line.strip() for line in open(teams_file).readlines()]
        splits = {line.split(":")[0]: line.split(":")[1] for line in lines}  # reads in a definitions list for settings

        for k in setts.keys():  # reassign settings if a new one was found
            try:
                setts[k] = int(splits[k])
                log.debug("Found value for {0}: {1}".format(k, setts[k]))
            except KeyError as e:
                log.warning("No value found for {0}, using default value {1}".format(k, setts[k]))

        team_sizes = {sett[5:]: setts[sett] for sett in setts.keys()
                      if sett in ["size_red", "size_blue", "size_black"]}
        team_sizes["grey"] = max(0, 25 - sum(team_sizes.values()))
        team_weights = {sett[7:]: setts[sett] for sett in setts.keys()
                        if sett in ["weight_red", "weight_grey", "weight_blue", "weight_black"]}

        log.debug("Team sizes: {0}".format(" - ".join([k + ":" + str(team_sizes[k]) for
                                                       k in sorted(team_sizes.keys())])))
        log.debug("Team weights: {0}".format(" - ".join([k + ":" + str(team_weights[k]) for
                                                       k in sorted(team_weights.keys())])))
        log.info("Done loading team sizes and weights")
        return team_sizes, team_weights

    def load_word_model(self, model_name):
        log.info("Loading word model...")

        if model_name == "word2vec-google-news-300":
            log.debug("Loading Google News 300")
            word_model = KeyedVectors.load_word2vec_format(
                r"C:\Users\benja\gensim-data\word2vec-google-news-300\word2vec-google-news-300.gz", binary=True,
                limit=500000)
        elif model_name == "glove-twitter-100":
            log.debug("Loading Twitter 100")
            word_model = KeyedVectors.load_word2vec_format(
                r"C:\Users\benja\gensim-data\glove-twitter-100\glove-twitter-100.gz", limit=500000)
        else:
            log.debug("Loading Wiki 100")
            word_model = KeyedVectors.load_word2vec_format(
                r"C:\Users\benja\gensim-data\glove-wiki-gigaword-100\glove-wiki-gigaword-100.gz", limit=500000)

        log.info("Done loading models")
        return word_model

    def load_game_words(self, words_file="game_words.txt"):
        log.info("Loading game words...")
        file_words = [w.replace(" ","_").strip() for w in open(words_file, "r").readlines()]
        try:
            game_words = [w for w in file_words if w in self.word_model.vocab]
            missing = [w for w in file_words if w not in game_words]
        except NameError:
            log.warning("No word model to filter game words by, assuming all are valid")
            game_words = file_words
            missing = []
        log.info("Done loading game words")
        log.debug("Loaded {0} words, {1} missing (missing word(s): {2})".format(len(game_words), len(missing),
                                                                                ", ".join(missing)))
        return game_words

r"""
gameRuns = 3
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
        hints[red] = wordModel.most_similar(positive=[(red, 30)],
                                            negative=[(word, -1) for word in teamNames["grey"]] +
                                                     [(word, -3) for word in teamNames["blue"]] +
                                                     [(word, -7) for word in teamNames["black"]],
                                            topn=5)
    log.debug("Hints:")
    for red in teamNames["red"]:
        log.debug("{0}: \t{1}".format(red, "\t//\t".join([" - ".join([h[0], "{0:3.3f}".format(h[1])]) for h in hints[red]])))
    print("Hints: ")
    pp.pprint(hints)

log.info("##### - Program ended - #####")

"""

if __name__ == "__main__":
    log.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', datefmt="%d/%m - %H:%M:%S",
                    filename="spymaster-log.txt", level=log.DEBUG)

    sm = SpyMaster()

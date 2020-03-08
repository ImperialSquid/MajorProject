import logging as log
from random import shuffle
from itertools import combinations
from nltk.stem import porter, lancaster, wordnet
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
        file_words = [w.replace(" ", "_").strip() for w in open(words_file, "r").readlines()]
        try:
            game_words = [w for w in file_words if w in self.word_model.vocab]
            missing = [w for w in file_words if w not in game_words]
        except AttributeError:
            log.warning("No word model to filter game words by, assuming all are valid")
            game_words = file_words
            missing = []
        log.info("Done loading game words")
        log.debug("Loaded {0} words, {1} missing (missing word(s): {2})".format(len(game_words), len(missing),
                                                                                ", ".join(missing)))
        return game_words

    def run_round(self):
        log.info("Running round")
        shuffle(self.game_words)
        word_gen = iter(self.game_words)
        team_words = {team: [next(word_gen) for words in range(self.team_sizes[team])]
                      for team in sorted(self.team_sizes.keys())}
        log.info("Team words:\n{0}".format("\n".join([team + ": " + ", ".join(team_words[team])
                                                      for team in team_words.keys()])))

    def get_hints_raw(self, team_words={}, reds=()):
        hints_raw = self.word_model.most_similar(positive=[(red, self.team_weights["red"])
                                                           for red in reds],
                                                 negative=[(grey, self.team_weights["grey"])
                                                           for grey in team_words["grey"]] +
                                                          [(blue, self.team_weights["blue"])
                                                           for blue in team_words["blue"]] +
                                                          [(black, self.team_weights["black"])
                                                           for black in team_words["black"]],
                                                 topn=50)
        hints_filtered = (raw for raw in hints_raw if self.check_legal(raw[0]))
        return hints_filtered

    def check_legal(self, hint):
        # From the Codenames rules:
        # You can't say any form of a visible word on the table
        # You can't say part of a compound word on the table

        # TODO check compound using regex (won't cause collisions normally
        #  since hint and board words will be valid words)
        # TODO check forms using nltk stemmers
        return True


if __name__ == "__main__":
    log.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', datefmt="%d/%m - %H:%M:%S",
                    filename="spymaster-log.txt", level=log.DEBUG)

    sm = SpyMaster()
    sm.run_round()

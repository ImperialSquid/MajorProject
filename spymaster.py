import logging as log
from random import shuffle
from itertools import combinations
from six import integer_types
# from nltk.stem import porter, lancaster, wordnet
from gensim.models import KeyedVectors


class SpyMaster:
    def __init__(self, teams_file="teams.txt", words_file="game_words.txt"):
        log.info("SpyMaster Initialised")
        self.team_sizes, self.team_weights = self.load_teams(teams_file)
        self.team_words = dict()  # made as an attribute to save passing back and forth while running rounds
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
            except KeyError:
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
        self.team_words = {team: [next(word_gen) for i in range(self.team_sizes[team])]
                           for team in sorted(self.team_sizes.keys())}
        log.info("Team words:\n{0}".format("\n".join([team + ": " + ", ".join(self.team_words[team])
                                                      for team in self.team_words.keys()])))

        log.info("Finding hints for overlap levels")
        max_overlap = 2
        overlaps = dict()
        for i in range(max_overlap):
            log.info("Finding hints for {0} word(s)".format(str(i + 1)))
            overlaps[i + 1] = self.get_best_hint_multi(i + 1)
            log.info("Hint overlaps found: \n{0}\n{1}".format("{0:20} {1:20} {2:20}".format("Level", "Word", "Score"),
                                                              "\n".join(["{0:20} {1:20} {2:20}".format(str(k),
                                                                                                       overlaps[k][0],
                                                                                                       overlaps[k][1])
                                                                         for k in sorted(overlaps.keys())]
                                                                        )))

    def get_best_hint_multi(self, overlap=1):
        if not isinstance(overlap, integer_types) or overlap < 1:
            log.warning("Bad word overlap passed {}, set to 1".format(str(overlap)))
            overlap = 1
        multis = []
        for multi in combinations(self.team_words["red"], overlap):
            hint = self.get_best_hint(multi)
            multis.append((multi, hint))  # multis = [ ((<target1.1>, <target1.2>, ...), hint1), ... ]
            log.debug("Words: {0} \t\t Hint: {1}".format(", ".join(multi), hint[0]))

        multis = sorted(multis, key=lambda x: x[1][1])
        return multis[0]

    def get_best_hint(self, reds):
        hints = self.get_hints(reds=reds)
        hints = sorted(hints, key=lambda x: x[1])
        return hints[0]

    def get_hints(self, reds):
        hints_raw = self.word_model.most_similar(positive=[(red, self.team_weights["red"])
                                                           for red in reds],
                                                 negative=[(grey, self.team_weights["grey"])
                                                           for grey in self.team_words["grey"]] +
                                                          [(blue, self.team_weights["blue"])
                                                           for blue in self.team_words["blue"]] +
                                                          [(black, self.team_weights["black"])
                                                           for black in self.team_words["black"]],
                                                 topn=20)
        hints_filtered = [raw for raw in hints_raw if self.check_legal(raw[0])]
        log.debug("Found {0} legal hints (of {1} searched) for {2}: (3)".format(len(hints_filtered), len(hints_raw),
                                                                                ", ".join(reds),
                                                                                " // ".join(
                                                                                    ["{0}:{1:.5f}".format(h[0],
                                                                                                          h[1])
                                                                                     for h in hints_filtered])))
        return hints_filtered

    def check_legal(self, hint):
        # From the Codenames rules:
        # You can't say any form of a visible word on the table
        # You can't say part of a compound word on the table
        # TODO check compound using regex (won't cause collisions normally
        #  since hint and board words will be valid words)
        # TODO check forms using nltk stemmers? lemmatizers?
        return True


if __name__ == "__main__":
    log.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', datefmt="%d/%m - %H:%M:%S",
                    filename="spymaster-log.txt", level=log.DEBUG)

    sm = SpyMaster()
    sm.run_round()

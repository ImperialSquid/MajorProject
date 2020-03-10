import logging as log  # logging spymaster
from itertools import combinations, chain, cycle
from math import sqrt  # adjust search weighting as search scope increases
from random import shuffle

import enchant  # load american english language
import regex as re
import spacy  # lemmatisation
from gensim.models import KeyedVectors  # lading pre-trained word vectors
from nltk.stem.lancaster import LancasterStemmer  # stemming
from six import integer_types


class SpyMaster:
    def __init__(self, teams_file="team_weights.txt", words_file="game_words.txt"):
        log.info("SpyMaster initialising...")
        # spymaster stuff
        self.settings = self.__load_settings(sett_file="spymaster_settings.txt",
                                             default_dict={"top_hints_per_word": 3,
                                                           "max_levels": 3})

        # game stuff (what game words are available depends on the word model used so it is loaded in load_model)
        self.game_words = list()

        # teams stuff
        self.team_weights = self.__load_settings(sett_file="team_weights.txt",
                                                 default_dict={"red": 30, "grey": -1,
                                                               "blue": -3, "black": -10})
        self.team_words = dict()  # made as an attribute to save passing back and forth while running rounds

        # nlp stuff
        self.word_model = self.load_word_model(model_name="")  # keyed vector model for generating hints
        self.ls = LancasterStemmer()  # stemmer for checking hint legality
        self.spacy_nlp = spacy.load("en_core_web_sm")  # lemmatiser for checking hint legality

        log.info("SpyMaster initialised!")

    def __load_settings(self, sett_file: str, default_dict: dict):
        # loads settings in the form of <setting name>:<value> from file (only loads numeric values)
        log.info("Loading settings for {0} from {1}... ".format(", ".join(default_dict.keys()), sett_file))
        lines = [line.strip() for line in open(sett_file).readlines()]
        splits = {line.split(":")[0]: line.split(":")[1] for line in lines}  # reads in a definitions list for settings

        for k in default_dict.keys():  # reassign settings if a new one was found
            try:
                default_dict[k] = int(splits[k])
                log.debug("Found value for {0}: {1}".format(k, default_dict[k]))
            except KeyError:
                log.warning("No value found for {0}, using default value {1}".format(k, default_dict[k]))

        log.info("Done loading settings from {0}".format(sett_file))
        return default_dict

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
        self.__load_game_words(word_model)
        return word_model

    def __load_game_words(self, word_model, words_file="game_words.txt"):
        log.info("Loading game words...")
        file_words = [w.replace(" ", "_").strip() for w in open(words_file, "r").readlines()]
        try:
            game_words = [w for w in file_words if w in word_model.vocab]
            missing = [w for w in file_words if w not in game_words]
        except AttributeError:
            log.warning("No word model to filter game words by, assuming all are valid")
            game_words = file_words
            missing = []
        log.info("Done loading game words")
        self.game_words = game_words
        log.debug("Loaded {0} words, {1} missing (missing word(s): {2})".format(len(self.game_words), len(missing),
                                                                                ", ".join(missing)))

    def run_random_round(self):
        log.info("Running round with random teams...")
        log.debug("Shuffling words")
        shuffle(self.game_words)
        word_gen = cycle(self.game_words)

        log.debug("Loading team sizes...")
        team_sizes = self.__load_settings(sett_file="team_sizes.txt",
                                          default_dict={"red": 8, "blue": 8, "black": 1, "grey": 8})
        log.debug("Team sizes: {0}".format(" - ".join([k + ":" + str(team_sizes[k]) for
                                                       k in sorted(team_sizes.keys())])))

        log.debug("Generating team words...")
        self.team_words = {team: [next(word_gen) for i in range(team_sizes[team])]
                           for team in sorted(team_sizes.keys())}
        log.info("Team words:\n{0}".format("\n".join([team + ": " + ", ".join(self.team_words[team])
                                                      for team in self.team_words.keys()])))

        self.__run_round()

    def run_defined_round(self, reds: list, blues: list, greys: list, blacks: list):
        log.info("Running round with predefined teams...")
        self.team_words["red"] = reds
        self.team_words["blue"] = blues
        self.team_words["grey"] = greys
        self.team_words["black"] = blacks
        log.info("Team words:\n{0}".format("\n".join([team + ": " + ", ".join(self.team_words[team])
                                                      for team in self.team_words.keys()])))
        self.__run_round()

    def __run_round(self):
        log.info("Running round")

        log.info("Finding hints for overlap levels")
        max_overlap = 2
        overlaps = dict()
        for i in range(max_overlap):
            log.info("Finding hints for {0} word(s)".format(str(i + 1)))
            overlaps[i + 1] = self.__get_top_hints_multi(i + 1)
        log.info("Hint overlaps found: \n{0}\n{1}".format(
            "{0:20} {1:30} {2:20} {3:20}".format("Level", "Word", "Hint", "Score"),
            "\n".join(["{0:20} {1:30} {2:20} {3:20.5f}".format(str(k),
                                                               ", ".join(overlaps[k][0]),
                                                               overlaps[k][1][0],
                                                               overlaps[k][1][1])
                       for k in sorted(overlaps.keys())]
                      )))

    def __get_top_hints_multi(self, overlap=1):
        if not isinstance(overlap, integer_types) or overlap < 1:
            log.warning("Bad word overlap passed {}, set to 1".format(str(overlap)))
            overlap = 1
        multis = []
        for multi in combinations(self.team_words["red"], overlap):
            hint = self.__get_top_hints(multi)
            multis.append((multi, hint))  # multis = [ ((<target1.1>, <target1.2>, ...), hint1), ... ]
            log.debug("Words: {0} \t\t Hint: {1} \t\t Score: {2}".format(", ".join(multi), hint[0], hint[1]))

        multis = sorted(multis, key=lambda x: x[1][1], reverse=True)
        return multis[0]

    def __get_top_hints(self, reds):
        hints = self.__get_hints(reds=reds)
        hints = sorted(hints, key=lambda x: x[1], reverse=True)
        return hints[0]

    def __get_hints(self, reds):
        hints_raw = self.word_model.most_similar(positive=[(red, int(self.team_weights["red"] / sqrt(len(reds))))
                                                           for red in reds],
                                                 negative=[(grey, self.team_weights["grey"])
                                                           for grey in self.team_words["grey"]] +
                                                          [(blue, self.team_weights["blue"])
                                                           for blue in self.team_words["blue"]] +
                                                          [(black, self.team_weights["black"])
                                                           for black in self.team_words["black"]],
                                                 topn=50)
        hints_filtered = [raw for raw in hints_raw if self.__check_legal(raw[0])]
        log.debug("Found {0} legal hints (of {1} searched) for {2}: {3}".format(len(hints_filtered), len(hints_raw),
                                                                                ", ".join(reds),
                                                                                " // ".join(
                                                                                    ["{0}:{1:.5f}".format(h[0], h[1])
                                                                                     for h in hints_filtered])))
        return hints_filtered

    def __check_legal(self, hint):
        board_words = [x for x in chain.from_iterable(self.team_words.values())]

        doc = self.spacy_nlp(" ".join([word for word in board_words]))
        hint_lemma_stem = self.ls.stem([token.lemma_ for token in self.spacy_nlp(hint)][0])
        matches = [hint_lemma_stem == self.ls.stem(token.lemma_) for token in doc]
        # list of Trues and Falses
        # True = illegal due to same root

        matches = matches + [re.match(".*{}.*".format(hint), bw) for bw in board_words]
        # True = board word contained within hint

        matches = matches + [re.match(".*{}.*".format(bw), hint) for bw in board_words]
        # True = hint contained within board word

        d = enchant.Dict("en_US")
        matches.append(not d.check(hint))
        # True = word not in US dictionary (Us not UK due to word model using Us dict)

        return not any(matches)  # If and Trues exist the hint is not legal


if __name__ == "__main__":
    log.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', datefmt="%d/%m - %H:%M:%S",
                    filename="spymaster-log.txt", level=log.DEBUG)
    sm = SpyMaster()
    sm.run_random_round()
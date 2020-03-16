import logging as log  # logging spymaster
from itertools import combinations, chain, cycle
from math import sqrt  # adjust search weighting as search scope increases
from random import shuffle

import enchant  # load american english language
import regex as re
import spacy  # lemmatisation
from gensim.models import KeyedVectors  # lading pre-trained word vectors
from nltk.stem.lancaster import LancasterStemmer  # stemming


class SpyMaster:
    def __init__(self, teams_file="team_weights.txt", words_file="game_words.txt"):
        log.info("SpyMaster initialising...")
        # spymaster stuff
        self.settings = self.__load_settings(sett_file="settings.txt",
                                             default_dict={"max_top_hints": 10,
                                                           "max_levels": 2})

        # game stuff (what game words are available depends on the word model used so it is loaded in load_model)
        self.game_words = list()

        # teams stuff
        self.team_weights = self.__load_settings(sett_file=teams_file,
                                                 default_dict={"red": 30, "grey": -1,
                                                               "blue": -3, "black": -10})
        self.team_words = dict()  # made as an attribute to save passing back and forth while running rounds

        # nlp stuff
        self.word_model = self.load_word_model(model_name="",
                                               game_words_file=words_file)  # keyed vector model for generating hints
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

    def load_word_model(self, model_name, game_words_file="game_words.txt"):
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
        self.__load_game_words(word_model, words_file=game_words_file)
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

    def run_random_round(self, out_file=None):
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

        self.__run_round(out_file=out_file)

    def run_defined_round(self, reds: list, blues: list, greys: list, blacks: list, out_file=None):
        log.info("Running round with predefined teams...")
        self.team_words["red"] = [red for red in reds if red in self.word_model.vocab]
        self.team_words["blue"] = [blue for blue in blues if blue in self.word_model.vocab]
        self.team_words["grey"] = [grey for grey in greys if grey in self.word_model.vocab]
        self.team_words["black"] = [black for black in blacks if black in self.word_model.vocab]
        log.info("Team words:\n{0}".format("\n".join([team + ": " + ", ".join(self.team_words[team])
                                                      for team in self.team_words.keys()])))
        self.__run_round(out_file=out_file)

    def __run_round(self, out_file=None):
        log.info("Running round")

        log.info("Finding hints for overlap levels")
        overlaps = dict()
        for i in range(self.settings["max_levels"]):
            log.info("Finding hints for {0} word(s)".format(str(i + 1)))
            overlaps[i + 1] = self.__get_top_hints_multi(i + 1)

        log.info("Results:")
        log.info("{0:7} | {1:30} | {2:15} | {3:10}".format("Level", "Words", "Hint", "Score"))
        for level in sorted(overlaps.keys()):
            log.info("{0:^7} | {1:^30} | {2:^15} | {3:^10}".format("-", "--", "-", "--"))
            for hint in overlaps[level]:
                log.info("{0:7} | {1:30} | {2:15} | {3:10}".format(level, ",".join(hint[0]), hint[1][0], hint[1][1]))

        if out_file is not None:
            log.info("Output file detected, writing hints")
            with open(out_file, "w") as outf:
                outf.write("Teams:\n")
                for team in sorted(self.team_words.keys()):
                    outf.write("{0}: {1}\n".format(team, " - ".join(self.team_words[team])))
                outf.write("Hints:\n")
                for level in sorted(overlaps.keys()):
                    outf.write("Level: {0}\n".format(str(level)))
                    outf.write("{0:40}{1:20}{2:20}\n".format("Target", "Hint", "Score"))
                    for hint in overlaps[level]:
                        outf.write("{0:40}{1:20}{2:20}\n".format(",".join(hint[0]), hint[1][0], hint[1][1]))
            log.info("Done")
            return None
        else:
            log.info("No out file given")
            return overlaps

    def __get_top_hints_multi(self, overlap=1):
        multis = []
        for multi in combinations(self.team_words["red"], overlap):
            hints = self.__get_hints(multi)
            for hint in hints:
                multis.append((multi, hint))
                # multis = [ [[target1, ...], [hint1, score1]]
                #            [[target1, ...], [hint2, score2]]
                #            [[target2, ...], [hint3, score3]]
                #            [[target2, ...], [hint4, score4]]
                #            ... ] Allows hints to be sorted on individual strength
            log.debug("Words: {0:20} Hints: {1}".format("|".join(multi), " // ".join(["{0}-{1}".format(hint[0], hint[1])
                                                                                      for hint in hints])))

        multis = sorted(multis, key=lambda x: x[1][1], reverse=True)
        return multis[0:self.settings["max_top_hints"] if self.settings["max_top_hints"] > 0 else None]

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
        if len(hints_filtered) == 0:
            hints_filtered = [["NO HINT FOUND", -1]]
            log.debug("Illegal Hints (since all were illegal): {0}".format(" // ".join(["{0}:{1:.5f}".format(h[0], h[1])
                                                                                        for h in hints_raw])))
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

        matches.append(re.match(r".*\-.*", hint))
        # True = word contains - implying two words concatenated in text but separate in speech

        return not any(matches)  # If and Trues exist the hint is not legal


if __name__ == "__main__":
    root_logger = log.getLogger()
    root_logger.setLevel(log.DEBUG)
    handler = log.FileHandler("spymaster-log.txt", "a", "utf-8")
    handler.setFormatter(log.Formatter("%(asctime)s : %(levelname)s : %(message)s", datefmt="%d/%m - %H:%M:%S"))
    root_logger.addHandler(handler)

    sm = SpyMaster()
    sm.run_random_round(out_file="hint-results.txt")

import logging as log  # logging spymaster
from itertools import combinations, chain, cycle
from math import sqrt  # adjust search weighting as search scope increases
from random import shuffle

import enchant  # load american english language
import regex as re
import spacy  # lemmatisation
from gensim.models import KeyedVectors  # lading pre-trained word vectors
from gensim.similarities.index import AnnoyIndexer
from nltk.stem.lancaster import LancasterStemmer  # stemming

from utils import load_settings


class SpyMaster:
    def __init__(self, teams_file="settings/team_weights.txt", words_file="settings/game_words.txt",
                 full_log=None, game_log=None):
        self.full_log = full_log
        self.game_log = game_log
        if self.full_log is not None:
            self.full_log.info("SpyMaster initialising...")
        if self.game_log is not None:
            self.game_log.info("SpyMaster initialising...")
        # spymaster stuff
        self.settings = load_settings(sett_file="settings/spymaster_setts.txt",
                                      default_dict={"max_top_hints": 10, "max_levels": 2,
                                                    "use_annoy_indexer": True, "model_name": "glove-wiki-100",
                                                    "vocab_limit": 0})

        # game stuff (what game words are available depends on the word model used so it is loaded in load_model)
        self.game_words = list()

        # teams stuff
        self.team_weights = load_settings(sett_file=teams_file,
                                          default_dict={"t": 30, "b": -1, "o": -3, "k": -10})
        self.team_words = dict()  # made as an attribute to save passing back and forth while running rounds

        # nlp stuff
        self.word_model = self.load_word_model(model_name=self.settings["model_name"],
                                               game_words_file=words_file)  # keyed vector model for generating hints

        self.indexer = self.load_indexer(model_name=self.settings["model_name"])

        self.ls = LancasterStemmer()  # stemmer for checking hint legality
        self.spacy_nlp = spacy.load("en_core_web_sm")  # lemmatiser for checking hint legality

        if self.full_log is not None:
            self.full_log.info("SpyMaster initialised!")
        if self.game_log is not None:
            self.game_log.info("SpyMaster initialised!")

    def load_word_model(self, model_name, game_words_file="settings/game_words.txt"):
        if self.full_log is not None:
            self.full_log.info("Loading word model...")

        if model_name == "word2vec-gnews-300":
            if self.full_log is not None:
                self.full_log.debug("Loading Google News 300")
            word_model = KeyedVectors.load(r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3\CS39440"
                                           r"\MajorProject\models\word2vec-gnews-300.bin")
        elif model_name == "glove-twitter-100":
            if self.full_log is not None:
                self.full_log.debug("Loading Twitter 100")
            word_model = KeyedVectors.load(r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3\CS39440"
                                           r"\MajorProject\models\glove-twitter-100.bin")
        elif model_name == "glove-twitter-200":
            if self.full_log is not None:
                self.full_log.debug("Loading Twitter 200")
            word_model = KeyedVectors.load(r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3\CS39440"
                                           r"\MajorProject\models\glove-twitter-200.bin")
        elif model_name == "glove-wiki-300":
            if self.full_log is not None:
                self.full_log.debug("Loading Wiki 300")
            word_model = KeyedVectors.load(r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3\CS39440"
                                           r"\MajorProject\models\glove-wiki-300.bin")
        else:
            if self.full_log is not None:
                self.full_log.debug("Loading Wiki 100")
            word_model = KeyedVectors.load(r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3\CS39440"
                                           r"\MajorProject\models\glove-wiki-100.bin")

        if self.full_log is not None:
            self.full_log.info("Done loading models")
        self.__load_game_words(word_model, words_file=game_words_file)
        return word_model

    def load_indexer(self, model_name):
        if self.full_log is not None:
            self.full_log.info("Loading word model indexer...")

        indexer = None

        if self.settings["use_annoy_indexer"]:
            if model_name == "glove-twitter-100":
                if self.full_log is not None:
                    self.full_log.debug("Loading Twitter 100")
                indexer = AnnoyIndexer()
                indexer.load(r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3\CS39440" +
                             r"\MajorProject\models\glove-twitter-100-5-trees.ann")
            elif model_name == "glove-twitter-200":
                if self.full_log is not None:
                    self.full_log.debug("Loading Twitter 200")
                indexer = AnnoyIndexer()
                indexer.load(r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3\CS39440" +
                             r"\MajorProject\models\glove-twitter-200-5-trees.ann")
            elif model_name == "glove-wiki-300":
                if self.full_log is not None:
                    self.full_log.debug("Loading Wiki 300")
                indexer = AnnoyIndexer()
                indexer.load(r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3\CS39440" +
                             r"\MajorProject\models\glove-wiki-300-5-trees.ann")
            elif model_name == "glove-wiki-100":
                if self.full_log is not None:
                    self.full_log.debug("Loading Wiki 100")
                indexer = AnnoyIndexer()
                indexer.load(r"C:\Users\benja\OneDrive\Documents\UniWork\Aberystwyth\Year3\CS39440" +
                             r"\MajorProject\models\glove-wiki-100-5-trees.ann")
            if self.full_log is not None:
                self.full_log.info("Done loading model indexer")
        else:
            if self.full_log is not None:
                self.full_log.warning("No indexer selected, using default")

        return indexer

    def __load_game_words(self, word_model, words_file="settings/game_words.txt"):
        if self.full_log is not None:
            self.full_log.info("Loading game words...")
        file_words = [w.replace(" ", "_").strip() for w in open(words_file, "r").readlines()]
        try:
            game_words = [w for w in file_words if w in word_model.vocab]
            missing = [w for w in file_words if w not in game_words]
        except AttributeError:
            log.warning("No word model to filter game words by, assuming all are valid")
            game_words = file_words
            missing = []

        if self.full_log is not None:
            self.full_log.info("Done loading game words")

        self.game_words = game_words

        if self.full_log is not None:
            self.full_log.debug("Loaded {0} words, {1} missing (missing word(s): {2})".format(len(self.game_words),
                                                                                              len(missing),
                                                                                              ", ".join(missing)))
        if self.game_log is not None:
            self.game_log.info("Loaded {0} words, {1} missing)".format(len(self.game_words), len(missing)))
            self.game_log.info("Loaded words: {0}".format(", ".join(missing)))

    def run_random_round(self, out_file=None):
        if self.full_log is not None:
            self.full_log.info("Running round with random teams...")
            self.full_log.debug("Shuffling words")
        if self.game_log is not None:
            self.game_log.info("Running round with random teams...")

        shuffle(self.game_words)
        word_gen = cycle(self.game_words)

        if self.full_log is not None:
            self.full_log.debug("Loading team sizes...")
        team_sizes = load_settings(sett_file="settings/team_sizes.txt",
                                   default_dict={"t": 8, "o": 8, "k": 1, "b": 8})
        if self.full_log is not None:
            self.full_log.debug("Team sizes: {0}".format(" - ".join([k + ":" + str(team_sizes[k]) for
                                                                     k in ["t", "o", "b", "k"]])))

        if self.full_log is not None:
            self.full_log.debug("Generating team words...")
        self.team_words = {team: [next(word_gen) for i in range(team_sizes[team])] for team in ["t", "o", "b", "k"]}
        if self.full_log is not None:
            self.full_log.info("Team words:\n{0}".format("\n".join([team + ": " + ", ".join(self.team_words[team])
                                                                    for team in ["t", "o", "b", "k"]])))
        if self.game_log is not None:
            self.game_log.info("Randomly generated teams are:\n{0}".format("\n".join([team + ": " +
                                                                                      ", ".join(self.team_words[team])
                                                                                      for team in
                                                                                      ["t", "o", "b", "k"]])))

        return self.__run_round(out_file=out_file)

    def run_defined_round(self, ts: list, os: list, bs: list, ks: list, out_file=None):
        if self.full_log is not None:
            self.full_log.info("Running round with predefined teams...")
        if self.game_log is not None:
            self.game_log.info("Running round with predefined teams...")
        self.team_words["t"] = [t for t in ts if t in self.word_model.vocab]
        self.team_words["o"] = [o for o in os if o in self.word_model.vocab]
        self.team_words["b"] = [b for b in bs if b in self.word_model.vocab]
        self.team_words["k"] = [k for k in ks if k in self.word_model.vocab]
        if self.full_log is not None:
            self.full_log.info("Team words:\n{0}".format("\n".join([team + ": " + ", ".join(self.team_words[team])
                                                                    for team in ["t", "o", "b", "k"]])))
        if self.game_log is not None:
            self.game_log.info("Given teams are:\n{0}".format("\n".join([team + ": " + ", ".join(self.team_words[team])
                                                                         for team in ["t", "o", "b", "k"]])))
        return self.__run_round(out_file=out_file)

    def __run_round(self, out_file=None):
        if self.full_log is not None:
            self.full_log.info("Running round")

        if self.full_log is not None:
            self.full_log.info("Finding hints for overlap levels")
        overlaps = dict()
        for i in range(self.settings["max_levels"]):
            if self.full_log is not None:
                self.full_log.info("Finding hints for {0} word(s)".format(str(i + 1)))
            overlaps[i + 1] = self.__get_top_hints_multi(i + 1)

        if self.full_log is not None:
            self.full_log.info("Finished making hints")
            self.full_log.debug("Results:")
            self.full_log.debug("{0:7} | {1:30} | {2:15} | {3:10}".format("Level", "Words", "Hint", "Score"))
            for level in sorted(overlaps.keys()):
                self.full_log.debug("{0:^7} | {1:^30} | {2:^15} | {3:^10}".format("-", "--", "-", "--"))
                for hint in overlaps[level]:
                    self.full_log.debug("{0:7} | {1:30} | {2:15} | {3:10}".format(level, ",".join(hint[0]),
                                                                                  hint[1][0], hint[1][1]))

        if self.game_log is not None:
            self.game_log.info("Finished making hints")
            self.game_log.info("Candidate hints are:")
            self.game_log.info("{0:10}|{1:30}|{2:10}".format("Hint", "Target", "Score"))
            for hint in chain.from_iterable([overlaps[level] for level in overlaps.keys()]):
                self.game_log.info("{0:10}|{1:30}|{2:10}".format(hint[1][0], ", ".join(hint[0]), hint[1][1]))

        if out_file is not None:
            if self.full_log is not None:
                self.full_log.info("Output file detected, writing hints")
            with open(out_file, "w") as outf:
                outf.write("Teams:\n")
                for team in ["t", "o", "b", "k"]:
                    outf.write("{0}: {1}\n".format(team, " - ".join(self.team_words[team])))
                outf.write("Hints:\n")
                for level in sorted(overlaps.keys()):
                    outf.write("Level: {0}\n".format(str(level)))
                    outf.write("{0:40}{1:20}{2:20}\n".format("Target", "Hint", "Score"))
                    for hint in overlaps[level]:
                        outf.write("{0:40}{1:20}{2:20}\n".format(",".join(hint[0]), hint[1][0], hint[1][1]))
            if self.full_log is not None:
                self.full_log.info("Done")
            return None
        else:
            if self.full_log is not None:
                self.full_log.info("No out file given")
            return overlaps

    def __get_top_hints_multi(self, overlap=1):
        multis = []
        for multi in combinations(self.team_words["t"], overlap):
            hints = self.__get_hints(multi)
            for hint in hints:
                multis.append((multi, hint))
                # multis = [ [[target1, ...], [hint1, score1]]
                #            [[target1, ...], [hint2, score2]]
                #            [[target2, ...], [hint3, score3]]
                #            [[target2, ...], [hint4, score4]]
                #            ... ] Allows hints to be sorted on individual strength
            if self.full_log is not None:
                self.full_log.debug("Words: {0:20} Hints: {1}".format("|".join(multi),
                                                                      " // ".join(["{0}-{1}".format(hint[0], hint[1])
                                                                                   for hint in hints])))

        multis = sorted(multis, key=lambda x: x[1][1], reverse=True)
        return multis[0:self.settings["max_top_hints"] if self.settings["max_top_hints"] > 0 else None]

    def __get_hints(self, ts):
        hints_raw = self.word_model.most_similar(positive=[(t, self.team_weights["t"] / sqrt(len(ts)))
                                                           for t in ts],
                                                 negative=[(b, self.team_weights["b"])
                                                           for b in self.team_words["b"]] +
                                                          [(o, self.team_weights["o"])
                                                           for o in self.team_words["o"]] +
                                                          [(k, self.team_weights["k"])
                                                           for k in self.team_words["k"]],
                                                 topn=50, indexer=self.indexer,
                                                 restrict_vocab=self.settings["vocab_limit"] if
                                                 self.settings["vocab_limit"] != 0 else None)
        hints_filtered = [raw for raw in hints_raw if self.__check_legal(raw[0])]
        if self.full_log is not None:
            self.full_log.debug("Found {0} legal hints (of {1} searched) for {2}: {3}".format(
                len(hints_filtered), len(hints_raw), ", ".join(ts),
                " // ".join(["{0}:{1:.5f}".format(h[0], h[1]) for h in hints_filtered])))
        if len(hints_filtered) == 0:
            hints_filtered = [["NO HINT FOUND", -1]]
            if self.full_log is not None:
                self.full_log.debug("Illegal Hints (since all were illegal): {0}".format(
                    " // ".join(["{0}:{1:.5f}".format(h[0], h[1]) for h in hints_raw])))
        return hints_filtered

    def __check_legal(self, hint):
        board_words = [x for x in chain.from_iterable(self.team_words.values())]

        board_lemma_stems = [self.ls.stem(token.lemma_) for token in
                             self.spacy_nlp(" ".join([word for word in board_words]))]
        hint_lemma_stem = self.ls.stem([token.lemma_ for token in self.spacy_nlp(hint)][0])
        matches = [hint_lemma_stem == bls for bls in board_lemma_stems]
        # list of Trues and Falses
        # True = illegal due to same root

        matches = matches + [re.match(re.escape(".*{}.*".format(hint)), bw) for bw in board_words]
        # True = board word contained within hint

        matches = matches + [re.match(re.escape(".*{}.*".format(bw)), hint) for bw in board_words]
        # True = hint contained within board word

        d = enchant.Dict("en_US")
        matches.append(not d.check(hint))
        # True = word not in US dictionary (US not UK due to word model using US dict)

        matches.append(re.match(r"[^a-z]", hint))
        # True = word contains non-alphabetic chars

        return not any(matches)  # If any Trues exist the hint is not legal

    def check_legality(self, team_words, hint_word: str) -> bool:
        if self.full_log is not None:
            self.full_log.info("Checking legality of external hint {0}".format(hint_word))
        if self.game_log is not None:
            self.game_log.info("Checking legality of hint {0}".format(hint_word))

        for team in ["t", "o", "b", "k"]:
            if self.full_log is not None:
                self.full_log.info("Team {0} - {1}".format(team, ", ".join(team_words[team])))
            if self.game_log is not None:
                self.game_log.info("Team {0} - {1}".format(team, ", ".join(team_words[team])))
            self.team_words[team] = team_words.get(team, [])

        return self.__check_legal(hint=hint_word)


if __name__ == "__main__":
    sm_full_logger = log.getLogger("spymaster-full")
    sm_full_logger.setLevel(log.DEBUG)
    sm_full_logger.propagate = False
    handler = log.FileHandler("logs/spymaster-log.txt", "a", "utf-8")
    handler.setFormatter(log.Formatter("%(asctime)s : %(levelname)s : %(message)s", datefmt="%d/%m - %H:%M:%S"))
    sm_full_logger.addHandler(handler)

    sm = SpyMaster(full_log=sm_full_logger)
    print(sm.run_random_round(out_file=None))

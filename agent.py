import logging as log
from itertools import chain
from time import sleep

import requests as req


class Agent:
    def __init__(self):
        log.info("Agent initialising...")
        self.team_words = dict()
        self.board_words = list()
        self.hints = dict()
        self.settings = self.__load_settings(sett_file="settings.txt",
                                             default_dict={"max_top_hints": 10,
                                                           "max_levels": 2})
        self.evaluation_methods = [self.__word_net_eval]
        log.info("Agent initialised!")

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

    def load_results(self, infile):
        log.info("Loading hints from {0}...".format(infile))
        with open(infile, "r") as inf:
            inf.readline()
            for t_index in range(4):
                line = inf.readline()
                team = line.split(": ")[0]
                words = line.split(": ")[1].strip().split(" - ")
                self.team_words[team] = words
                self.board_words = [x for x in chain.from_iterable(self.team_words.values())]
            log.info("Loaded teams")
            for team in sorted(self.team_words.keys()):
                log.debug("{0}: {1}".format(team, " - ".join(self.team_words[team])))
            inf.readline()
            for l_index in range(self.settings["max_levels"]):
                level = int(inf.readline().split(": ")[1])
                inf.readline()
                hints = []
                for h in range(self.settings["max_top_hints"]):
                    line = inf.readline()
                    targets = line[:40].strip().split(",")
                    hint = line[40:60].strip()
                    score = float(line[60:].strip())
                    hints.append((targets, (hint, score)))
                self.hints[level] = hints
            log.info("Loaded hints")
            for level in sorted(self.hints.keys()):
                log.debug("Level: {0}".format(str(level)))
                log.debug("{0:40}{1:20}{2:20}".format("Target", "Hint", "Score"))
                for hint in self.hints[level]:
                    log.debug("{0:40}{1:20}{2:20}".format(",".join(hint[0]), hint[1][0], hint[1][1]))

    def evaluate_hints(self, out_file):
        log.info("Evaluating hints")
        with open(out_file, "w") as outf:
            outf.write("Teams:\n")
            for team in sorted(self.team_words.keys()):
                outf.write("{0}: {1}\n".format(team, " - ".join(self.team_words[team])))
            outf.write("Hint Evaluation:\n")
            for level in self.hints.keys():
                log.info("Level {0} hints".format(level))
                outf.write("Level: {0}\n".format(level))
                for num, hint in enumerate(self.hints[level][:1]):
                    log.info("Evaluating hint {0} of {1}: {2}".format(num + 1, len(self.hints[level]), hint[1][0]))
                    outf.write("Target: {0:30} Hint: {1:20} WM Score: {2:20f}\n".format(",".join(hint[0]),
                                                                                        hint[1][0], hint[1][1]))

                    for method in self.evaluation_methods:
                        log.info("Evaluating with method: {0}".format(method.__name__))
                        scored_board_words = [[word, method(hint=hint[1][0], target=word)]
                                              for word in self.board_words]
                        sorted_board_words = sorted(scored_board_words,
                                                    key=lambda x: x[1],
                                                    reverse=True)
                        score_str = " - ".join(
                            ["{0}-{1}".format(word[0], word[1]) for word in sorted_board_words])
                        outf.write("Ranked by {0}: {1}\n".format(method.__name__, score_str))

    def __word_net_eval(self, hint: str, target: str):
        relatedness_url = "http://api.conceptnet.io/relatedness?node1=/c/en/{}&node2=/c/en/{}"
        json = req.get(relatedness_url.format(hint, target)).json()
        sleep(2)
        return json["value"]


if __name__ == "__main__":
    root_logger = log.getLogger()
    root_logger.setLevel(log.DEBUG)
    handler = log.FileHandler("agent-log.txt", "a", "utf-8")
    handler.setFormatter(log.Formatter("%(asctime)s : %(levelname)s : %(message)s", datefmt="%d/%m - %H:%M:%S"))
    root_logger.addHandler(handler)

    log.getLogger("urllib3").setLevel(log.WARNING)  # prevent log from filling with http info

    ag = Agent()
    ag.load_results("results.txt")
    ag.evaluate_hints("evaluation.txt")

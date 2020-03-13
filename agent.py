import logging as log
from pprint import pprint


class Agent:
    def __init__(self):
        log.info("Agent initialising...")
        self.team_words = dict()
        self.hints = dict()
        self.settings = self.__load_settings(sett_file="settings.txt",
                                             default_dict={"max_top_hints": 10,
                                                           "max_levels": 2})
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
        with open(infile, "r") as inf:
            inf.readline()
            for t_index in range(4):
                line = inf.readline()
                team = line.split(": ")[0]
                words = line.split(": ")[1].strip().split(" - ")
                self.team_words[team] = words
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

    def evaluate_hints(self):
        # TODO some methods for hint eval
        pass


if __name__ == "__main__":
    root_logger = log.getLogger()
    root_logger.setLevel(log.DEBUG)
    handler = log.FileHandler("agent-log.txt", "w", "utf-8")
    handler.setFormatter(log.Formatter("%(asctime)s : %(levelname)s : %(message)s", datefmt="%d/%m - %H:%M:%S"))
    root_logger.addHandler(handler)

    ag = Agent()
    ag.load_results("results.txt")
    print(ag.team_words)
    pprint(ag.hints)

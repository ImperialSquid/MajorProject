import logging as log
from distutils.util import strtobool


def load_settings(sett_file: str, default_dict: dict):
    # loads settings in the form of <setting name>:<type>:<value> from file
    # type is any one of str, int, bool
    # all types other than these will be interpreted as str
    log.info("Loading settings for {0} from {1}... ".format(", ".join(default_dict.keys()), sett_file))
    lines = [line.strip() for line in open(sett_file).readlines()]
    splits = [line.split(":") for line in lines]  # reads in a definitions list for settings
    settings = [key for key in default_dict.keys()]

    for split in splits:
        if split[0] in settings:
            log.info("Found setting for {0}: {2} of type {1}".format(*split))
            settings.remove(split[0])
            if split[1] == "int":
                default_dict[split[0]] = int(split[2])
            elif split[1] == "bool":
                default_dict[split[0]] = strtobool(split[2])
            elif split[1] == "hex":
                default_dict[split[0]] = int(split[2], 16)
            else:
                default_dict[split[0]] = split[2]

    if len(settings):
        log.warning("No settings found (using default) for: {0}".format(", ".join(settings)))
    log.info("Done loading settings from {0}".format(sett_file))

    return default_dict

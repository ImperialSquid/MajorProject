import itertools as it
import logging as log
import random as rand
import sys

import pygame as pyg

from field_agent import FieldAgent
from spymaster import SpyMaster
from utils import load_settings


# TODO add a lot of processing logging
# TODO add game analysis log
class Game:
    def __init__(self):
        log.info("Initialising Game...")
        log.info("Initialising pygame...")
        pyg.init()

        self.setts = load_settings("settings/game_setts.txt",
                                   {"scrn_w": 500, "scrn_h": 500,
                                    "back_hex": 0xB52E59,
                                    "fore_hex_light": 0xC8C8C8, "fore_hex_dark": 0x646464,
                                    "red_spymaster_cpu": True, "red_field_agent_cpu": False,
                                    "blue_spymaster_cpu": True, "blue_field_agent_cpu": True})

        self.surface = pyg.display.set_mode((self.setts["scrn_w"], self.setts["scrn_h"]))

        self.screen = "loading"  # current screen to display
        self.draw()  # set loading screen before loading in agents

        self.red_spymaster = SpyMaster()
        self.red_spymaster.word_model.init_sims()
        self.red_field_agent = FieldAgent()

        self.blue_spymaster = SpyMaster()
        self.blue_spymaster.word_model.init_sims()
        self.blue_field_agent = FieldAgent()

        # intersection of both spymaster's game_words, means only words on board will be in both vocabs, no duplicates
        self.game_words = list(set(self.red_spymaster.game_words) & set(self.blue_spymaster.game_words))
        self.team_words = dict()  # all words on each team yet to be found
        self.discovered_team_words = dict()  # all words on each team, that have been found
        self.board = list()  # iterable of iterables for board state (5x5 grid)
        # rs = red spymaster, bs = blue spymaster,
        # rf = red field agent, bf = blue field agent
        self.current_agent = "rs"
        self.hint = None
        self.hint_num = 0
        self.guess = None
        self.guesses_made = 0

        self.buttons = dict()

        self.screen = "main"
        self.running = True
        self.loop()

    def loop(self):
        clock = pyg.time.Clock()
        while self.running:
            self.draw()
            clock.tick(30)
            self.process_events()
            if self.screen == "game":
                self.__process_game()

    def process_events(self):
        for event in pyg.event.get():
            if event.type == pyg.QUIT:
                self.quit()
            if event.type == pyg.MOUSEBUTTONDOWN:
                pos = pyg.mouse.get_pos()
                if self.screen == "main":
                    if self.buttons["play_btn"].collidepoint(pos):
                        self.screen = "setup"
                    if self.buttons["about_btn"].collidepoint(pos):
                        self.screen = "about"

                elif self.screen == "setup":
                    if self.buttons["back_btn"].collidepoint(pos):
                        self.screen = "main"

                    if self.buttons["red_sm_cpu_btn"].collidepoint(pos):
                        self.setts["red_spymaster_cpu"] = True
                    if self.buttons["red_sm_ply_btn"].collidepoint(pos):
                        self.setts["red_spymaster_cpu"] = False
                    if self.buttons["red_fa_cpu_btn"].collidepoint(pos):
                        self.setts["red_field_agent_cpu"] = True
                    if self.buttons["red_fa_ply_btn"].collidepoint(pos):
                        self.setts["red_field_agent_cpu"] = False

                    if self.buttons["blue_sm_cpu_btn"].collidepoint(pos):
                        self.setts["blue_spymaster_cpu"] = True
                    if self.buttons["blue_sm_ply_btn"].collidepoint(pos):
                        self.setts["blue_spymaster_cpu"] = False
                    if self.buttons["blue_fa_cpu_btn"].collidepoint(pos):
                        self.setts["blue_field_agent_cpu"] = True
                    if self.buttons["blue_fa_ply_btn"].collidepoint(pos):
                        self.setts["blue_field_agent_cpu"] = False

                    if self.buttons["begin_game_btn"].collidepoint(pos):
                        self.current_agent = rand.choice(["rs", "bs"])  # randomly pick who starts
                        rand.shuffle(self.game_words)
                        word_gen = it.cycle(self.game_words)

                        # if red goes first they have one more to guess, same for blue
                        self.team_words["red"] = [next(word_gen) for i in
                                                  range(9 if self.current_agent == "rs" else 8)]
                        self.team_words["blue"] = [next(word_gen) for i in
                                                   range(9 if self.current_agent == "bs" else 8)]
                        # always 7 bystanders and 1 assassin
                        self.team_words["grey"] = [next(word_gen) for i in range(7)]
                        self.team_words["black"] = [next(word_gen) for i in range(1)]

                        for team in self.team_words.keys():
                            self.discovered_team_words[team] = []  # start of game, all words on board are undiscovered

                        board_words = [x for x in it.chain.from_iterable(self.team_words.values())]
                        # list of lists to display board state
                        self.board = [board_words[5 * i: 5 * i + 5] for i in range(5)]

                        self.hint = None
                        self.hint_num = 0
                        self.guess = None
                        self.guesses_made = 0

                        self.screen = "game"

                        self.draw()  # skip past first spymaster processing to draw game screen
                        self.draw()

                elif self.screen == "game":
                    if self.buttons["back_btn"].collidepoint(pos):
                        self.screen = "setup"

                    for x in range(5):
                        for y in range(5):
                            if self.buttons["board_btns"][x][y].collidepoint(pos):
                                if self.board[x][y] not in [word for word in
                                                            it.chain(self.discovered_team_words.values())]:
                                    self.guess = self.board[x][y]

                    if self.buttons["pass_turn_btn"].collidepoint(pos):
                        self.hint = None
                        self.guesses_made = 0
                        if self.current_agent == "rf":
                            self.current_agent = "bs"
                        elif self.current_agent == "bf":
                            self.current_agent = "rs"
                        self.draw()  # skip past spymaster processing to draw game screen
                        self.draw()

    def __process_game(self):
        if self.current_agent[1] == "s" and self.hint is None:  # --- spymaster and no existing hint ---
            # TODO investigate if moving hint gen into a diff thread would prevent Not Responding window
            if self.current_agent[0] == "r" and self.setts["red_spymaster_cpu"]:  # red team, comp generated hint
                hints = self.red_spymaster.run_defined_round(reds=self.team_words["red"],
                                                             blues=self.team_words["blue"],
                                                             greys=self.team_words["grey"],
                                                             blacks=self.team_words["black"])
                hint = rand.choice([hint for hint in it.chain.from_iterable([hints for hints in hints.values()])])
                self.hint = hint[1][0]
                self.hint_num = len(hint[0])
                self.current_agent = "rf"

            elif self.current_agent[0] == "b" and self.setts["blue_spymaster_cpu"]:  # blue team, comp generated hint
                hints = self.blue_spymaster.run_defined_round(reds=self.team_words["blue"],
                                                              blues=self.team_words["red"],
                                                              greys=self.team_words["grey"],
                                                              blacks=self.team_words["black"])
                hint = rand.choice([hint for hint in it.chain.from_iterable([hints for hints in hints.values()])])
                self.hint = hint[1][0]
                self.hint_num = len(hint[0])
                self.current_agent = "bf"

            elif (self.current_agent[0] == "r" and not self.setts["red_spymaster_cpu"]) or \
                    (self.current_agent[0] == "b" and not self.setts["blue_spymaster_cpu"]):
                # either team, human gen hint
                pass  # TODO get player inputted hint

        elif self.current_agent[1] == "f":  # --- field agent ---
            # --- process cpu field agents ---
            if self.setts["red_field_agent_cpu"]:
                self.guess = ""  # TODO add comp hint eval
            elif self.setts["blue_field_agent_cpu"]:
                self.guess = ""

            # --- process guess ---
            if self.guess is not None:  # only do processing is guess exists, so user gen'd can take more than one frame
                # check for correct guess
                if (self.current_agent[0] == "r" and self.guess in self.team_words["red"]) or \
                        (self.current_agent[0] == "b" and self.guess in self.team_words["blue"]):

                    self.guesses_made += 1

                    if self.guesses_made >= self.hint_num + 1:  # if guess max reached reset counter and swap team
                        self.hint = None
                        self.guesses_made = 0
                        if self.current_agent[0] == "r":
                            self.current_agent = "bs"
                        else:
                            self.current_agent = "rs"

                else:  # if incorrect guess
                    if self.guess in self.team_words["black"]:
                        pass  # TODO add fail state
                    else:  # guess in wrong team or bystander by process of elimination
                        self.hint = None
                        self.guesses_made = 0
                        if self.current_agent[0] == "r":
                            self.current_agent = "bs"
                        else:
                            self.current_agent = "rs"

                for team in self.team_words.keys():
                    if self.guess in self.team_words[team]:
                        self.team_words[team].remove(self.guess)
                        self.discovered_team_words[team].append(self.guess)
                        self.guess = None
                # TODO add win state

    def draw(self):
        if self.screen == "loading":
            self.__draw_loading()
        elif self.screen == "main":
            self.__draw_main()
        elif self.screen == "setup":
            self.__draw_setup()
        elif self.screen == "game":
            self.__draw_game()
        elif self.screen == "win":
            self.__draw_win()
        elif self.screen == "about":
            self.__draw_about()
        pyg.display.flip()

    def __draw_loading(self):
        self.surface.fill((255, 255, 255))
        fnt = pyg.font.Font(pyg.font.get_default_font(), 30)
        txt = fnt.render("LOADING...", True, pyg.Color(self.setts["fore_hex_dark"]))
        coords = (self.surface.get_width() - fnt.size("LOADING...")[0] - 30,
                  self.surface.get_height() - fnt.size("LOADING...")[1] - 30)
        self.surface.blit(txt, coords)

    def __draw_main(self):
        self.surface.fill(pyg.Color(self.setts["back_hex"]))

        # -- play btn --
        fnt = pyg.font.Font(pyg.font.get_default_font(), 70)
        txt = fnt.render("CODENAMES", True, pyg.Color(self.setts["fore_hex_light"]))
        coords = ((self.surface.get_width() - fnt.size("CODENAMES")[0]) // 2, 50)
        self.surface.blit(txt, coords)

        play_btn = pyg.Rect(50, self.setts["scrn_h"] * 2 // 5,
                            self.setts["scrn_w"] // 2 - 100, self.setts["scrn_h"] // 4)
        pyg.draw.rect(self.surface, pyg.Color(self.setts["fore_hex_light"]), play_btn)
        self.buttons["play_btn"] = play_btn

        fnt = pyg.font.Font(pyg.font.get_default_font(), 50)
        txt = fnt.render("PLAY", True, pyg.Color(self.setts["fore_hex_dark"]))
        coords = (play_btn.centerx - fnt.size("PLAY")[0] // 2, play_btn.centery - fnt.size("PLAY")[1] // 2)
        self.surface.blit(txt, coords)

        # -- about btn --
        about_btn = pyg.Rect.copy(play_btn)
        about_btn.move_ip(self.setts["scrn_w"] // 2, 0)
        pyg.draw.rect(self.surface, pyg.Color(self.setts["fore_hex_light"]), about_btn)
        self.buttons["about_btn"] = about_btn

        fnt = pyg.font.Font(pyg.font.get_default_font(), 50)
        txt = fnt.render("ABOUT", True, pyg.Color(self.setts["fore_hex_dark"]))
        coords = (about_btn.centerx - fnt.size("ABOUT")[0] // 2, about_btn.centery - fnt.size("ABOUT")[1] // 2)
        self.surface.blit(txt, coords)

    def __draw_setup(self):
        self.surface.fill(pyg.Color(self.setts["back_hex"]))

        fnt1 = pyg.font.Font(pyg.font.get_default_font(), 70)
        fnt2 = pyg.font.Font(pyg.font.get_default_font(), 60)
        fnt3 = pyg.font.Font(pyg.font.get_default_font(), 40)
        fnt4 = pyg.font.Font(pyg.font.get_default_font(), 30)

        back_btn_dims = (fnt1.size("SETUP")[1], fnt1.size("SETUP")[1])
        back_btn = pyg.Rect((50, 50), back_btn_dims)
        pyg.draw.rect(self.surface, pyg.Color(self.setts["fore_hex_light"]), back_btn)
        self.buttons["back_btn"] = back_btn
        pyg.draw.polygon(self.surface, pyg.Color(self.setts["fore_hex_dark"]),
                         [(50 + back_btn_dims[0] // 4, 50 + back_btn_dims[1] // 2),
                          (50 + 3 * back_btn_dims[0] // 4, 50 + back_btn_dims[1] // 4),
                          (50 + 3 * back_btn_dims[0] // 4, 50 + 3 * back_btn_dims[1] // 4)])

        title = fnt1.render("SETUP", True, pyg.Color(self.setts["fore_hex_light"]))
        title_coords = ((self.surface.get_width() - fnt1.size("SETUP")[0]) // 2, 50)
        self.surface.blit(title, title_coords)

        # --- red team options ---
        r_team_title = fnt2.render("RED TEAM", True, pyg.Color(self.setts["fore_hex_light"]))
        r_team_title_coords = ((self.setts["scrn_w"] // 2 - fnt2.size("RED TEAM")[0]) // 2, self.setts["scrn_h"] // 4)
        self.surface.blit(r_team_title, r_team_title_coords)

        # --- red spymaster options ---
        txt3 = fnt3.render("SPYMASTER", True, pyg.Color(self.setts["fore_hex_light"]))
        coords3 = (self.setts["scrn_w"] // 4 - fnt3.size("SPYMASTER")[0] // 2,
                   self.setts["scrn_h"] // 4 + fnt2.size("RED TEAM")[1] + 10)
        self.surface.blit(txt3, coords3)

        red_sm_cpu_btn = pyg.Rect(
            (self.setts["scrn_w"] - 2 * fnt4.size("CPU")[0] - 2 * fnt4.size("PLAYER")[0] - 120) // 4,
            self.setts["scrn_h"] // 4 + fnt2.size("RED TEAM")[1] + fnt3.size("SPYMASTER")[1] + 20,
            fnt4.size("CPU")[0] + 20, fnt4.size("CPU")[1] + 20)
        self.buttons["red_sm_cpu_btn"] = red_sm_cpu_btn

        red_sm_ply_btn = pyg.Rect(
            (self.setts["scrn_w"] + 2 * fnt4.size("CPU")[0] - 2 * fnt4.size("PLAYER")[0] + 40) // 4,
            self.setts["scrn_h"] // 4 + fnt2.size("RED TEAM")[1] + fnt3.size("SPYMASTER")[1] + 20,
            fnt4.size("PLAYER")[0] + 20, fnt4.size("PLAYER")[1] + 20)
        self.buttons["red_sm_ply_btn"] = red_sm_ply_btn

        if self.setts["red_spymaster_cpu"]:
            pyg.draw.rect(self.surface, pyg.Color(self.setts["fore_hex_dark"]), red_sm_cpu_btn, 5)
        else:
            pyg.draw.rect(self.surface, pyg.Color(self.setts["fore_hex_dark"]), red_sm_ply_btn, 5)

        txt4 = fnt4.render("CPU", True, pyg.Color(self.setts["fore_hex_light"]))
        self.surface.blit(txt4, (red_sm_cpu_btn.x + 10, red_sm_cpu_btn.y + 10))

        txt4 = fnt4.render("PLAYER", True, pyg.Color(self.setts["fore_hex_light"]))
        self.surface.blit(txt4, (red_sm_ply_btn.x + 10, red_sm_ply_btn.y + 10))

        # --- red field agent options ---
        red_sm_offset = 10 + fnt3.size("SPYMASTER")[1] + 10 + fnt4.size("CPU")[1] + 10 + 10
        txt3 = fnt3.render("FIELD AGENT", True, pyg.Color(self.setts["fore_hex_light"]))
        coords3 = (self.setts["scrn_w"] // 4 - fnt3.size("SPYMASTER")[0] // 2,
                   self.setts["scrn_h"] // 4 + fnt2.size("RED TEAM")[1] + 10 + red_sm_offset)
        self.surface.blit(txt3, coords3)

        red_fa_cpu_btn = pyg.Rect(
            (self.setts["scrn_w"] - 2 * fnt4.size("CPU")[0] - 2 * fnt4.size("PLAYER")[0] - 120) // 4,
            self.setts["scrn_h"] // 4 + fnt2.size("RED TEAM")[1] + fnt3.size("FIELD AGENT")[1] + 20 + red_sm_offset,
            fnt4.size("CPU")[0] + 20, fnt4.size("CPU")[1] + 20)
        self.buttons["red_fa_cpu_btn"] = red_fa_cpu_btn

        red_fa_ply_btn = pyg.Rect(
            (self.setts["scrn_w"] + 2 * fnt4.size("CPU")[0] - 2 * fnt4.size("PLAYER")[0] + 40) // 4,
            self.setts["scrn_h"] // 4 + fnt2.size("RED TEAM")[1] + fnt3.size("FIELD AGENT")[1] + 20 + red_sm_offset,
            fnt4.size("PLAYER")[0] + 20, fnt4.size("PLAYER")[1] + 20)
        self.buttons["red_fa_ply_btn"] = red_fa_ply_btn

        if self.setts["red_field_agent_cpu"]:
            pyg.draw.rect(self.surface, pyg.Color(self.setts["fore_hex_dark"]), red_fa_cpu_btn, 5)
        else:
            pyg.draw.rect(self.surface, pyg.Color(self.setts["fore_hex_dark"]), red_fa_ply_btn, 5)

        txt4 = fnt4.render("CPU", True, pyg.Color(self.setts["fore_hex_light"]))
        self.surface.blit(txt4, (red_fa_cpu_btn.x + 10, red_fa_cpu_btn.y + 10))

        txt4 = fnt4.render("PLAYER", True, pyg.Color(self.setts["fore_hex_light"]))
        self.surface.blit(txt4, (red_fa_ply_btn.x + 10, red_fa_ply_btn.y + 10))

        # --- blue team options ---
        b_team_title = fnt2.render("BLUE TEAM", True, pyg.Color(self.setts["fore_hex_light"]))
        b_team_title_coords = (
            3 * self.setts["scrn_w"] // 4 - fnt2.size("BLUE TEAM")[0] // 2, self.setts["scrn_h"] // 4)
        self.surface.blit(b_team_title, b_team_title_coords)

        # --- blue spymaster options ---
        txt3 = fnt3.render("SPYMASTER", True, pyg.Color(self.setts["fore_hex_light"]))
        coords3 = (3 * self.setts["scrn_w"] // 4 - fnt3.size("SPYMASTER")[0] // 2,
                   self.setts["scrn_h"] // 4 + fnt2.size("RED TEAM")[1] + 10)
        self.surface.blit(txt3, coords3)

        blue_sm_cpu_btn = pyg.Rect(
            (3 * self.setts["scrn_w"] - 2 * fnt4.size("CPU")[0] - 2 * fnt4.size("PLAYER")[0] - 120) // 4,
            self.setts["scrn_h"] // 4 + fnt2.size("RED TEAM")[1] + fnt3.size("SPYMASTER")[1] + 20,
            fnt4.size("CPU")[0] + 20, fnt4.size("CPU")[1] + 20)
        self.buttons["blue_sm_cpu_btn"] = blue_sm_cpu_btn

        blue_sm_ply_btn = pyg.Rect(
            (3 * self.setts["scrn_w"] + 2 * fnt4.size("CPU")[0] - 2 * fnt4.size("PLAYER")[0] + 40) // 4,
            self.setts["scrn_h"] // 4 + fnt2.size("RED TEAM")[1] + fnt3.size("SPYMASTER")[1] + 20,
            fnt4.size("PLAYER")[0] + 20, fnt4.size("PLAYER")[1] + 20)
        self.buttons["blue_sm_ply_btn"] = blue_sm_ply_btn

        if self.setts["blue_spymaster_cpu"]:
            pyg.draw.rect(self.surface, pyg.Color(self.setts["fore_hex_dark"]), blue_sm_cpu_btn, 5)
        else:
            pyg.draw.rect(self.surface, pyg.Color(self.setts["fore_hex_dark"]), blue_sm_ply_btn, 5)

        txt4 = fnt4.render("CPU", True, pyg.Color(self.setts["fore_hex_light"]))
        self.surface.blit(txt4, (blue_sm_cpu_btn.x + 10, blue_sm_cpu_btn.y + 10))

        txt4 = fnt4.render("PLAYER", True, pyg.Color(self.setts["fore_hex_light"]))
        self.surface.blit(txt4, (blue_sm_ply_btn.x + 10, blue_sm_ply_btn.y + 10))

        # --- blue field agent options ---
        blue_sm_offset = 10 + fnt3.size("SPYMASTER")[1] + 10 + fnt4.size("CPU")[1] + 10 + 10
        txt3 = fnt3.render("FIELD AGENT", True, pyg.Color(self.setts["fore_hex_light"]))
        coords3 = (3 * self.setts["scrn_w"] // 4 - fnt3.size("SPYMASTER")[0] // 2,
                   self.setts["scrn_h"] // 4 + fnt2.size("BLUE TEAM")[1] + 10 + blue_sm_offset)
        self.surface.blit(txt3, coords3)

        blue_fa_cpu_btn = pyg.Rect(
            (3 * self.setts["scrn_w"] - 2 * fnt4.size("CPU")[0] - 2 * fnt4.size("PLAYER")[0] - 120) // 4,
            self.setts["scrn_h"] // 4 + fnt2.size("RED TEAM")[1] + fnt3.size("FIELD AGENT")[1] + 20 + blue_sm_offset,
            fnt4.size("CPU")[0] + 20, fnt4.size("CPU")[1] + 20)
        self.buttons["blue_fa_cpu_btn"] = blue_fa_cpu_btn

        blue_fa_ply_btn = pyg.Rect(
            (3 * self.setts["scrn_w"] + 2 * fnt4.size("CPU")[0] - 2 * fnt4.size("PLAYER")[0] + 40) // 4,
            self.setts["scrn_h"] // 4 + fnt2.size("RED TEAM")[1] + fnt3.size("FIELD AGENT")[1] + 20 + blue_sm_offset,
            fnt4.size("PLAYER")[0] + 20, fnt4.size("PLAYER")[1] + 20)
        self.buttons["blue_fa_ply_btn"] = blue_fa_ply_btn

        if self.setts["blue_field_agent_cpu"]:
            pyg.draw.rect(self.surface, pyg.Color(self.setts["fore_hex_dark"]), blue_fa_cpu_btn, 5)
        else:
            pyg.draw.rect(self.surface, pyg.Color(self.setts["fore_hex_dark"]), blue_fa_ply_btn, 5)

        txt4 = fnt4.render("CPU", True, pyg.Color(self.setts["fore_hex_light"]))
        self.surface.blit(txt4, (blue_fa_cpu_btn.x + 10, blue_fa_cpu_btn.y + 10))

        txt4 = fnt4.render("PLAYER", True, pyg.Color(self.setts["fore_hex_light"]))
        self.surface.blit(txt4, (blue_fa_ply_btn.x + 10, blue_fa_ply_btn.y + 10))

        # --- play button ---
        txt_dims = fnt2.size("BEGIN GAME!")
        begin_game_btn = pyg.Rect(
            ((self.setts["scrn_w"] - txt_dims[0] - 20) // 2,
             self.setts["scrn_h"] // 4 + blue_sm_offset * 2 + fnt2.size("RED TEAM")[1] + 30),
            (txt_dims[0] + 20, txt_dims[1] + 20))
        pyg.draw.rect(self.surface, pyg.Color(self.setts["fore_hex_light"]), begin_game_btn)
        self.buttons["begin_game_btn"] = begin_game_btn

        txt2 = fnt2.render("BEGIN GAME!", True, pyg.Color(self.setts["fore_hex_dark"]))
        self.surface.blit(txt2, (begin_game_btn.x + 10, begin_game_btn.y + 10))

    def __draw_game(self):
        self.surface.fill(pyg.Color(self.setts["back_hex"]))

        fnt1 = pyg.font.Font(pyg.font.get_default_font(), 70)
        fnt2 = pyg.font.Font(pyg.font.get_default_font(), 60)
        fnt3 = pyg.font.Font(pyg.font.get_default_font(), 40)
        fnt4 = pyg.font.Font(pyg.font.get_default_font(), 30)

        back_btn_dims = (fnt1.size("GAME")[1], fnt1.size("GAME")[1])
        back_btn = pyg.Rect((50, 50), back_btn_dims)
        pyg.draw.rect(self.surface, pyg.Color(self.setts["fore_hex_light"]), back_btn)
        self.buttons["back_btn"] = back_btn
        pyg.draw.polygon(self.surface, pyg.Color(self.setts["fore_hex_dark"]),
                         [(50 + back_btn_dims[0] // 4, 50 + back_btn_dims[1] // 2),
                          (50 + 3 * back_btn_dims[0] // 4, 50 + back_btn_dims[1] // 4),
                          (50 + 3 * back_btn_dims[0] // 4, 50 + 3 * back_btn_dims[1] // 4)])

        title = fnt1.render("GAME", True, pyg.Color(self.setts["fore_hex_light"]))
        title_coords = ((self.surface.get_width() - fnt1.size("GAME")[0]) // 2, 50)
        self.surface.blit(title, title_coords)

        # --- drawing word grid ---
        card_dims = [(self.setts["scrn_w"] - 50 * 2 - 10 * 4) // 5,
                     (5 * self.setts["scrn_h"] // 8 - 10 * 4) // 5]  # save recomputing each render

        board_btns = []  # list of lists of board word Rects

        # render board buttons
        for x in range(5):
            board_btns.append([])
            for y in range(5):
                btn = pyg.Rect((50 + x * (card_dims[0] + 10), self.setts["scrn_h"] // 4 + y * (10 + card_dims[1])),
                               card_dims)
                board_btns[-1].append(btn)  # append button to last list in list of lists

                if self.board[x][y] in self.discovered_team_words["red"]:  # render red,
                    pyg.draw.rect(self.surface, (225, 60, 20), btn)
                elif self.board[x][y] in self.discovered_team_words["blue"]:  # blue,
                    pyg.draw.rect(self.surface, (0, 100, 180), btn)
                elif self.board[x][y] in self.discovered_team_words["grey"]:  # grey
                    pyg.draw.rect(self.surface, (150, 150, 150), btn)
                elif self.board[x][y] in self.discovered_team_words["black"]:  # and black discovered words
                    pyg.draw.rect(self.surface, (20, 20, 20), btn)
                else:
                    # only render words on undiscovered words
                    pyg.draw.rect(self.surface, pyg.Color(self.setts["fore_hex_light"]), btn)

                    if fnt4.size(self.board[x][y].upper())[0] > card_dims[0] - 10:
                        # if text length exceeds box, split in two
                        txt1 = fnt4.render(self.board[x][y][:len(self.board[x][y]) // 2].upper() + "-", True,
                                           pyg.Color(self.setts["fore_hex_dark"]))
                        txt2 = fnt4.render(self.board[x][y][len(self.board[x][y]) // 2:].upper(), True,
                                           pyg.Color(self.setts["fore_hex_dark"]))
                        self.surface.blit(txt1, (btn.x + 5, btn.y + 5))
                        self.surface.blit(txt2, (btn.x + 5, btn.y + 5 + fnt4.size(self.board[x][y])[1]))
                    else:
                        txt = fnt4.render(self.board[x][y].upper(), True, pyg.Color(self.setts["fore_hex_dark"]))
                        self.surface.blit(txt, (btn.x + 5, btn.y + 5))

        self.buttons["board_btns"] = board_btns  # list of lists of buttons added as single item to simplify processing

        # --- other interface ---
        cur_txt = "Current: "
        if self.current_agent[0] == "r":
            cur_txt += "Red "
        elif self.current_agent[0] == "b":
            cur_txt += "Blue "

        if self.current_agent[1] == "s":
            cur_txt += "Spymaster"
        elif self.current_agent[1] == "f":
            cur_txt += "Field Agent"

        # no hint exists and comp generating
        if self.hint is None and ((self.current_agent == "rs" and self.setts["red_spymaster_cpu"]) or
                                  (self.current_agent == "bs" and self.setts["blue_spymaster_cpu"])):
            cur_txt += ", generating hint..."

        # no hint exists and user generated
        if self.hint is None and ((self.current_agent == "rs" and not self.setts["red_spymaster_cpu"]) or
                                  (self.current_agent == "bs" and not self.setts["blue_spymaster_cpu"])):
            cur_txt += ", input hint"

        # hint exists and comp evaluated
        if self.hint is not None and ((self.current_agent == "rf" and self.setts["red_field_agent_cpu"]) or
                                      (self.current_agent == "bf" and self.setts["blue_field_agent_cpu"])):
            cur_txt += ", evaluating hint..."

        # hint exists and user evaluated
        if self.hint is not None and ((self.current_agent == "rf" and not self.setts["red_field_agent_cpu"]) or
                                      (self.current_agent == "bf" and not self.setts["blue_field_agent_cpu"])):
            cur_txt += ", hint is \"{0} {1}\"".format(self.hint, self.hint_num)

        txt = fnt4.render(cur_txt, True, pyg.Color(self.setts["fore_hex_light"]))
        self.surface.blit(txt, (50, 7 * self.setts["scrn_h"] // 8 + 10))

        btn = pyg.Rect((self.setts["scrn_w"] - 50 - 2 * 5 - fnt4.size("PASS TURN")[0],
                        7 * self.setts["scrn_h"] // 8 + 10),
                       (fnt4.size("PASS TURN")[0] + 10, fnt4.size("PASS TURN")[1] + 10))
        self.buttons["pass_turn_btn"] = btn

        if self.guesses_made >= 1 and self.current_agent[1] == "f":  # only draw the button if activating it is legal
            pyg.draw.rect(self.surface, pyg.Color(self.setts["fore_hex_dark"]), btn)

            txt = fnt4.render("PASS TURN", True, pyg.Color(self.setts["fore_hex_light"]))
            self.surface.blit(txt, (btn.x + 5, btn.y + 5))

    def __draw_win(self):
        pass

    def __draw_about(self):
        self.surface.fill(pyg.Color(self.setts["back_hex"]))

        fnt = pyg.font.Font(pyg.font.get_default_font(), 70)
        txt = fnt.render("ABOUT", True, pyg.Color(self.setts["fore_hex_light"]))
        coords = ((self.surface.get_width() - fnt.size("ABOUT")[0]) // 2, 40)
        self.surface.blit(txt, coords)

    def quit(self):
        pyg.quit()
        self.running = False
        sys.exit()


if __name__ == "__main__":
    game_logger = log.getLogger("game")
    game_logger.setLevel(log.DEBUG)
    handler = log.FileHandler("logs/game-log.txt", "a", "utf-8")
    handler.setFormatter(log.Formatter("%(asctime)s : %(module)-15s : %(levelname)s : %(message)s",
                                       datefmt="%d/%m - %H:%M:%S"))
    game_logger.addHandler(handler)

    game = Game()

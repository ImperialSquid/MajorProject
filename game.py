import logging as log

import pygame as pyg

from field_agent import FieldAgent
from spymaster import SpyMaster


class Game:
    def __init__(self):
        log.info("Initialising Game...")
        log.info("Initialising pygame...")
        pyg.init()

        self.setts = self.__load_settings("settings/game_setts.txt",
                                          {"scrn_w": 500, "scrn_h": 500,
                                           "red_spymaster_cpu": 1, "red_field_agent_cpu": 1,
                                           "blue_spymaster_cpu": 1, "blue_field_agent_cpu": 1})

        self.surface = pyg.display.set_mode((self.setts["scrn_w"], self.setts["scrn_h"]))

        self.screen = "loading"
        self.draw()

        self.red_spymaster = SpyMaster()
        self.red_field_agent = FieldAgent()

        self.blue_spymaster = SpyMaster()
        self.blue_field_agent = FieldAgent()

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
                        self.setts["red_spymaster_cpu"] = 1
                    if self.buttons["red_sm_ply_btn"].collidepoint(pos):
                        self.setts["red_spymaster_cpu"] = 0
                    if self.buttons["red_fa_cpu_btn"].collidepoint(pos):
                        self.setts["red_field_agent_cpu"] = 1
                    if self.buttons["red_fa_ply_btn"].collidepoint(pos):
                        self.setts["red_field_agent_cpu"] = 0

                    if self.buttons["blue_sm_cpu_btn"].collidepoint(pos):
                        self.setts["blue_spymaster_cpu"] = 1
                    if self.buttons["blue_sm_ply_btn"].collidepoint(pos):
                        self.setts["blue_spymaster_cpu"] = 0
                    if self.buttons["blue_fa_cpu_btn"].collidepoint(pos):
                        self.setts["blue_field_agent_cpu"] = 1
                    if self.buttons["blue_fa_ply_btn"].collidepoint(pos):
                        self.setts["blue_field_agent_cpu"] = 0

    def draw(self):
        if self.screen == "loading":
            self.__draw_loading()
        elif self.screen == "main":
            self.__draw_main()
        elif self.screen == "setup":
            self.__draw_setup()
        elif self.screen == "game":
            self.__draw_game()
        elif self.screen == "about":
            self.__draw_about()
        pyg.display.flip()

    def __draw_loading(self):
        self.surface.fill((255, 255, 255))
        fnt = pyg.font.Font(pyg.font.get_default_font(), 30)
        txt = fnt.render("LOADING...", True, (100, 100, 100))
        coords = (self.surface.get_width() - fnt.size("LOADING...")[0] - 30,
                  self.surface.get_height() - fnt.size("LOADING...")[1] - 30)
        self.surface.blit(txt, coords)

    def __draw_main(self):
        self.surface.fill((181, 46, 89))

        fnt = pyg.font.Font(pyg.font.get_default_font(), 70)
        txt = fnt.render("CODENAMES", True, (200, 200, 200))
        coords = ((self.surface.get_width() - fnt.size("CODENAMES")[0]) // 2, 50)
        self.surface.blit(txt, coords)

        play_btn = pyg.Rect(50, self.setts["scrn_h"] * 2 // 5,
                            self.setts["scrn_w"] // 2 - 100, self.setts["scrn_h"] // 4)
        pyg.draw.rect(self.surface, (200, 200, 200), play_btn)
        self.buttons["play_btn"] = play_btn

        fnt = pyg.font.Font(pyg.font.get_default_font(), 50)
        txt = fnt.render("PLAY", True, (100, 100, 100))
        coords = (play_btn.centerx - fnt.size("PLAY")[0] // 2, play_btn.centery - fnt.size("PLAY")[1] // 2)
        self.surface.blit(txt, coords)

        about_btn = pyg.Rect.copy(play_btn)
        about_btn.move_ip(self.setts["scrn_w"] // 2, 0)
        pyg.draw.rect(self.surface, (200, 200, 200), about_btn)
        self.buttons["about_btn"] = about_btn

        fnt = pyg.font.Font(pyg.font.get_default_font(), 50)
        txt = fnt.render("ABOUT", True, (100, 100, 100))
        coords = (about_btn.centerx - fnt.size("ABOUT")[0] // 2, about_btn.centery - fnt.size("ABOUT")[1] // 2)
        self.surface.blit(txt, coords)

    def __draw_setup(self):
        self.surface.fill((181, 46, 89))

        fnt1 = pyg.font.Font(pyg.font.get_default_font(), 70)
        fnt2 = pyg.font.Font(pyg.font.get_default_font(), 60)
        fnt3 = pyg.font.Font(pyg.font.get_default_font(), 40)
        fnt4 = pyg.font.Font(pyg.font.get_default_font(), 30)

        back_btn_dims = (fnt1.size("SETUP")[1], fnt1.size("SETUP")[1])
        back_btn = pyg.Rect((50, 50), back_btn_dims)
        pyg.draw.rect(self.surface, (200, 200, 200), back_btn)
        self.buttons["back_btn"] = back_btn
        pyg.draw.polygon(self.surface, (100, 100, 100), [(50 + back_btn_dims[0] // 4, 50 + back_btn_dims[1] // 2),
                                                         (50 + 3 * back_btn_dims[0] // 4, 50 + back_btn_dims[1] // 4),
                                                         (50 + 3 * back_btn_dims[0] // 4,
                                                          50 + 3 * back_btn_dims[1] // 4)])

        title = fnt1.render("SETUP", True, (200, 200, 200))
        title_coords = ((self.surface.get_width() - fnt1.size("SETUP")[0]) // 2, 50)
        self.surface.blit(title, title_coords)

        # --- red team options ---
        r_team_title = fnt2.render("RED TEAM", True, (200, 200, 200))
        r_team_title_coords = ((self.setts["scrn_w"] // 2 - fnt2.size("RED TEAM")[0]) // 2, self.setts["scrn_h"] // 3)
        self.surface.blit(r_team_title, r_team_title_coords)

        # --- red spymaster options ---
        txt3 = fnt3.render("SPYMASTER", True, (200, 200, 200))
        coords3 = (self.setts["scrn_w"] // 4 - fnt3.size("SPYMASTER")[0] // 2,
                   self.setts["scrn_h"] // 3 + fnt2.size("RED TEAM")[1] + 10)
        self.surface.blit(txt3, coords3)

        red_sm_cpu_btn = pyg.Rect(
            (self.setts["scrn_w"] - 2 * fnt4.size("CPU")[0] - 2 * fnt4.size("PLAYER")[0] - 120) // 4,
            self.setts["scrn_h"] // 3 + fnt2.size("RED TEAM")[1] + fnt3.size("SPYMASTER")[1] + 20,
            fnt4.size("CPU")[0] + 20, fnt4.size("CPU")[1] + 20)
        self.buttons["red_sm_cpu_btn"] = red_sm_cpu_btn

        red_sm_ply_btn = pyg.Rect(
            (self.setts["scrn_w"] + 2 * fnt4.size("CPU")[0] - 2 * fnt4.size("PLAYER")[0] + 40) // 4,
            self.setts["scrn_h"] // 3 + fnt2.size("RED TEAM")[1] + fnt3.size("SPYMASTER")[1] + 20,
            fnt4.size("PLAYER")[0] + 20, fnt4.size("PLAYER")[1] + 20)
        self.buttons["red_sm_ply_btn"] = red_sm_ply_btn

        if self.setts["red_spymaster_cpu"]:
            pyg.draw.rect(self.surface, (100, 100, 100), red_sm_cpu_btn, 5)
        else:
            pyg.draw.rect(self.surface, (100, 100, 100), red_sm_ply_btn, 5)

        txt4 = fnt4.render("CPU", True, (200, 200, 200))
        self.surface.blit(txt4, (red_sm_cpu_btn.x + 10, red_sm_cpu_btn.y + 10))

        txt4 = fnt4.render("PLAYER", True, (200, 200, 200))
        self.surface.blit(txt4, (red_sm_ply_btn.x + 10, red_sm_ply_btn.y + 10))

        # --- red field agent options ---
        red_sm_offset = 10 + fnt3.size("SPYMASTER")[1] + 10 + fnt4.size("CPU")[1] + 10 + 10
        txt3 = fnt3.render("FIELD AGENT", True, (200, 200, 200))
        coords3 = (self.setts["scrn_w"] // 4 - fnt3.size("SPYMASTER")[0] // 2,
                   self.setts["scrn_h"] // 3 + fnt2.size("RED TEAM")[1] + 10 + red_sm_offset)
        self.surface.blit(txt3, coords3)

        red_fa_cpu_btn = pyg.Rect(
            (self.setts["scrn_w"] - 2 * fnt4.size("CPU")[0] - 2 * fnt4.size("PLAYER")[0] - 120) // 4,
            self.setts["scrn_h"] // 3 + fnt2.size("RED TEAM")[1] + fnt3.size("FIELD AGENT")[1] + 20 + red_sm_offset,
            fnt4.size("CPU")[0] + 20, fnt4.size("CPU")[1] + 20)
        self.buttons["red_fa_cpu_btn"] = red_fa_cpu_btn

        red_fa_ply_btn = pyg.Rect(
            (self.setts["scrn_w"] + 2 * fnt4.size("CPU")[0] - 2 * fnt4.size("PLAYER")[0] + 40) // 4,
            self.setts["scrn_h"] // 3 + fnt2.size("RED TEAM")[1] + fnt3.size("FIELD AGENT")[1] + 20 + red_sm_offset,
            fnt4.size("PLAYER")[0] + 20, fnt4.size("PLAYER")[1] + 20)
        self.buttons["red_fa_ply_btn"] = red_fa_ply_btn

        if self.setts["red_field_agent_cpu"]:
            pyg.draw.rect(self.surface, (100, 100, 100), red_fa_cpu_btn, 5)
        else:
            pyg.draw.rect(self.surface, (100, 100, 100), red_fa_ply_btn, 5)

        txt4 = fnt4.render("CPU", True, (200, 200, 200))
        self.surface.blit(txt4, (red_fa_cpu_btn.x + 10, red_fa_cpu_btn.y + 10))

        txt4 = fnt4.render("PLAYER", True, (200, 200, 200))
        self.surface.blit(txt4, (red_fa_ply_btn.x + 10, red_fa_ply_btn.y + 10))

        # --- blue team options ---
        b_team_title = fnt2.render("BLUE TEAM", True, (200, 200, 200))
        b_team_title_coords = (
            3 * self.setts["scrn_w"] // 4 - fnt2.size("BLUE TEAM")[0] // 2, self.setts["scrn_h"] // 3)
        self.surface.blit(b_team_title, b_team_title_coords)

        # --- blue spymaster options ---
        txt3 = fnt3.render("SPYMASTER", True, (200, 200, 200))
        coords3 = (3 * self.setts["scrn_w"] // 4 - fnt3.size("SPYMASTER")[0] // 2,
                   self.setts["scrn_h"] // 3 + fnt2.size("RED TEAM")[1] + 10)
        self.surface.blit(txt3, coords3)

        blue_sm_cpu_btn = pyg.Rect(
            (3 * self.setts["scrn_w"] - 2 * fnt4.size("CPU")[0] - 2 * fnt4.size("PLAYER")[0] - 120) // 4,
            self.setts["scrn_h"] // 3 + fnt2.size("RED TEAM")[1] + fnt3.size("SPYMASTER")[1] + 20,
            fnt4.size("CPU")[0] + 20, fnt4.size("CPU")[1] + 20)
        self.buttons["blue_sm_cpu_btn"] = blue_sm_cpu_btn

        blue_sm_ply_btn = pyg.Rect(
            (3 * self.setts["scrn_w"] + 2 * fnt4.size("CPU")[0] - 2 * fnt4.size("PLAYER")[0] + 40) // 4,
            self.setts["scrn_h"] // 3 + fnt2.size("RED TEAM")[1] + fnt3.size("SPYMASTER")[1] + 20,
            fnt4.size("PLAYER")[0] + 20, fnt4.size("PLAYER")[1] + 20)
        self.buttons["blue_sm_ply_btn"] = blue_sm_ply_btn

        if self.setts["blue_spymaster_cpu"]:
            pyg.draw.rect(self.surface, (100, 100, 100), blue_sm_cpu_btn, 5)
        else:
            pyg.draw.rect(self.surface, (100, 100, 100), blue_sm_ply_btn, 5)

        txt4 = fnt4.render("CPU", True, (200, 200, 200))
        self.surface.blit(txt4, (blue_sm_cpu_btn.x + 10, blue_sm_cpu_btn.y + 10))

        txt4 = fnt4.render("PLAYER", True, (200, 200, 200))
        self.surface.blit(txt4, (blue_sm_ply_btn.x + 10, blue_sm_ply_btn.y + 10))

        # --- blue field agent options ---
        blue_sm_offset = 10 + fnt3.size("SPYMASTER")[1] + 10 + fnt4.size("CPU")[1] + 10 + 10
        txt3 = fnt3.render("FIELD AGENT", True, (200, 200, 200))
        coords3 = (3 * self.setts["scrn_w"] // 4 - fnt3.size("SPYMASTER")[0] // 2,
                   self.setts["scrn_h"] // 3 + fnt2.size("BLUE TEAM")[1] + 10 + blue_sm_offset)
        self.surface.blit(txt3, coords3)

        blue_fa_cpu_btn = pyg.Rect(
            (3 * self.setts["scrn_w"] - 2 * fnt4.size("CPU")[0] - 2 * fnt4.size("PLAYER")[0] - 120) // 4,
            self.setts["scrn_h"] // 3 + fnt2.size("RED TEAM")[1] + fnt3.size("FIELD AGENT")[1] + 20 + blue_sm_offset,
            fnt4.size("CPU")[0] + 20, fnt4.size("CPU")[1] + 20)
        self.buttons["blue_fa_cpu_btn"] = blue_fa_cpu_btn

        blue_fa_ply_btn = pyg.Rect(
            (3 * self.setts["scrn_w"] + 2 * fnt4.size("CPU")[0] - 2 * fnt4.size("PLAYER")[0] + 40) // 4,
            self.setts["scrn_h"] // 3 + fnt2.size("RED TEAM")[1] + fnt3.size("FIELD AGENT")[1] + 20 + blue_sm_offset,
            fnt4.size("PLAYER")[0] + 20, fnt4.size("PLAYER")[1] + 20)
        self.buttons["blue_fa_ply_btn"] = blue_fa_ply_btn

        if self.setts["blue_field_agent_cpu"]:
            pyg.draw.rect(self.surface, (100, 100, 100), blue_fa_cpu_btn, 5)
        else:
            pyg.draw.rect(self.surface, (100, 100, 100), blue_fa_ply_btn, 5)

        txt4 = fnt4.render("CPU", True, (200, 200, 200))
        self.surface.blit(txt4, (blue_fa_cpu_btn.x + 10, blue_fa_cpu_btn.y + 10))

        txt4 = fnt4.render("PLAYER", True, (200, 200, 200))
        self.surface.blit(txt4, (blue_fa_ply_btn.x + 10, blue_fa_ply_btn.y + 10))

    def __draw_game(self):
        pass

    def __draw_about(self):
        self.surface.fill((181, 46, 89))

        fnt = pyg.font.Font(pyg.font.get_default_font(), 70)
        txt = fnt.render("ABOUT", True, (200, 200, 200))
        coords = ((self.surface.get_width() - fnt.size("ABOUT")[0]) // 2, 40)
        self.surface.blit(txt, coords)

    def quit(self):
        pyg.quit()
        self.running = False

    def __load_settings(self, sett_file: str, default_dict: dict):
        # loads setts in the form of <setting name>:<value> from file (only loads numeric values)
        log.info("Loading setts for {0} from {1}... ".format(", ".join(default_dict.keys()), sett_file))
        lines = [line.strip() for line in open(sett_file).readlines()]
        splits = {line.split(":")[0]: line.split(":")[1] for line in lines}  # reads in a definitions list for setts

        for k in default_dict.keys():  # reassign setts if a new one was found
            try:
                default_dict[k] = int(splits[k])
                log.debug("Found value for {0}: {1}".format(k, default_dict[k]))
            except KeyError:
                log.warning("No value found for {0}, using default value {1}".format(k, default_dict[k]))

        log.info("Done loading setts from {0}".format(sett_file))
        return default_dict


if __name__ == "__main__":
    root_logger = log.getLogger()
    root_logger.setLevel(log.DEBUG)
    handler = log.FileHandler("logs/game-log.txt", "a", "utf-8")
    handler.setFormatter(log.Formatter("%(asctime)s : %(module)-15s : %(levelname)s : %(message)s",
                                       datefmt="%d/%m - %H:%M:%S"))
    root_logger.addHandler(handler)

    game = Game()

import sys

import numpy as np
import pygame as pg

WIDTH, HEIGHT = 1200, 700
WIN_SIZE = (WIDTH, HEIGHT)
FPS = 144

FIRE_PALETTE_NAMES = ['black', 'blue', 'blue3', 'aqua', 'white']


class FireConfig:
    def __init__(self):
        self.pixel_size = 2
        self.steps_between_colors = 4
        self.cool_rate = 0.30
        self.jitter = 4
        self.bias = 1
        self.seed_bottom = True

    @property
    def palette_size(self):
        return (len(FIRE_PALETTE_NAMES) - 1) * self.steps_between_colors + 1


def build_palette(cfg):
    n = cfg.palette_size
    pal = np.zeros((n, 3), dtype=np.uint8)
    colors = [(0, 0, 0)]
    for i in range(len(FIRE_PALETTE_NAMES) - 1):
        c1, c2 = FIRE_PALETTE_NAMES[i], FIRE_PALETTE_NAMES[i + 1]
        for step in range(cfg.steps_between_colors):
            colors.append(pg.Color(c1).lerp(
                c2, (step + 0.5) / cfg.steps_between_colors)[:3])
    pal[:len(colors)] = colors
    return pal


class DoomFire:
    def __init__(self, app, cfg):
        self.app = app
        self.cfg = cfg
        self.palette = build_palette(cfg)
        self.rng = np.random.default_rng()

        self.w = WIDTH // cfg.pixel_size
        self.h = HEIGHT // cfg.pixel_size
        self.surface = pg.Surface((self.w, self.h), depth=24).convert()
        self.rebuild()

    def rebuild(self):
        self.palette = build_palette(self.cfg)
        self.fire = np.zeros((self.w, self.h), dtype=np.uint8)
        self.fire[:, -1] = self.cfg.palette_size - 1

    def update(self):
        cfg = self.cfg
        w, h = self.w, self.h
        fire = self.fire

        rnd = self.rng.integers(
            0, cfg.jitter + 1, size=(w, h - 1), dtype=np.int16)
        cool = (self.rng.random((w, h - 1)) < cfg.cool_rate).astype(np.int16)
        vals = fire[:, 1:].astype(np.int16)
        new_vals = np.maximum(vals - cool, 0)

        xs = (np.arange(w, dtype=np.int16)[:, None] - rnd + cfg.bias) % w
        ys = np.arange(h - 1, dtype=np.int16)[None, :].repeat(w, axis=0)
        fire[xs, ys] = new_vals.astype(np.uint8)

        if cfg.seed_bottom:
            fire[:, -1] = cfg.palette_size - 1

    def draw(self):
        rgb = self.palette[self.fire]
        pg.surfarray.blit_array(self.surface, rgb)
        self.app.screen.blit(
            pg.transform.scale(self.surface, (WIDTH, HEIGHT)), (0, 0))


class App:
    def __init__(self):
        pg.font.init()
        self.screen = pg.display.set_mode(WIN_SIZE)
        self.clock = pg.time.Clock()
        self.font = pg.font.Font(None, 22)
        self.cfg = FireConfig()
        self.fire = DoomFire(self, self.cfg)
        self.show_hud = True

    def handle_tweaks(self):
        keys = pg.key.get_pressed()
        cfg = self.cfg

        if keys[pg.K_q]:
            cfg.cool_rate = min(cfg.cool_rate + 0.02, 0.95)
        if keys[pg.K_a]:
            cfg.cool_rate = max(cfg.cool_rate - 0.02, 0.02)
        if keys[pg.K_w]:
            cfg.jitter = min(cfg.jitter + 1, 12)
        if keys[pg.K_s]:
            cfg.jitter = max(cfg.jitter - 1, 0)
        if keys[pg.K_e]:
            cfg.bias = min(cfg.bias + 1, 4)
        if keys[pg.K_d]:
            cfg.bias = max(cfg.bias - 1, -4)
        if keys[pg.K_r]:
            cfg.seed_bottom = not cfg.seed_bottom

        if keys[pg.K_t] or keys[pg.K_g]:
            if keys[pg.K_t]:
                cfg.steps_between_colors = min(
                    cfg.steps_between_colors + 1, 12)
            if keys[pg.K_g]:
                cfg.steps_between_colors = max(cfg.steps_between_colors - 1, 1)
            self.fire.rebuild()

    def draw_hud(self):
        cfg = self.cfg
        lines = [
            f"FPS {self.clock.get_fps():5.1f}",
            f"cool_rate  {cfg.cool_rate:4.2f}     Q/A",
            f"jitter     {cfg.jitter:2d}        W/S",
            f"bias       {cfg.bias:2d}        E/D",
            f"steps      {cfg.steps_between_colors:2d}        T/G",
            f"seed_bot   {str(cfg.seed_bottom):5s}     R",
            f"TAB: toggle HUD",
        ]
        y = 10
        for line in lines:
            surf = self.font.render(line, True, (255, 230, 180))
            bg = pg.Surface(surf.get_size(), pg.SRCALPHA)
            bg.fill((0, 0, 0, 150))
            self.screen.blit(bg, (10, y))
            self.screen.blit(surf, (10, y))
            y += 22

    def run(self):
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                if event.type == pg.KEYDOWN and event.key == pg.K_TAB:
                    self.show_hud = not self.show_hud

            self.handle_tweaks()
            self.fire.update()
            self.fire.draw()
            if self.show_hud:
                self.draw_hud()
            pg.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    App().run()

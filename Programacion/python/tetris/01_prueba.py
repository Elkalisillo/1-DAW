"""
TETRIS - versión estética en Python + pygame
Instalar:  pip install pygame
Ejecutar:  python tetris.py

Controles
  ← →      mover            ↑ / X   rotar (horario)
  ↓        bajada suave     Z       rotar (antihorario)
  ESPACIO  caída directa    C       guardar pieza (hold)
  P        pausa            R       reiniciar        ESC  salir
"""
import math
import random
import sys

import pygame

# ----------------------------------------------------------------- config
COLS, ROWS, CELL = 10, 20, 32
BOARD_X, BOARD_Y = 230, 60
BOARD_W, BOARD_H = COLS * CELL, ROWS * CELL
WIDTH, HEIGHT = BOARD_X + BOARD_W + 230, BOARD_Y + BOARD_H + 20

SHAPES = {
    "I": [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
    "O": [[1, 1], [1, 1]],
    "T": [[0, 1, 0], [1, 1, 1], [0, 0, 0]],
    "S": [[0, 1, 1], [1, 1, 0], [0, 0, 0]],
    "Z": [[1, 1, 0], [0, 1, 1], [0, 0, 0]],
    "J": [[1, 0, 0], [1, 1, 1], [0, 0, 0]],
    "L": [[0, 0, 1], [1, 1, 1], [0, 0, 0]],
}
COLORS = {
    "I": (64, 224, 255),
    "O": (255, 214, 64),
    "T": (186, 104, 255),
    "S": (96, 235, 130),
    "Z": (255, 92, 108),
    "J": (80, 130, 255),
    "L": (255, 160, 64),
}
LINE_POINTS = [0, 100, 300, 500, 800]
KICKS = [(0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1), (-1, -1), (1, -1)]


def rot_cw(m):
    return [list(r) for r in zip(*m[::-1])]


def rot_ccw(m):
    return [list(r) for r in zip(*m)][::-1]


# ----------------------------------------------------------------- dibujo
_block_cache = {}


def block_surface(kind, size):
    """Bloque con borde, brillo superior y destello (cacheado)."""
    key = (kind, size)
    if key in _block_cache:
        return _block_cache[key]
    color = COLORS[kind]
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    dark = tuple(int(c * 0.42) for c in color)
    light = tuple(min(255, int(c * 1.2) + 30) for c in color)
    outer = pygame.Rect(1, 1, size - 2, size - 2)
    pygame.draw.rect(s, dark, outer, border_radius=max(3, size // 5))
    inner = outer.inflate(-max(3, size // 7), -max(3, size // 7))
    pygame.draw.rect(s, color, inner, border_radius=max(3, size // 6))
    # degradado suave: franja inferior más oscura
    band = pygame.Surface((inner.w, inner.h // 2), pygame.SRCALPHA)
    pygame.draw.rect(band, (0, 0, 0, 45), band.get_rect(),
                     border_bottom_left_radius=max(3, size // 6),
                     border_bottom_right_radius=max(3, size // 6))
    s.blit(band, (inner.x, inner.y + inner.h // 2))
    # brillo superior
    hl = pygame.Surface((inner.w - 4, max(3, inner.h // 3)), pygame.SRCALPHA)
    pygame.draw.rect(hl, (*light, 120), hl.get_rect(), border_radius=max(2, size // 8))
    s.blit(hl, (inner.x + 2, inner.y + 2))
    # destello
    pygame.draw.circle(s, (255, 255, 255, 190), (inner.x + 5, inner.y + 5), max(1, size // 14))
    _block_cache[key] = s
    return s


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def make_background():
    bg = pygame.Surface((WIDTH, HEIGHT))
    top, bottom = (10, 12, 30), (34, 14, 54)
    for y in range(HEIGHT):
        pygame.draw.line(bg, lerp(top, bottom, y / HEIGHT), (0, y), (WIDTH, y))
    return bg


def make_glow():
    pad = 24
    g = pygame.Surface((BOARD_W + pad * 2, BOARD_H + pad * 2), pygame.SRCALPHA)
    for i in range(10, 0, -1):
        r = pygame.Rect(pad, pad, BOARD_W, BOARD_H).inflate(i * 2, i * 2)
        pygame.draw.rect(g, (110, 130, 255, 5 + (10 - i) * 3), r, width=2, border_radius=10 + i)
    return g, pad


class Piece:
    def __init__(self, kind):
        self.kind = kind
        self.m = [row[:] for row in SHAPES[kind]]
        self.x = (COLS - len(self.m[0])) // 2
        self.y = 0

    def cells(self, m=None, x=None, y=None):
        m = self.m if m is None else m
        x = self.x if x is None else x
        y = self.y if y is None else y
        for r, row in enumerate(m):
            for c, v in enumerate(row):
                if v:
                    yield x + c, y + r


# ----------------------------------------------------------------- juego
class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.grid = [[None] * COLS for _ in range(ROWS)]
        self.bag = []
        self.queue = [self.next_kind() for _ in range(3)]
        self.score = self.lines = 0
        self.level = 1
        self.hold = None
        self.can_hold = True
        self.fall_t = 0.0
        self.state = "play"      # play | clearing
        self.clear_rows = []
        self.clear_t = 0.0
        self.over = False
        self.paused = False
        self.particles = []
        self.popups = []
        self.shake = 0.0
        self.dir = 0
        self.das_t = self.arr_t = 0.0
        self.cur = None
        self.spawn()

    # --- piezas
    def next_kind(self):
        if not self.bag:
            self.bag = list(SHAPES)
            random.shuffle(self.bag)
        return self.bag.pop()

    def valid(self, m, x, y):
        for r, row in enumerate(m):
            for c, v in enumerate(row):
                if not v:
                    continue
                cx, cy = x + c, y + r
                if cx < 0 or cx >= COLS or cy >= ROWS:
                    return False
                if cy >= 0 and self.grid[cy][cx]:
                    return False
        return True

    def spawn(self):
        self.cur = Piece(self.queue.pop(0))
        self.queue.append(self.next_kind())
        self.can_hold = True
        self.fall_t = 0.0
        if not self.valid(self.cur.m, self.cur.x, self.cur.y):
            self.over = True

    def move(self, dx, dy):
        p = self.cur
        if p and self.valid(p.m, p.x + dx, p.y + dy):
            p.x += dx
            p.y += dy
            return True
        return False

    def rotate(self, clockwise=True):
        p = self.cur
        if not p or p.kind == "O":
            return
        m = rot_cw(p.m) if clockwise else rot_ccw(p.m)
        for dx, dy in KICKS:
            if self.valid(m, p.x + dx, p.y + dy):
                p.m, p.x, p.y = m, p.x + dx, p.y + dy
                return

    def ghost_y(self):
        p = self.cur
        y = p.y
        while self.valid(p.m, p.x, y + 1):
            y += 1
        return y

    def hard_drop(self):
        if not self.cur or self.state != "play":
            return
        gy = self.ghost_y()
        dist = gy - self.cur.y
        self.score += dist * 2
        for x, y in self.cur.cells(y=gy):
            self.burst(x, y, COLORS[self.cur.kind], 3, 60)
        self.cur.y = gy
        self.shake = 6.0
        self.lock()

    def do_hold(self):
        if not self.cur or not self.can_hold or self.state != "play":
            return
        kind = self.cur.kind
        if self.hold is None:
            self.hold = kind
            self.spawn()
        else:
            self.cur = Piece(self.hold)
            self.hold = kind
            self.fall_t = 0.0
            if not self.valid(self.cur.m, self.cur.x, self.cur.y):
                self.over = True
        self.can_hold = False

    def lock(self):
        for x, y in self.cur.cells():
            if 0 <= y < ROWS:
                self.grid[y][x] = self.cur.kind
        self.cur = None
        full = [r for r in range(ROWS) if all(self.grid[r])]
        if full:
            self.state = "clearing"
            self.clear_rows = full
            self.clear_t = 0.0
            for r in full:
                for c in range(COLS):
                    self.burst(c, r, COLORS[self.grid[r][c]], 3, 140)
        else:
            self.spawn()

    def finish_clear(self):
        n = len(self.clear_rows)
        for r in sorted(self.clear_rows):
            del self.grid[r]
            self.grid.insert(0, [None] * COLS)
        self.score += LINE_POINTS[n] * self.level
        self.lines += n
        self.level = self.lines // 10 + 1
        names = {1: "SINGLE", 2: "DOUBLE", 3: "TRIPLE", 4: "¡TETRIS!"}
        self.popups.append([names[n], 0.0])
        if n == 4:
            self.shake = 12.0
        self.clear_rows = []
        self.state = "play"
        self.spawn()

    # --- efectos
    def burst(self, gx, gy, color, count, speed):
        px = gx * CELL + CELL / 2
        py = gy * CELL + CELL / 2
        for _ in range(count):
            a = random.uniform(0, math.tau)
            v = random.uniform(speed * 0.3, speed)
            self.particles.append([px, py, math.cos(a) * v, math.sin(a) * v - 30,
                                   random.uniform(0.4, 0.9), color, random.randint(2, 4)])

    def fx_update(self, dt):
        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 380 * dt
            p[4] -= dt
        self.particles = [p for p in self.particles if p[4] > 0]
        for pop in self.popups:
            pop[1] += dt
        self.popups = [p for p in self.popups if p[1] < 1.2]
        self.shake = max(0.0, self.shake - 40 * dt)

    # --- lógica por frame
    def update(self, dt):
        self.fx_update(dt)
        if self.over or self.paused:
            return
        if self.state == "clearing":
            self.clear_t += dt
            if self.clear_t >= 0.38:
                self.finish_clear()
            return

        keys = pygame.key.get_pressed()
        if self.dir == -1 and not keys[pygame.K_LEFT]:
            self.dir = 1 if keys[pygame.K_RIGHT] else 0
        if self.dir == 1 and not keys[pygame.K_RIGHT]:
            self.dir = -1 if keys[pygame.K_LEFT] else 0
        if self.dir:
            self.das_t += dt
            if self.das_t > 0.17:
                self.arr_t += dt
                while self.arr_t >= 0.045:
                    self.arr_t -= 0.045
                    self.move(self.dir, 0)

        soft = keys[pygame.K_DOWN]
        base = max(0.04, (0.8 - (self.level - 1) * 0.007) ** (self.level - 1))
        interval = min(base, 0.035) if soft else base
        self.fall_t += dt
        while self.fall_t >= interval and self.cur:
            self.fall_t -= interval
            if self.move(0, 1):
                if soft:
                    self.score += 1
            else:
                self.lock()
                break

    def key_down(self, key):
        if key == pygame.K_p and not self.over:
            self.paused = not self.paused
            return
        if self.over or self.paused or self.state != "play":
            return
        if key == pygame.K_LEFT:
            self.dir, self.das_t, self.arr_t = -1, 0.0, 0.0
            self.move(-1, 0)
        elif key == pygame.K_RIGHT:
            self.dir, self.das_t, self.arr_t = 1, 0.0, 0.0
            self.move(1, 0)
        elif key in (pygame.K_UP, pygame.K_x):
            self.rotate(True)
        elif key == pygame.K_z:
            self.rotate(False)
        elif key == pygame.K_SPACE:
            self.hard_drop()
        elif key == pygame.K_c:
            self.do_hold()


# ----------------------------------------------------------------- UI
class Renderer:
    def __init__(self, screen):
        self.s = screen
        self.bg = make_background()
        self.glow, self.glow_pad = make_glow()
        self.stars = [[random.uniform(0, WIDTH), random.uniform(0, HEIGHT),
                       random.uniform(6, 22), random.uniform(0, math.tau)] for _ in range(70)]
        pick = lambda names, size, bold=True: pygame.font.SysFont(names, size, bold=bold)
        names = "segoeui,helveticaneue,arial,dejavusans"
        self.f_title = pick(names, 34)
        self.f_big = pick(names, 28)
        self.f_med = pick(names, 20)
        self.f_small = pick(names, 13, False)
        self.f_label = pick(names, 13)

    def text(self, s, font, color, pos, anchor="topleft", shadow=True):
        if shadow:
            sh = font.render(s, True, (0, 0, 0))
            r = sh.get_rect(**{anchor: (pos[0] + 2, pos[1] + 2)})
            sh.set_alpha(120)
            self.s.blit(sh, r)
        img = font.render(s, True, color)
        self.s.blit(img, img.get_rect(**{anchor: pos}))

    def panel(self, rect, label):
        surf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (255, 255, 255, 16), surf.get_rect(), border_radius=14)
        pygame.draw.rect(surf, (255, 255, 255, 46), surf.get_rect(), width=1, border_radius=14)
        self.s.blit(surf, rect.topleft)
        self.text(label, self.f_label, (160, 172, 220), (rect.centerx, rect.y + 14),
                  "midtop", shadow=False)

    def mini(self, kind, cx, cy, size=22, alpha=255):
        m = SHAPES[kind]
        cells = [(c, r) for r, row in enumerate(m) for c, v in enumerate(row) if v]
        minc, maxc = min(c for c, _ in cells), max(c for c, _ in cells)
        minr, maxr = min(r for _, r in cells), max(r for _, r in cells)
        w, h = (maxc - minc + 1) * size, (maxr - minr + 1) * size
        ox, oy = cx - w // 2, cy - h // 2
        surf = block_surface(kind, size)
        if alpha != 255:
            surf = surf.copy()
            surf.set_alpha(alpha)
        for c, r in cells:
            self.s.blit(surf, (ox + (c - minc) * size, oy + (r - minr) * size))

    def draw_stars(self, dt):
        for st in self.stars:
            st[1] += st[2] * dt
            st[3] += dt * 2
            if st[1] > HEIGHT:
                st[0], st[1] = random.uniform(0, WIDTH), -2
            b = int(90 + 70 * math.sin(st[3]))
            pygame.draw.circle(self.s, (b, b, min(255, b + 40)), (int(st[0]), int(st[1])), 1)

    def draw(self, g, dt):
        s = self.s
        s.blit(self.bg, (0, 0))
        self.draw_stars(dt)

        self.text("T E T R I S", self.f_title, (235, 238, 255),
                  (BOARD_X + BOARD_W // 2, 8), "midtop")

        # --- panel izquierdo: HOLD + stats
        lx, lw = 30, 170
        hold_r = pygame.Rect(lx, BOARD_Y, lw, 120)
        self.panel(hold_r, "GUARDAR  (C)")
        if g.hold:
            self.mini(g.hold, hold_r.centerx, hold_r.centery + 12, 24,
                      255 if g.can_hold else 90)

        for i, (label, val) in enumerate((("PUNTOS", g.score), ("LÍNEAS", g.lines), ("NIVEL", g.level))):
            r = pygame.Rect(lx, BOARD_Y + 140 + i * 82, lw, 70)
            self.panel(r, label)
            self.text(f"{val:,}".replace(",", "."), self.f_big, (255, 255, 255),
                      (r.centerx, r.y + 42), "center")

        # --- panel derecho: siguientes
        rx = BOARD_X + BOARD_W + 30
        next_r = pygame.Rect(rx, BOARD_Y, lw, 300)
        self.panel(next_r, "SIGUIENTE")
        for i, k in enumerate(g.queue):
            self.mini(k, next_r.centerx, next_r.y + 85 + i * 90, 24 if i == 0 else 20)

        help_lines = ["← →  mover", "↑ X  rotar", "Z  rotar inverso", "↓  bajada suave",
                      "ESPACIO  caída", "C  guardar", "P  pausa"]
        for i, line in enumerate(help_lines):
            self.text(line, self.f_small, (150, 160, 200), (rx + 6, BOARD_Y + 330 + i * 21),
                      shadow=False)

        # --- tablero
        ox = BOARD_X + (random.uniform(-g.shake, g.shake) if g.shake else 0)
        oy = BOARD_Y + (random.uniform(-g.shake, g.shake) if g.shake else 0)
        s.blit(self.glow, (BOARD_X - self.glow_pad, BOARD_Y - self.glow_pad))
        board = pygame.Rect(ox, oy, BOARD_W, BOARD_H)
        bsurf = pygame.Surface(board.size, pygame.SRCALPHA)
        pygame.draw.rect(bsurf, (6, 8, 22, 215), bsurf.get_rect(), border_radius=8)
        for c in range(1, COLS):
            pygame.draw.line(bsurf, (255, 255, 255, 10), (c * CELL, 0), (c * CELL, BOARD_H))
        for r in range(1, ROWS):
            pygame.draw.line(bsurf, (255, 255, 255, 10), (0, r * CELL), (BOARD_W, r * CELL))
        s.blit(bsurf, board.topleft)

        # piezas fijas
        for r in range(ROWS):
            for c in range(COLS):
                k = g.grid[r][c]
                if k:
                    s.blit(block_surface(k, CELL), (ox + c * CELL, oy + r * CELL))

        # fantasma + pieza actual
        if g.cur and not g.over:
            gy = g.ghost_y()
            col = COLORS[g.cur.kind]
            for x, y in g.cur.cells(y=gy):
                if y >= 0:
                    rr = pygame.Rect(ox + x * CELL + 3, oy + y * CELL + 3, CELL - 6, CELL - 6)
                    pygame.draw.rect(s, col, rr, width=2, border_radius=6)
            for x, y in g.cur.cells():
                if y >= 0:
                    s.blit(block_surface(g.cur.kind, CELL), (ox + x * CELL, oy + y * CELL))

        # parpadeo al limpiar
        if g.state == "clearing":
            a = int(60 + 195 * abs(math.sin(g.clear_t * math.pi * 5)))
            flash = pygame.Surface((BOARD_W, CELL), pygame.SRCALPHA)
            flash.fill((255, 255, 255, a))
            for r in g.clear_rows:
                s.blit(flash, (ox, oy + r * CELL))

        # partículas
        for p in g.particles:
            a = max(0, min(255, int(p[4] * 400)))
            dot = pygame.Surface((p[6] * 2, p[6] * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot, (*p[5], a), (p[6], p[6]), p[6])
            s.blit(dot, (ox + p[0] - p[6], oy + p[1] - p[6]))

        # textos flotantes
        for text, t in g.popups:
            alpha = max(0, int(255 * (1 - t / 1.2)))
            img = self.f_big.render(text, True, (255, 240, 170))
            img.set_alpha(alpha)
            s.blit(img, img.get_rect(center=(BOARD_X + BOARD_W // 2, BOARD_Y + 200 - t * 60)))

        # overlays
        if g.paused:
            self.overlay("PAUSA", "pulsa P para continuar")
        elif g.over:
            self.overlay("GAME OVER", f"{g.score:,} puntos".replace(",", "."), "R para reiniciar")

    def overlay(self, title, sub, sub2=None):
        dim = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        pygame.draw.rect(dim, (5, 6, 18, 200), dim.get_rect(), border_radius=8)
        self.s.blit(dim, (BOARD_X, BOARD_Y))
        cx, cy = BOARD_X + BOARD_W // 2, BOARD_Y + BOARD_H // 2
        self.text(title, self.f_title, (255, 255, 255), (cx, cy - 30), "center")
        self.text(sub, self.f_med, (190, 200, 240), (cx, cy + 14), "center")
        if sub2:
            self.text(sub2, self.f_small, (150, 160, 200), (cx, cy + 46), "center")


# ----------------------------------------------------------------- main
def main():
    pygame.init()
    pygame.display.set_caption("Tetris")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    game = Game()
    renderer = Renderer(screen)

    while True:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if e.key == pygame.K_r:
                    game.reset()
                else:
                    game.key_down(e.key)
        game.update(dt)
        renderer.draw(game, dt)
        pygame.display.flip()


if __name__ == "__main__":
    main()
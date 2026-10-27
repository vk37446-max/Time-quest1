"""TIME QUEST — a small, asset-free arcade survival game."""
import asyncio
import math
import random
import sys
import pygame

WIDTH, HEIGHT = 960, 640
FPS = 60
ROUND_SECONDS = 100
BG = (10, 17, 37)
WHITE = (238, 245, 255)
MUTED = (146, 164, 193)
CYAN = (68, 226, 255)
GOLD = (255, 204, 74)
PINK = (255, 91, 136)


def fit_web_canvas():
    """Scale the browser canvas to fit the viewport without stretching it."""
    if sys.platform == "emscripten":
        import platform as browser
        canvas = browser.window.canvas
        canvas.style.width = "min(100vw, 150vh)"
        canvas.style.height = "auto"
        canvas.style.maxWidth = "100vw"
        canvas.style.maxHeight = "100vh"
        canvas.style.position = "fixed"
        canvas.style.left = "50%"
        canvas.style.top = "50%"
        canvas.style.transform = "translate(-50%, -50%)"
        canvas.style.touchAction = "none"
        browser.document.body.style.margin = "0"
        browser.document.body.style.overflow = "hidden"
        browser.document.body.style.backgroundColor = "#0a1125"


def text(surface, value, font, color, pos, center=False):
    image = font.render(str(value), True, color)
    rect = image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
    surface.blit(image, rect)


def glow(surface, pos, radius, color, core=None):
    layer = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
    cx = cy = radius * 2
    for r, alpha in ((radius * 2, 15), (int(radius * 1.5), 25), (radius, 45)):
        pygame.draw.circle(layer, (*color, alpha), (cx, cy), r)
    pygame.draw.circle(layer, (*(core or color), 255), (cx, cy), max(3, radius // 3))
    surface.blit(layer, (int(pos[0] - cx), int(pos[1] - cy)))


class Orb:
    def __init__(self, arena):
        self.arena = arena
        self.respawn()

    def respawn(self):
        pad = 35
        self.x = random.randint(self.arena.left + pad, self.arena.right - pad)
        self.y = random.randint(self.arena.top + pad, self.arena.bottom - pad)
        self.radius = 12
        self.phase = random.random() * math.tau

    def draw(self, screen, t):
        y = self.y + math.sin(t * 3 + self.phase) * 4
        glow(screen, (self.x, y), 20, GOLD, (255, 237, 151))
        pygame.draw.circle(screen, (255, 247, 197), (int(self.x), int(y)), 4)


class Hazard:
    def __init__(self, arena, speed):
        self.arena = arena
        self.r = random.randint(14, 21)
        self.x = random.randint(arena.left + 30, arena.right - 30)
        self.y = random.randint(arena.top + 30, arena.bottom - 30)
        angle = random.random() * math.tau
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.spin = random.random() * math.tau

    def update(self, dt, speed):
        scale = 1 + min(speed / 300, .35)
        self.x += self.vx * scale * dt
        self.y += self.vy * scale * dt
        if self.x < self.arena.left + self.r or self.x > self.arena.right - self.r:
            self.vx *= -1
        if self.y < self.arena.top + self.r or self.y > self.arena.bottom - self.r:
            self.vy *= -1
        self.x = max(self.arena.left + self.r, min(self.arena.right - self.r, self.x))
        self.y = max(self.arena.top + self.r, min(self.arena.bottom - self.r, self.y))
        self.spin += dt * 2

    def draw(self, screen):
        glow(screen, (self.x, self.y), self.r + 13, PINK, (255, 102, 151))
        points = []
        for i in range(8):
            a = self.spin + i * math.tau / 8
            r = self.r if i % 2 == 0 else self.r * .58
            points.append((int(self.x + math.cos(a) * r), int(self.y + math.sin(a) * r)))
        pygame.draw.polygon(screen, (255, 127, 161), points)
        pygame.draw.circle(screen, (255, 219, 229), (int(self.x), int(self.y)), 4)


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("TIME QUEST — Arcade Survival")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        fit_web_canvas()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("segoeui", 22)
        self.small = pygame.font.SysFont("segoeui", 16)
        self.medium = pygame.font.SysFont("segoeui", 30, bold=True)
        self.big = pygame.font.SysFont("segoeui", 64, bold=True)
        self.arena = pygame.Rect(70, 112, 820, 470)
        self.stars = [(random.randrange(WIDTH), random.randrange(HEIGHT), random.choice((1, 1, 2))) for _ in range(100)]
        self.state = "title"
        self.pointer_active = False
        self.pointer_target = None
        self.best = 0
        self.reset()

    def reset(self):
        self.player = pygame.Vector2(WIDTH / 2, HEIGHT / 2)
        self.score = 0
        self.lives = 3
        self.elapsed = 0.0
        self.invuln = 0.0
        self.orb = Orb(self.arena)
        self.hazards = [Hazard(self.arena, 105)]
        self.spawn_at = 0

    def start(self):
        self.reset()
        self.state = "playing"

    def update(self, dt):
        if self.state != "playing":
            return
        self.elapsed += dt
        self.invuln = max(0, self.invuln - dt)
        if self.elapsed >= ROUND_SECONDS or self.lives <= 0:
            self.state = "over"
            self.best = max(self.best, self.score)
            return
        keys = pygame.key.get_pressed()
        move = pygame.Vector2(int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT]),
                              int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP]))
        if not move.length_squared() and self.pointer_active and self.pointer_target is not None:
            target = pygame.Vector2(
                max(self.arena.left + 16, min(self.arena.right - 16, self.pointer_target.x)),
                max(self.arena.top + 16, min(self.arena.bottom - 16, self.pointer_target.y)),
            )
            delta = target - self.player
            if delta.length_squared() > 64:
                move = delta.normalize()
        if move.length_squared():
            move = move.normalize()
        speed = 280
        self.player += move * speed * dt
        self.player.x = max(self.arena.left + 16, min(self.arena.right - 16, self.player.x))
        self.player.y = max(self.arena.top + 16, min(self.arena.bottom - 16, self.player.y))
        difficulty = min(self.elapsed / ROUND_SECONDS, 1)
        self.spawn_at += dt
        spawn_interval = max(4.2, 12 - self.elapsed * .075)
        if self.spawn_at >= spawn_interval and len(self.hazards) < 9:
            self.spawn_at = 0
            self.hazards.append(Hazard(self.arena, 105 + self.elapsed * 1.25))
        for hazard in self.hazards:
            hazard.update(dt, 105 + self.elapsed * 1.25)
            if self.invuln <= 0 and self.player.distance_to((hazard.x, hazard.y)) < hazard.r + 15:
                self.lives -= 1
                self.invuln = 1.5
                if self.lives > 0:
                    self.player.update(WIDTH / 2, HEIGHT / 2)
        if self.player.distance_to((self.orb.x, self.orb.y)) < 27:
            self.score += 10 + int(self.elapsed // 20) * 2
            self.orb.respawn()

    def draw_background(self):
        self.screen.fill(BG)
        for x, y, r in self.stars:
            pygame.draw.circle(self.screen, (37, 55, 84), (x, y), r)
        pygame.draw.rect(self.screen, (17, 28, 55), self.arena, border_radius=18)
        pygame.draw.rect(self.screen, (45, 80, 119), self.arena, 2, border_radius=18)
        for x in range(self.arena.left + 30, self.arena.right, 40):
            pygame.draw.line(self.screen, (20, 37, 66), (x, self.arena.top + 2), (x, self.arena.bottom - 2), 1)
        for y in range(self.arena.top + 30, self.arena.bottom, 40):
            pygame.draw.line(self.screen, (20, 37, 66), (self.arena.left + 2, y), (self.arena.right - 2, y), 1)

    def draw_hud(self):
        text(self.screen, "TIME QUEST", self.medium, CYAN, (72, 30))
        text(self.screen, "SCORE", self.small, MUTED, (360, 28))
        text(self.screen, self.score, self.medium, WHITE, (360, 48))
        left = max(0, math.ceil(ROUND_SECONDS - self.elapsed))
        color = PINK if left <= 15 and self.state == "playing" else WHITE
        text(self.screen, f"{left:02d}", self.medium, color, (510, 36))
        text(self.screen, "SECONDS", self.small, MUTED, (552, 50))
        for i in range(3):
            c = PINK if i < self.lives else (52, 58, 78)
            pygame.draw.circle(self.screen, c, (790 + i * 28, 51), 9)
        text(self.screen, "LIVES", self.small, MUTED, (790, 27))

    def draw_player(self, t):
        if self.invuln > 0 and int(t * 12) % 2 == 0:
            return
        glow(self.screen, self.player, 24, CYAN, (92, 245, 255))
        x, y = map(int, self.player)
        pygame.draw.circle(self.screen, (107, 244, 255), (x, y), 13)
        pygame.draw.circle(self.screen, (224, 255, 255), (x, y), 7)
        pygame.draw.circle(self.screen, (16, 81, 119), (x + 2, y - 1), 3)

    def overlay(self, heading, subheading, lines):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((4, 9, 24, 190))
        self.screen.blit(veil, (0, 0))
        text(self.screen, heading, self.big, CYAN, (WIDTH // 2, 205), center=True)
        text(self.screen, subheading, self.font, WHITE, (WIDTH // 2, 267), center=True)
        for i, line in enumerate(lines):
            text(self.screen, line, self.font if i == len(lines) - 1 else self.small,
                 GOLD if i == len(lines) - 1 else MUTED, (WIDTH // 2, 335 + i * 34), center=True)

    def draw_touch_target(self):
        if self.pointer_active and self.pointer_target is not None and self.state == "playing":
            point = (int(self.pointer_target.x), int(self.pointer_target.y))
            pygame.draw.circle(self.screen, (113, 235, 255), point, 18, 2)
            pygame.draw.circle(self.screen, (214, 251, 255), point, 4)

    def draw(self, t):
        self.draw_background()
        self.draw_hud()
        self.orb.draw(self.screen, t)
        for h in self.hazards:
            h.draw(self.screen)
        self.draw_player(t)
        if self.state == "title":
            self.overlay("TIME QUEST", "A 100-second arcade survival run", [
                "Phone: touch and drag anywhere in the arena to steer", "Computer: use WASD or the arrow keys", "Collect gold orbs. Dodge pink hazards. You have 3 lives.", "TAP ANYWHERE OR PRESS ENTER / SPACE TO PLAY"])
        elif self.state == "over":
            result = "TIME'S UP!" if self.elapsed >= ROUND_SECONDS else "RUN ENDED"
            self.overlay(result, f"Final score: {self.score}     Best this session: {self.best}", [
                "Gold orbs are worth more as the challenge builds.", "Press ESC to quit", "TAP ANYWHERE OR PRESS R / ENTER / SPACE TO PLAY AGAIN"])
        else:
            self.draw_touch_target()
            text(self.screen, "TOUCH & DRAG TO STEER  •  WASD / ARROWS  •  ESC TO QUIT", self.small, (94, 115, 148), (WIDTH // 2, 604), center=True)
        pygame.display.flip()

    async def run(self):
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000, .05)
            t = pygame.time.get_ticks() / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif self.state == "title" and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.start()
                    elif self.state == "over" and event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                        self.start()
                elif event.type == pygame.FINGERDOWN:
                    if self.state != "playing":
                        self.start()
                    self.pointer_active = True
                    self.pointer_target = pygame.Vector2(event.x * WIDTH, event.y * HEIGHT)
                elif event.type == pygame.FINGERMOTION and self.pointer_active:
                    self.pointer_target = pygame.Vector2(event.x * WIDTH, event.y * HEIGHT)
                elif event.type == pygame.FINGERUP:
                    self.pointer_active = False
                    self.pointer_target = None
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state != "playing":
                        self.start()
                    self.pointer_active = True
                    self.pointer_target = pygame.Vector2(event.pos)
                elif event.type == pygame.MOUSEMOTION and self.pointer_active:
                    self.pointer_target = pygame.Vector2(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.pointer_active = False
                    self.pointer_target = None
            self.update(dt)
            self.draw(t)
            await asyncio.sleep(0)
        pygame.quit()


if __name__ == "__main__":
    asyncio.run(Game().run())



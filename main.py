import math
import random
import tkinter as tk


WIDTH = 960
HEIGHT = 600
HALF_HEIGHT = HEIGHT // 2
FOV = math.pi / 3
RAYS = 160
COLUMN_WIDTH = WIDTH / RAYS
MOVE_SPEED = 2.7
TURN_SPEED = 0.055

WALL_COLORS = {"1": "#682f2f", "2": "#3f4f72", "3": "#735a31"}
MAP = [
    "1111111111111111",
    "1..............1",
    "1..111...22....1",
    "1........2.....1",
    "1........2.....1",
    "1..33...22.....1",
    "1..3...........1",
    "1..3..1111.....1",
    "1......1.......1",
    "1......1...33..1",
    "1..........3...1",
    "1..............1",
    "1111111111111111",
]

# Alias satiricos de figuras publicas; los retratos se dibujan geometricamente.
ENEMY_TYPES = [
    {"name": "Boric", "color": "#c45d4b", "hair": "#3a2020"},
    {"name": "Bachelet", "color": "#d98972", "hair": "#6b392b"},
    {"name": "Pinera", "color": "#b97250", "hair": "#d7d4c5"},
    {"name": "Allende", "color": "#b46b45", "hair": "#242424"},
    {"name": "Senador", "color": "#c77d58", "hair": "#3b2822"},
]


class DoomPapiMickey:
    def __init__(self, root):
        self.root = root
        self.root.title("Papi Mickey: Pasillos del Poder")
        self.root.resizable(False, False)
        self.root.configure(bg="#090b12")
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#111522", highlightthickness=0)
        self.canvas.pack()
        self.root.bind("<KeyPress>", self.key_down)
        self.root.bind("<KeyRelease>", self.key_up)
        self.keys = set()
        self.reset()
        self.last_time = self.root.tk.call("after", "info")
        self.root.after(30, self.loop)

    def reset(self):
        self.player = [2.0, 2.0, 0.0]
        self.health = 100
        self.score = 0
        self.paused = False
        self.game_over = False
        self.won = False
        self.flash = 0
        self.shake = 0
        self.enemies = []
        spawn_points = [(6.5, 2.0), (12.5, 2.5), (4.5, 5.5), (11.5, 8.5), (13.0, 10.5)]
        for point, profile in zip(spawn_points, ENEMY_TYPES):
            self.enemies.append({"x": point[0], "y": point[1], "profile": profile, "alive": True, "cooldown": 0})
        self.keys.clear()
        self.render()

    def key_down(self, event):
        key = event.keysym.lower()
        if key == "r":
            self.reset()
        elif key == "p" and not self.game_over and not self.won:
            self.paused = not self.paused
        elif key == "space" and not self.paused and not self.game_over and not self.won:
            self.shoot()
        else:
            self.keys.add(key)

    def key_up(self, event):
        self.keys.discard(event.keysym.lower())

    def loop(self):
        if not self.paused and not self.game_over and not self.won:
            self.update()
        self.render()
        self.root.after(30, self.loop)

    def is_wall(self, x, y):
        grid_x, grid_y = int(x), int(y)
        return grid_y < 0 or grid_y >= len(MAP) or grid_x < 0 or grid_x >= len(MAP[0]) or MAP[grid_y][grid_x] != "."

    def try_move(self, x, y):
        radius = 0.18
        if not self.is_wall(x + radius, y) and not self.is_wall(x - radius, y):
            self.player[0] = x
        if not self.is_wall(self.player[0], y + radius) and not self.is_wall(self.player[0], y - radius):
            self.player[1] = y

    def update(self):
        if "left" in self.keys:
            self.player[2] -= TURN_SPEED
        if "right" in self.keys:
            self.player[2] += TURN_SPEED
        forward = int("w" in self.keys) - int("s" in self.keys)
        strafe = int("d" in self.keys) - int("a" in self.keys)
        if forward or strafe:
            angle = self.player[2]
            dx = (math.cos(angle) * forward - math.sin(angle) * strafe) * MOVE_SPEED * 0.03
            dy = (math.sin(angle) * forward + math.cos(angle) * strafe) * MOVE_SPEED * 0.03
            self.try_move(self.player[0] + dx, self.player[1] + dy)

        for enemy in self.enemies:
            if not enemy["alive"]:
                continue
            enemy["cooldown"] = max(0, enemy["cooldown"] - 1)
            distance = math.hypot(enemy["x"] - self.player[0], enemy["y"] - self.player[1])
            if distance < 0.85 and enemy["cooldown"] == 0:
                self.health -= 8
                enemy["cooldown"] = 35
                self.shake = 5
                if self.health <= 0:
                    self.game_over = True

        if self.flash:
            self.flash -= 1
        if self.shake:
            self.shake -= 1
        if all(not enemy["alive"] for enemy in self.enemies):
            self.won = True

    def shoot(self):
        self.flash = 3
        best = None
        best_distance = 999
        for enemy in self.enemies:
            if not enemy["alive"]:
                continue
            dx = enemy["x"] - self.player[0]
            dy = enemy["y"] - self.player[1]
            distance = math.hypot(dx, dy)
            relative = math.atan2(math.sin(math.atan2(dy, dx) - self.player[2]), math.cos(math.atan2(dy, dx) - self.player[2]))
            if abs(relative) < 0.10 and distance < best_distance and not self.wall_between(enemy["x"], enemy["y"]):
                best = enemy
                best_distance = distance
        if best:
            best["alive"] = False
            self.score += 100

    def wall_between(self, target_x, target_y):
        distance = math.hypot(target_x - self.player[0], target_y - self.player[1])
        steps = max(1, int(distance * 12))
        for step in range(1, steps):
            ratio = step / steps
            x = self.player[0] + (target_x - self.player[0]) * ratio
            y = self.player[1] + (target_y - self.player[1]) * ratio
            if self.is_wall(x, y):
                return True
        return False

    def render(self):
        self.canvas.delete("all")
        offset = random.randint(-self.shake, self.shake) if self.shake else 0
        self.canvas.create_rectangle(0, 0, WIDTH, HALF_HEIGHT + offset, fill="#161d34", outline="")
        self.canvas.create_rectangle(0, HALF_HEIGHT + offset, WIDTH, HEIGHT, fill="#251c22", outline="")
        self.canvas.create_rectangle(0, HALF_HEIGHT - 2 + offset, WIDTH, HALF_HEIGHT + 2 + offset, fill="#b18153", outline="")

        z_buffer = []
        for ray in range(RAYS):
            camera_x = 2 * ray / RAYS - 1
            ray_angle = self.player[2] + math.atan(camera_x * math.tan(FOV / 2))
            distance = self.cast_ray(ray_angle)
            corrected = max(0.1, distance * math.cos(ray_angle - self.player[2]))
            wall_height = min(HEIGHT * 2, HEIGHT / corrected)
            x1 = int(ray * COLUMN_WIDTH)
            x2 = int((ray + 1) * COLUMN_WIDTH) + 1
            shade = max(0.25, 1 - corrected / 10)
            color = self.shade(WALL_COLORS.get(self.wall_at(ray_angle), "#555555"), shade)
            self.canvas.create_rectangle(x1, HALF_HEIGHT - wall_height / 2 + offset, x2, HALF_HEIGHT + wall_height / 2 + offset, fill=color, outline="")
            z_buffer.append(corrected)

        visible_enemies = []
        for enemy in self.enemies:
            if enemy["alive"]:
                dx = enemy["x"] - self.player[0]
                dy = enemy["y"] - self.player[1]
                distance = math.hypot(dx, dy)
                relative = math.atan2(math.sin(math.atan2(dy, dx) - self.player[2]), math.cos(math.atan2(dy, dx) - self.player[2]))
                if abs(relative) < FOV * 0.7 and not self.wall_between(enemy["x"], enemy["y"]):
                    visible_enemies.append((distance, relative, enemy))
        for distance, relative, enemy in sorted(visible_enemies, reverse=True):
            screen_x = WIDTH / 2 + math.tan(relative) / math.tan(FOV / 2) * WIDTH / 2
            size = min(270, HEIGHT / max(0.25, distance) * 0.55)
            self.draw_enemy(screen_x, HALF_HEIGHT + offset, size, enemy["profile"])

        self.draw_weapon(offset)
        self.draw_hud()
        if self.paused:
            self.message("PAUSA", "P = continuar")
        elif self.game_over:
            self.message("PAPI MICKEY HA CAIDO", "R = reiniciar")
        elif self.won:
            self.message("PASILLO DESPEJADO", "R = jugar otra vez")

    def cast_ray(self, angle):
        distance = 0.0
        while distance < 20:
            distance += 0.04
            if self.is_wall(self.player[0] + math.cos(angle) * distance, self.player[1] + math.sin(angle) * distance):
                return distance
        return 20

    def wall_at(self, angle):
        distance = self.cast_ray(angle)
        x = int(self.player[0] + math.cos(angle) * distance)
        y = int(self.player[1] + math.sin(angle) * distance)
        return MAP[y][x] if 0 <= y < len(MAP) and 0 <= x < len(MAP[0]) else "1"

    @staticmethod
    def shade(color, factor):
        color = color.lstrip("#")
        rgb = [int(color[index:index + 2], 16) for index in (0, 2, 4)]
        return "#" + "".join(f"{max(0, min(255, int(value * factor))):02x}" for value in rgb)

    def draw_enemy(self, x, center_y, size, profile):
        left = x - size * 0.32
        right = x + size * 0.32
        top = center_y - size * 0.55
        bottom = center_y + size * 0.45
        self.canvas.create_rectangle(left, top, right, bottom, fill="#20151a", outline="#0a0b10", width=3)
        self.canvas.create_oval(x - size * 0.25, top, x + size * 0.25, top + size * 0.62, fill=profile["color"], outline="#161014", width=2)
        self.canvas.create_arc(x - size * 0.25, top - size * 0.08, x + size * 0.25, top + size * 0.35, start=0, extent=180, fill=profile["hair"], outline=profile["hair"])
        eye_y = top + size * 0.3
        self.canvas.create_rectangle(x - size * 0.13, eye_y, x - size * 0.04, eye_y + size * 0.06, fill="#111111", outline="")
        self.canvas.create_rectangle(x + size * 0.04, eye_y, x + size * 0.13, eye_y + size * 0.06, fill="#111111", outline="")
        self.canvas.create_arc(x - size * 0.1, top + size * 0.38, x + size * 0.1, top + size * 0.5, start=180, extent=180, outline="#241317", width=2)
        self.canvas.create_text(x, bottom + 12, text=profile["name"], fill="#f5d6a1", font=("Courier New", max(8, int(size / 13)), "bold"))

    def draw_weapon(self, offset):
        center = WIDTH // 2
        self.canvas.create_polygon(center - 55, HEIGHT, center - 40, HEIGHT - 120 + offset, center + 40, HEIGHT - 120 + offset, center + 55, HEIGHT, fill="#30343c", outline="#090a0d", width=3)
        self.canvas.create_rectangle(center - 25, HEIGHT - 160 + offset, center + 25, HEIGHT - 100 + offset, fill="#aa6b3c", outline="#090a0d", width=3)
        if self.flash:
            self.canvas.create_polygon(center - 16, HEIGHT - 180 + offset, center, HEIGHT - 245 + offset, center + 16, HEIGHT - 180 + offset, fill="#f7d34e", outline="#fff2a3")

    def draw_hud(self):
        self.canvas.create_rectangle(0, 0, WIDTH, 46, fill="#090b12", outline="")
        alive = sum(enemy["alive"] for enemy in self.enemies)
        self.canvas.create_text(18, 23, anchor="w", text="PAPI MICKEY", fill="#f2c66d", font=("Courier New", 16, "bold"))
        self.canvas.create_text(WIDTH - 18, 16, anchor="e", text=f"VIDA {max(0, self.health)}   PUNTOS {self.score}", fill="#f5f1dc", font=("Courier New", 11, "bold"))
        self.canvas.create_text(WIDTH - 18, 33, anchor="e", text=f"OBJETIVOS: {alive}", fill="#cc8f8f", font=("Courier New", 9, "bold"))
        self.canvas.create_text(18, HEIGHT - 16, anchor="w", text="WASD MOVER  FLECHAS GIRAR  ESPACIO DISPARAR  P PAUSA  R REINICIAR", fill="#e3c99c", font=("Courier New", 9, "bold"))

    def message(self, title, subtitle):
        self.canvas.create_rectangle(230, 230, WIDTH - 230, 370, fill="#090b12", outline="#c58c54", width=3)
        self.canvas.create_text(WIDTH // 2, 275, text=title, fill="#f2c66d", font=("Courier New", 21, "bold"))
        self.canvas.create_text(WIDTH // 2, 320, text=subtitle, fill="#f5f1dc", font=("Courier New", 12, "bold"))


def main():
    root = tk.Tk()
    DoomPapiMickey(root)
    root.mainloop()


if __name__ == "__main__":
    main()

import math
import random
import tkinter as tk
from pathlib import Path

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


WIDTH = 960
HEIGHT = 600
HALF_HEIGHT = HEIGHT // 2
FOV = math.pi / 3
RAYS = 160
COLUMN_WIDTH = WIDTH / RAYS
MOVE_SPEED = 2.7
TURN_SPEED = 0.055
LEVEL_START_ENEMIES = 2

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
    {"name": "Boric", "image": "boric.png", "color": "#c45d4b", "hair": "#3a2020"},
    {"name": "Bachelet", "image": "bachelet.png", "color": "#d98972", "hair": "#6b392b"},
    {"name": "Pinera", "image": "pinera.png", "color": "#b97250", "hair": "#d7d4c5"},
    {"name": "Allende", "image": "allende.png", "color": "#b46b45", "hair": "#242424"},
    {"name": "Senador", "image": "senador.png", "color": "#c77d58", "hair": "#3b2822"},
]

WEAPONS = {
    "Pistola": {"cooldown": 10, "damage": 100, "spread": 0.08, "color": "#b9c0ca"},
    "Escopeta": {"cooldown": 24, "damage": 150, "spread": 0.18, "color": "#d98f4d"},
    "Rafaga": {"cooldown": 5, "damage": 55, "spread": 0.11, "color": "#6cc4a1"},
}
WEAPON_ORDER = list(WEAPONS)


class DoomPapiMickey:
    def __init__(self, root):
        self.root = root
        self.root.title("Papi Mickey: Pasillos del Poder")
        self.root.resizable(False, False)
        self.root.configure(bg="#090b12")
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg="#111522", highlightthickness=0)
        self.canvas.pack()
        self.enemy_images = self.load_enemy_images()
        self.frame_image_cache = {}
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
        self.level = 1
        self.weapon_inventory = ["Pistola"]
        self.weapon_index = 0
        self.weapon_cooldown = 0
        self.paused = False
        self.game_over = False
        self.won = False
        self.flash = 0
        self.shake = 0
        self.enemies = []
        self.weapon_pickups = []
        self.spawn_level()
        self.keys.clear()
        self.render()

    def spawn_level(self):
        self.player[0], self.player[1] = 2.0, 2.0
        open_cells = [
            (x + 0.5, y + 0.5)
            for y, row in enumerate(MAP)
            for x, tile in enumerate(row)
            if tile == "." and math.hypot(x + 0.5 - self.player[0], y + 0.5 - self.player[1]) > 3
        ]
        random.shuffle(open_cells)
        enemy_count = LEVEL_START_ENEMIES * (2 ** (self.level - 1))
        for index in range(enemy_count):
            point = open_cells[index % len(open_cells)]
            profile = ENEMY_TYPES[index % len(ENEMY_TYPES)]
            self.enemies.append({
                "x": point[0],
                "y": point[1],
                "profile": profile,
                "alive": True,
                "cooldown": 0,
                "speed": 0.018 + self.level * 0.003,
            })

        pickup_count = min(len(WEAPON_ORDER) - 1, 1 + self.level // 2)
        for weapon_name, point in zip(WEAPON_ORDER[1:], open_cells[enemy_count:enemy_count + pickup_count]):
            self.weapon_pickups.append({"x": point[0], "y": point[1], "name": weapon_name, "collected": False})

    def key_down(self, event):
        key = event.keysym.lower()
        if key == "r":
            self.reset()
        elif key == "p" and not self.game_over and not self.won:
            self.paused = not self.paused
        elif key == "space" and not self.paused and not self.game_over and not self.won:
            self.shoot()
        elif key in ("q", "e") and not self.paused and not self.game_over and not self.won:
            self.switch_weapon(-1 if key == "q" else 1)
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
        self.weapon_cooldown = max(0, self.weapon_cooldown - 1)
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
            if distance > 0.8:
                direction_x = (self.player[0] - enemy["x"]) / distance
                direction_y = (self.player[1] - enemy["y"]) / distance
                next_x = enemy["x"] + direction_x * enemy["speed"]
                next_y = enemy["y"] + direction_y * enemy["speed"]
                if not self.is_wall(next_x, enemy["y"]):
                    enemy["x"] = next_x
                if not self.is_wall(enemy["x"], next_y):
                    enemy["y"] = next_y
            if distance < 0.85 and enemy["cooldown"] == 0:
                self.health -= 6 + self.level * 2
                enemy["cooldown"] = max(14, 35 - self.level * 2)
                self.shake = 5
                if self.health <= 0:
                    self.game_over = True

        if self.flash:
            self.flash -= 1
        if self.shake:
            self.shake -= 1
        for pickup in self.weapon_pickups:
            if not pickup["collected"] and math.hypot(pickup["x"] - self.player[0], pickup["y"] - self.player[1]) < 0.65:
                pickup["collected"] = True
                if pickup["name"] not in self.weapon_inventory:
                    self.weapon_inventory.append(pickup["name"])
                self.weapon_index = self.weapon_inventory.index(pickup["name"])
        if all(not enemy["alive"] for enemy in self.enemies):
            self.level += 1
            self.health = min(100, self.health + 25)
            self.enemies = []
            self.weapon_pickups = []
            self.spawn_level()

    def shoot(self):
        if self.weapon_cooldown:
            return
        weapon_name = self.weapon_inventory[self.weapon_index]
        weapon = WEAPONS[weapon_name]
        self.weapon_cooldown = weapon["cooldown"]
        self.flash = 3
        targets = []
        for enemy in self.enemies:
            if not enemy["alive"]:
                continue
            dx = enemy["x"] - self.player[0]
            dy = enemy["y"] - self.player[1]
            distance = math.hypot(dx, dy)
            relative = math.atan2(math.sin(math.atan2(dy, dx) - self.player[2]), math.cos(math.atan2(dy, dx) - self.player[2]))
            if abs(relative) < weapon["spread"] and not self.wall_between(enemy["x"], enemy["y"]):
                targets.append((distance, enemy))
        targets.sort(key=lambda target: target[0])
        max_targets = 3 if weapon_name == "Escopeta" else 1
        for _, enemy in targets[:max_targets]:
            enemy["health"] = enemy.get("health", 100) - weapon["damage"]
            if enemy["health"] <= 0:
                enemy["alive"] = False
                self.score += 100

    def switch_weapon(self, direction):
        if len(self.weapon_inventory) < 2:
            return
        self.weapon_index = (self.weapon_index + direction) % len(self.weapon_inventory)

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
        self.frame_image_cache.clear()
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

        self.draw_pickups(offset)
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

    def load_enemy_images(self):
        images = {}
        if Image is None or ImageTk is None:
            return images

        asset_directory = Path(__file__).with_name("assets") / "enemies"
        for profile in ENEMY_TYPES:
            image_path = asset_directory / profile["image"]
            try:
                with Image.open(image_path) as source:
                    images[profile["name"]] = source.convert("RGBA").copy()
            except (FileNotFoundError, OSError):
                pass
        return images

    def draw_enemy(self, x, center_y, size, profile):
        image = self.enemy_images.get(profile["name"])
        if image is not None and ImageTk is not None:
            image_size = max(1, int(size))
            cache_key = (profile["name"], image_size)
            resized = self.frame_image_cache.get(cache_key)
            if resized is None:
                resized_image = image.resize((image_size, image_size), Image.Resampling.LANCZOS)
                resized = ImageTk.PhotoImage(resized_image)
                self.frame_image_cache[cache_key] = resized
            self.canvas.create_image(x, center_y - size * 0.08, image=resized, anchor="center")
            self.canvas.create_text(x, center_y + size * 0.52, text=profile["name"], fill="#f5d6a1", font=("Courier New", max(8, int(size / 13)), "bold"))
            return

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

    def draw_pickups(self, offset):
        visible_pickups = []
        for pickup in self.weapon_pickups:
            if pickup["collected"]:
                continue
            dx = pickup["x"] - self.player[0]
            dy = pickup["y"] - self.player[1]
            distance = math.hypot(dx, dy)
            relative = math.atan2(math.sin(math.atan2(dy, dx) - self.player[2]), math.cos(math.atan2(dy, dx) - self.player[2]))
            if abs(relative) < FOV * 0.7 and not self.wall_between(pickup["x"], pickup["y"]):
                visible_pickups.append((distance, relative, pickup))
        for distance, relative, pickup in sorted(visible_pickups, reverse=True):
            screen_x = WIDTH / 2 + math.tan(relative) / math.tan(FOV / 2) * WIDTH / 2
            size = min(100, HEIGHT / max(0.25, distance) * 0.18)
            center_y = HALF_HEIGHT + offset + size * 0.4
            color = WEAPONS[pickup["name"]]["color"]
            self.canvas.create_rectangle(screen_x - size * 0.35, center_y - size * 0.2, screen_x + size * 0.35, center_y + size * 0.2, fill=color, outline="#11131a", width=2)
            self.canvas.create_line(screen_x - size * 0.2, center_y - size * 0.2, screen_x + size * 0.2, center_y + size * 0.2, fill="#11131a", width=max(2, int(size / 10)))
            self.canvas.create_text(screen_x, center_y + size * 0.4, text=pickup["name"], fill="#f5d6a1", font=("Courier New", max(8, int(size / 9)), "bold"))

    def draw_weapon(self, offset):
        center = WIDTH // 2
        weapon_name = self.weapon_inventory[self.weapon_index]
        weapon_color = WEAPONS[weapon_name]["color"]
        barrel_width = 65 if weapon_name == "Escopeta" else 40
        self.canvas.create_polygon(center - barrel_width, HEIGHT, center - barrel_width * 0.7, HEIGHT - 120 + offset, center + barrel_width * 0.7, HEIGHT - 120 + offset, center + barrel_width, HEIGHT, fill="#30343c", outline="#090a0d", width=3)
        self.canvas.create_rectangle(center - 25, HEIGHT - 160 + offset, center + 25, HEIGHT - 100 + offset, fill="#aa6b3c", outline="#090a0d", width=3)
        self.canvas.create_rectangle(center - 30, HEIGHT - 190 + offset, center + 30, HEIGHT - 175 + offset, fill=weapon_color, outline="#090a0d", width=2)
        if self.flash:
            self.canvas.create_polygon(center - 16, HEIGHT - 180 + offset, center, HEIGHT - 245 + offset, center + 16, HEIGHT - 180 + offset, fill="#f7d34e", outline="#fff2a3")

    def draw_hud(self):
        self.canvas.create_rectangle(0, 0, WIDTH, 46, fill="#090b12", outline="")
        alive = sum(enemy["alive"] for enemy in self.enemies)
        weapon_name = self.weapon_inventory[self.weapon_index]
        inventory = " | ".join(
            f"[{name}]" if index == self.weapon_index else name
            for index, name in enumerate(self.weapon_inventory)
        )
        self.canvas.create_text(18, 23, anchor="w", text="PAPI MICKEY", fill="#f2c66d", font=("Courier New", 16, "bold"))
        self.canvas.create_text(WIDTH - 18, 13, anchor="e", text=f"NIVEL {self.level}   VIDA {max(0, self.health)}   PUNTOS {self.score}", fill="#f5f1dc", font=("Courier New", 10, "bold"))
        self.canvas.create_text(WIDTH - 18, 30, anchor="e", text=f"OBJETIVOS: {alive}   ARMA: {weapon_name}", fill="#cc8f8f", font=("Courier New", 9, "bold"))
        self.canvas.create_text(18, HEIGHT - 28, anchor="w", text=f"ARMAS {inventory}", fill="#b9d7c2", font=("Courier New", 9, "bold"))
        self.canvas.create_text(18, HEIGHT - 12, anchor="w", text="WASD MOVER  FLECHAS GIRAR  ESPACIO DISPARAR  Q/E CAMBIAR  P PAUSA  R REINICIAR", fill="#e3c99c", font=("Courier New", 8, "bold"))

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

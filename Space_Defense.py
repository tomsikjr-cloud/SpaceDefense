"""
Space Tower Defense - Graphical Version
A tower defense game with simple graphics and space-themed enemies.

Changes in this version:
- EMP is now an area-of-effect shockwave that damages all enemies in range.
- EMP radius is easy to tune using EMP_RADIUS_SQUARES.
- Laser range is easy to tune using LASER_RANGE_SQUARES.
- Tower stats are centralized in DEFENSE_STATS.
- Effects are separated from damage logic: LaserBeam and EMPShockwave.
- Several loops were cleaned up to avoid removing items while iterating.
"""

import json
import math
import os
import random
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

import pygame


# Initialize Pygame
pygame.init()

# Window/grid constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 700
HUD_HEIGHT = 80
GAME_HEIGHT = WINDOW_HEIGHT - HUD_HEIGHT
GRID_SIZE = 40
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = GAME_HEIGHT // GRID_SIZE
FPS = 60

# Files
HIGH_SCORE_FILE = "highscore.json"
LEVELS_FILE = "levels.json"

# Gameplay tuning - change these first when balancing.
LASER_RANGE_SQUARES = 4          # 3 grid squares = 120 pixels
EMP_RADIUS_SQUARES = 3           # surrounding 2-square radius = 80 pixels
LASER_RANGE = LASER_RANGE_SQUARES * GRID_SIZE
EMP_RADIUS = EMP_RADIUS_SQUARES * GRID_SIZE
LASER_BEAM_DURATION = 0.12
EMP_SHOCKWAVE_DURATION = 0.35

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BLUE = (25, 25, 112)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
PURPLE = (200, 50, 200)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (60, 60, 60)


class DefenseType(Enum):
    LASER = 1
    EMP = 2


class EnemyType(Enum):
    FIGHTER = 1  # Fast, weak
    TANK = 2     # Slow, armored


DEFENSE_STATS = {
    DefenseType.LASER: {
        "cost": 150,
        "damage": 25,
        "range": LASER_RANGE,
        "max_charge": 15,
        "label": "LASER",
        "description": f"Single target, {LASER_RANGE_SQUARES}-square range",
    },
    DefenseType.EMP: {
        "cost": 200,
        "damage": 50,
        "range": EMP_RADIUS,
        "max_charge": 50,
        "label": "EMP",
        "description": f"AoE shockwave, {EMP_RADIUS_SQUARES}-square radius",
    },
}

REWARD_PER_KILL = {
    EnemyType.FIGHTER: 25,
    EnemyType.TANK: 50,
}


@dataclass
class Vector2:
    x: float
    y: float

    def __add__(self, other: "Vector2") -> "Vector2":
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector2") -> "Vector2":
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vector2":
        return Vector2(self.x * scalar, self.y * scalar)

    def distance_squared_to(self, other: "Vector2") -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        return dx * dx + dy * dy

    def distance_to(self, other: "Vector2") -> float:
        return math.sqrt(self.distance_squared_to(other))

    def as_int_tuple(self) -> Tuple[int, int]:
        return int(self.x), int(self.y)


def grid_center(grid_x: int, grid_y: int) -> Vector2:
    return Vector2(
        grid_x * GRID_SIZE + GRID_SIZE // 2,
        grid_y * GRID_SIZE + GRID_SIZE // 2,
    )


def in_range(source: Vector2, target: Vector2, radius: float) -> bool:
    return source.distance_squared_to(target) <= radius * radius


class Asteroid:
    def __init__(self, x: int, y: int):
        self.grid_x = x
        self.grid_y = y
        self.position = grid_center(x, y)
        self.radius = 12

    def collides_with_point(self, point: Vector2) -> bool:
        return self.position.distance_squared_to(point) < (self.radius + 8) ** 2

    def draw(self, surface: pygame.Surface):
        x, y = self.position.as_int_tuple()
        pygame.draw.circle(surface, DARK_GRAY, (x, y), self.radius, 2)
        pygame.draw.circle(surface, DARK_GRAY, (x - 4, y - 4), 2)
        pygame.draw.circle(surface, DARK_GRAY, (x + 4, y + 4), 2)


class Defense:
    def __init__(self, grid_x: int, grid_y: int, defense_type: DefenseType):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.defense_type = defense_type
        self.position = grid_center(grid_x, grid_y)
        self.charge = 0
        self.stats = DEFENSE_STATS[defense_type]
        self.max_charge = self.stats["max_charge"]

    @property
    def damage(self) -> int:
        return self.stats["damage"]

    @property
    def range(self) -> int:
        return self.stats["range"]

    def is_charged(self) -> bool:
        return self.charge >= self.max_charge

    def charge_up(self):
        self.charge = min(self.max_charge, self.charge + 1)

    def fire(self):
        self.charge = 0

    def draw(self, surface: pygame.Surface):
        x, y = self.position.as_int_tuple()

        if self.defense_type == DefenseType.LASER:
            pygame.draw.circle(surface, CYAN, (x, y), 10)
            pygame.draw.line(surface, CYAN, (x - 5, y), (x + 5, y), 2)
            pygame.draw.line(surface, CYAN, (x, y - 5), (x, y + 5), 2)
        else:
            pygame.draw.rect(surface, PURPLE, (x - 12, y - 12, 24, 24), 2)
            pygame.draw.circle(surface, PURPLE, (x, y), 15, 2)
            # Show the EMP's real radius faintly so it is understandable to the player.
            pygame.draw.circle(surface, PURPLE, (x, y), self.range, 1)

        self.draw_charge_bar(surface, x, y)

    def draw_charge_bar(self, surface: pygame.Surface, x: int, y: int):
        charge_pct = self.charge / self.max_charge
        bar_width = 20
        bar_height = 4
        pygame.draw.rect(surface, GRAY, (x - bar_width // 2, y - 20, bar_width, bar_height))
        pygame.draw.rect(
            surface,
            GREEN if self.is_charged() else YELLOW,
            (x - bar_width // 2, y - 20, int(bar_width * charge_pct), bar_height),
        )


class LaserBeam:
    """Short visual beam. Damage is applied instantly when created."""

    def __init__(self, start_pos: Vector2, end_pos: Vector2):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.age = 0.0
        self.duration = LASER_BEAM_DURATION
        self.alive = True

    def update(self, dt: float):
        self.age += dt
        self.alive = self.age < self.duration

    def draw(self, surface: pygame.Surface):
        pct = max(0.0, 1.0 - self.age / self.duration)
        width = max(1, int(5 * pct))
        pygame.draw.line(surface, CYAN, self.start_pos.as_int_tuple(), self.end_pos.as_int_tuple(), width)
        pygame.draw.circle(surface, WHITE, self.end_pos.as_int_tuple(), max(2, width))


class EMPShockwave:
    """Expanding ring visual. Damage is applied instantly when created."""

    def __init__(self, center: Vector2, max_radius: int):
        self.center = center
        self.max_radius = max_radius
        self.age = 0.0
        self.duration = EMP_SHOCKWAVE_DURATION
        self.alive = True

    def update(self, dt: float):
        self.age += dt
        self.alive = self.age < self.duration

    def draw(self, surface: pygame.Surface):
        pct = min(1.0, self.age / self.duration)
        radius = max(4, int(self.max_radius * pct))
        width = max(1, int(6 * (1.0 - pct)))
        x, y = self.center.as_int_tuple()

        pygame.draw.circle(surface, PURPLE, (x, y), radius, width)
        pygame.draw.circle(surface, CYAN, (x, y), max(4, radius // 2), 1)


class Enemy:
    def __init__(self, enemy_type: EnemyType, lane: int, asteroids: Optional[List[Asteroid]] = None):
        self.enemy_type = enemy_type
        self.lane = lane
        self.position = Vector2(-20, lane * GRID_SIZE + GRID_SIZE // 2)
        self.health = 50 if enemy_type == EnemyType.FIGHTER else 100
        self.max_health = self.health
        self.speed = 80 if enemy_type == EnemyType.FIGHTER else 40
        self.asteroids = asteroids or []
        self.target_y = self.position.y

    def take_damage(self, damage: int):
        if self.enemy_type == EnemyType.TANK:
            damage = max(1, damage // 2)
        self.health -= damage

    def is_alive(self) -> bool:
        return self.health > 0

    def update(self, dt: float):
        self.position.x += self.speed * dt

        for asteroid in self.asteroids:
            if asteroid.collides_with_point(self.position):
                self.target_y += random.choice([-GRID_SIZE, GRID_SIZE])
                self.target_y = max(0, min(GAME_HEIGHT - GRID_SIZE, self.target_y))

        if abs(self.position.y - self.target_y) > 2:
            direction = 1 if self.target_y > self.position.y else -1
            self.position.y += direction * self.speed * 0.3 * dt

    def has_escaped(self) -> bool:
        return self.position.x > WINDOW_WIDTH

    def draw(self, surface: pygame.Surface):
        x, y = self.position.as_int_tuple()

        if self.enemy_type == EnemyType.FIGHTER:
            points = [(x + 15, y), (x - 10, y - 8), (x - 10, y + 8)]
            pygame.draw.polygon(surface, RED, points)
            pygame.draw.polygon(surface, RED, points, 2)
        else:
            points = []
            for i in range(6):
                angle = i * math.pi / 3
                points.append((x + 12 * math.cos(angle), y + 12 * math.sin(angle)))
            pygame.draw.polygon(surface, RED, points)
            pygame.draw.polygon(surface, RED, points, 2)

        self.draw_health_bar(surface, x, y)

    def draw_health_bar(self, surface: pygame.Surface, x: int, y: int):
        bar_width = 20
        bar_height = 3
        health_pct = max(0, self.health / self.max_health)
        color = GREEN if health_pct > 0.5 else YELLOW if health_pct > 0.2 else RED
        pygame.draw.rect(surface, GRAY, (x - bar_width // 2, y - 20, bar_width, bar_height))
        pygame.draw.rect(surface, color, (x - bar_width // 2, y - 20, int(bar_width * health_pct), bar_height))


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Space Tower Defense")
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.Font(None, 24)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_large = pygame.font.Font(None, 48)

        self.defenses: List[Defense] = []
        self.enemies: List[Enemy] = []
        self.effects: List[object] = []
        self.asteroids: List[Asteroid] = []

        self.cursor_grid = [GRID_WIDTH // 2, GRID_HEIGHT // 2]
        self.money = 350
        self.health = 20
        self.kills = 0
        self.current_level = 1
        self.wave_enemies_spawned = 0
        self.wave_enemies_killed = 0
        self.time = 0
        self.next_spawn_time = 30
        self.paused = False
        self.level_transition = False
        self.level_transition_time = 0
        self.high_score = self.load_high_score()

        self.show_menu = False
        self.game_over = False
        self.game_won = False

        self.levels = self.load_levels()
        self.level_data = self.get_level_data(self.current_level)
        self.enemies_per_level = self.level_data.get("enemies", 20)
        self.money = self.level_data.get("starting_money", self.money)

        self.generate_asteroids()

    def get_level_data(self, level_number: int) -> Dict:
        return self.levels.get(level_number) or self.levels.get(1) or self.create_default_levels()[1]

    def load_high_score(self) -> Dict:
        if os.path.exists(HIGH_SCORE_FILE):
            try:
                with open(HIGH_SCORE_FILE, "r") as file:
                    return json.load(file)
            except (OSError, json.JSONDecodeError):
                pass
        return {"score": 0, "money": 0, "date": "Never"}

    def save_high_score(self, score: int):
        if score <= self.high_score.get("score", 0):
            return

        self.high_score = {
            "score": score,
            "money": self.money,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        try:
            with open(HIGH_SCORE_FILE, "w") as file:
                json.dump(self.high_score, file)
        except OSError:
            pass

    def load_levels(self) -> Dict[int, Dict]:
        if os.path.exists(LEVELS_FILE):
            try:
                with open(LEVELS_FILE, "r") as file:
                    levels = json.load(file)
                return {int(level): data for level, data in levels.items()}
            except (OSError, json.JSONDecodeError, ValueError):
                pass
        return self.create_default_levels()

    def generate_asteroids(self):
        num_asteroids = self.level_data.get("asteroids", 8)
        attempts = 0
        while len(self.asteroids) < num_asteroids and attempts < 50:
            x = random.randint(3, GRID_WIDTH - 3)
            y = random.randint(2, GRID_HEIGHT - 2)
            too_close = any(abs(a.grid_x - x) < 3 and abs(a.grid_y - y) < 3 for a in self.asteroids)
            if not too_close:
                self.asteroids.append(Asteroid(x, y))
            attempts += 1

    def handle_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if not self.handle_keydown(event.key):
                    return False
        return True

    def handle_keydown(self, key: int) -> bool:
        if key == pygame.K_p:
            self.paused = not self.paused
        elif key == pygame.K_UP:
            self.cursor_grid[1] = max(0, self.cursor_grid[1] - 1)
        elif key == pygame.K_DOWN:
            self.cursor_grid[1] = min(GRID_HEIGHT - 1, self.cursor_grid[1] + 1)
        elif key == pygame.K_LEFT:
            self.cursor_grid[0] = max(0, self.cursor_grid[0] - 1)
        elif key == pygame.K_RIGHT:
            self.cursor_grid[0] = min(GRID_WIDTH - 1, self.cursor_grid[0] + 1)
        elif key == pygame.K_SPACE:
            self.show_menu = True
        elif key == pygame.K_q:
            return False
        elif key == pygame.K_ESCAPE:
            self.show_menu = False
        elif self.show_menu and key in (pygame.K_1, pygame.K_2):
            self.place_defense(DefenseType.LASER if key == pygame.K_1 else DefenseType.EMP)
            self.show_menu = False
        return True

    def place_defense(self, defense_type: DefenseType):
        cost = DEFENSE_STATS[defense_type]["cost"]
        grid_x, grid_y = self.cursor_grid

        if self.money < cost:
            return
        if any(d.grid_x == grid_x and d.grid_y == grid_y for d in self.defenses):
            return
        if any(a.grid_x == grid_x and a.grid_y == grid_y for a in self.asteroids):
            return

        self.money -= cost
        self.defenses.append(Defense(grid_x, grid_y, defense_type))

    def update(self, dt: float):
        if self.game_over or self.game_won:
            return
        if self.level_transition:
            self.update_level_transition(dt)
            return
        if self.paused:
            return

        self.time += 1
        self.spawn_enemies()
        self.update_enemies(dt)
        self.update_defenses()
        self.update_effects(dt)
        self.resolve_enemies()
        self.check_game_state()

    def update_level_transition(self, dt: float):
        self.level_transition_time += dt
        if self.level_transition_time >= 5:
            self.level_transition = False
            self.load_next_level()

    def spawn_enemies(self):
        if self.wave_enemies_spawned >= self.enemies_per_level or self.time < self.next_spawn_time:
            return

        lane = random.randint(0, GRID_HEIGHT - 1)
        enemy_type = random.choice([EnemyType.FIGHTER, EnemyType.TANK])
        self.enemies.append(Enemy(enemy_type, lane, self.asteroids))
        self.wave_enemies_spawned += 1

        spawn_min, spawn_max = self.level_data.get("spawn_rate", (40, 80))
        self.next_spawn_time = self.time + random.randint(spawn_min, spawn_max)

    def update_enemies(self, dt: float):
        for enemy in self.enemies:
            enemy.update(dt)

    def update_defenses(self):
        for defense in self.defenses:
            defense.charge_up()
            if not defense.is_charged():
                continue

            if defense.defense_type == DefenseType.LASER:
                self.fire_laser(defense)
            elif defense.defense_type == DefenseType.EMP:
                self.fire_emp(defense)

    def fire_laser(self, defense: Defense):
        target = self.find_nearest_enemy(defense.position, defense.range)
        if not target:
            return

        target.take_damage(defense.damage)
        self.effects.append(LaserBeam(defense.position, target.position))
        defense.fire()

    def fire_emp(self, defense: Defense):
        targets = [enemy for enemy in self.enemies if enemy.is_alive() and in_range(defense.position, enemy.position, defense.range)]
        if not targets:
            return

        for enemy in targets:
            enemy.take_damage(defense.damage)

        self.effects.append(EMPShockwave(defense.position, defense.range))
        defense.fire()

    def find_nearest_enemy(self, position: Vector2, radius: int) -> Optional[Enemy]:
        radius_squared = radius * radius
        nearest_enemy = None
        nearest_distance = float("inf")

        for enemy in self.enemies:
            if not enemy.is_alive():
                continue
            distance = position.distance_squared_to(enemy.position)
            if distance <= radius_squared and distance < nearest_distance:
                nearest_enemy = enemy
                nearest_distance = distance

        return nearest_enemy

    def update_effects(self, dt: float):
        for effect in self.effects:
            effect.update(dt)
        self.effects = [effect for effect in self.effects if effect.alive]

    def resolve_enemies(self):
        remaining_enemies = []
        for enemy in self.enemies:
            if not enemy.is_alive():
                self.money += REWARD_PER_KILL[enemy.enemy_type]
                self.kills += 1
                self.wave_enemies_killed += 1
            elif enemy.has_escaped():
                self.health -= 1
            else:
                remaining_enemies.append(enemy)
        self.enemies = remaining_enemies

    def check_game_state(self):
        if self.health <= 0:
            self.game_over = True
            self.save_high_score(self.kills)
            return

        wave_complete = self.wave_enemies_spawned >= self.enemies_per_level and not self.enemies
        if not wave_complete:
            return

        if self.current_level < max(self.levels):
            self.level_transition = True
            self.level_transition_time = 0
        else:
            self.game_won = True
            self.save_high_score(self.kills)

    def load_next_level(self):
        self.current_level += 1
        self.level_data = self.get_level_data(self.current_level)
        self.wave_enemies_spawned = 0
        self.wave_enemies_killed = 0
        self.time = 0
        self.next_spawn_time = 30
        self.enemies_per_level = self.level_data.get("enemies", 20)

        self.enemies.clear()
        self.effects.clear()
        self.defenses.clear()
        self.asteroids.clear()
        self.cursor_grid = [GRID_WIDTH // 2, GRID_HEIGHT // 2]

        self.generate_asteroids()

    def draw_grid(self):
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, GRAY, (x, 0), (x, GAME_HEIGHT), 1)
        for y in range(0, GAME_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, GRAY, (0, y), (WINDOW_WIDTH, y), 1)

    def draw_cursor(self):
        x = self.cursor_grid[0] * GRID_SIZE
        y = self.cursor_grid[1] * GRID_SIZE
        pygame.draw.rect(self.screen, GREEN, (x, y, GRID_SIZE, GRID_SIZE), 3)

    def draw_menu(self):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        menu_width = 440
        menu_height = 250
        menu_x = (WINDOW_WIDTH - menu_width) // 2
        menu_y = (WINDOW_HEIGHT - menu_height) // 2

        pygame.draw.rect(self.screen, DARK_BLUE, (menu_x, menu_y, menu_width, menu_height))
        pygame.draw.rect(self.screen, CYAN, (menu_x, menu_y, menu_width, menu_height), 3)

        title = self.font_medium.render("SELECT DEFENSE", True, CYAN)
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, menu_y + 30)))

        money_text = self.font_small.render(f"Money: ${self.money}", True, YELLOW)
        self.screen.blit(money_text, (menu_x + 20, menu_y + 70))

        self.draw_menu_option(menu_x, menu_y + 110, pygame.K_1, DefenseType.LASER, CYAN)
        self.draw_menu_option(menu_x, menu_y + 170, pygame.K_2, DefenseType.EMP, PURPLE)

    def draw_menu_option(self, menu_x: int, y: int, key: int, defense_type: DefenseType, color: Tuple[int, int, int]):
        stats = DEFENSE_STATS[defense_type]
        option_number = "1" if key == pygame.K_1 else "2"
        label = self.font_small.render(f"{option_number}) {stats['label']} - ${stats['cost']}", True, color)
        desc = self.font_small.render(stats["description"], True, LIGHT_GRAY)
        self.screen.blit(label, (menu_x + 30, y))
        self.screen.blit(desc, (menu_x + 50, y + 25))

    def draw_hud(self):
        hud_bg = pygame.Surface((WINDOW_WIDTH, HUD_HEIGHT))
        hud_bg.set_alpha(200)
        hud_bg.fill(DARK_BLUE)
        self.screen.blit(hud_bg, (0, GAME_HEIGHT))

        enemies_left = self.enemies_per_level - self.wave_enemies_killed
        hud_items = [
            (f"Health: {self.health}", RED if self.health <= 5 else WHITE, (20, GAME_HEIGHT + 15)),
            (f"Money: ${self.money}", YELLOW, (200, GAME_HEIGHT + 15)),
            (f"Level: {self.current_level} | Enemies: {enemies_left}/{self.enemies_per_level}", CYAN, (400, GAME_HEIGHT + 15)),
            (f"Kills: {self.kills}", GREEN, (800, GAME_HEIGHT + 15)),
            (f"High Score: {self.high_score.get('score', 0)} | Best Money: ${self.high_score.get('money', 0)}", PURPLE, (20, GAME_HEIGHT + 45)),
        ]

        for text, color, position in hud_items:
            self.screen.blit(self.font_small.render(text, True, color), position)

        pause_text = "P=Pause" if not self.paused else "P=Resume"
        controls = f"ARROWS: Move | SPACE: Place | {pause_text} | Q: Quit"
        self.screen.blit(self.font_small.render(controls, True, LIGHT_GRAY), (400, GAME_HEIGHT + 45))

    def draw(self):
        self.screen.fill(BLACK)
        self.draw_grid()

        for asteroid in self.asteroids:
            asteroid.draw(self.screen)
        for defense in self.defenses:
            defense.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        for effect in self.effects:
            effect.draw(self.screen)

        self.draw_cursor()
        self.draw_hud()
        self.draw_overlay_state()

        if self.show_menu:
            self.draw_menu()

        pygame.display.flip()

    def draw_overlay_state(self):
        if self.game_over:
            self.draw_center_message("GAME OVER", RED, f"Final Score: {self.kills} kills, ${self.money}")
        elif self.game_won:
            self.draw_center_message("ALL LEVELS COMPLETE!", GREEN, f"Final Score: {self.kills} kills, ${self.money}")
        elif self.paused:
            self.draw_pause_overlay()
        elif self.level_transition:
            self.draw_level_transition()

    def draw_center_message(self, title: str, title_color: Tuple[int, int, int], subtitle: str):
        title_surface = self.font_large.render(title, True, title_color)
        subtitle_surface = self.font_medium.render(subtitle, True, WHITE)
        self.screen.blit(title_surface, title_surface.get_rect(center=(WINDOW_WIDTH // 2, GAME_HEIGHT // 2 - 40)))
        self.screen.blit(subtitle_surface, subtitle_surface.get_rect(center=(WINDOW_WIDTH // 2, GAME_HEIGHT // 2 + 40)))

    def draw_pause_overlay(self):
        overlay = pygame.Surface((WINDOW_WIDTH, GAME_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        self.draw_center_message("PAUSED", CYAN, "Press P to Resume")

    def draw_level_transition(self):
        overlay = pygame.Surface((WINDOW_WIDTH, GAME_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        next_level = self.current_level + 1
        level_name = self.get_level_data(next_level).get("name", f"Level {next_level}")
        countdown = max(0, int(5 - self.level_transition_time))

        level_text = self.font_large.render(f"LEVEL {next_level}", True, GREEN)
        name_text = self.font_medium.render(level_name, True, CYAN)
        countdown_text = self.font_medium.render(f"Starting in: {countdown}", True, YELLOW)

        self.screen.blit(level_text, level_text.get_rect(center=(WINDOW_WIDTH // 2, GAME_HEIGHT // 2 - 60)))
        self.screen.blit(name_text, name_text.get_rect(center=(WINDOW_WIDTH // 2, GAME_HEIGHT // 2)))
        self.screen.blit(countdown_text, countdown_text.get_rect(center=(WINDOW_WIDTH // 2, GAME_HEIGHT // 2 + 60)))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            running = self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()

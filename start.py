import threading
import time

import pygame
import sys
import random
import math
from collections import deque

pygame.init()
clock = pygame.time.Clock()

# --- Загрузка ресурсов и глобальные настройки ---
SIZE_DEFAULT = (28, 28)
ammo_texture = pygame.transform.scale(pygame.image.load('images/patron.png'), SIZE_DEFAULT)
mine_texture = pygame.transform.scale(pygame.image.load('images/mina.png'), SIZE_DEFAULT)
bandage_texture = pygame.transform.scale(pygame.image.load('images/bandage.png'), SIZE_DEFAULT)
armor_texture = pygame.transform.scale(pygame.image.load('images/armor.png'), SIZE_DEFAULT)

cover_texture_raw = pygame.image.load('images/box_3.png')
health_texture = pygame.transform.scale(bandage_texture, SIZE_DEFAULT)
cover_texture = None

# Звуки (будущая доработка: можно добавить звук выстрела через pygame.mixer.Sound("...").play())
shoot_sound = pygame.mixer.Sound("sounds/shoot.mp3")
reload_sound = pygame.mixer.Sound("sounds/reload.wav")
release_sound = pygame.mixer.Sound("sounds/release.mp3")
explosion_sound = pygame.mixer.Sound("sounds/explosion.wav")

WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Городской бой")
FONT = pygame.font.SysFont("Arial", 20)

# Цвета и константы
BG_COLOR = (30, 30, 50)
ENEMY_COLOR = (200, 0, 0)
SNIPER_COLOR = (255, 0, 255)
BOSS_COLOR = (255, 165, 0)
HOSTAGE_COLOR = (0, 200, 200)
BOMB_COLOR = (255, 255, 0)
COVER_COLOR = (90, 60, 30)
ITEM_COLOR = (255, 255, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
LEVEL_COUNT = 20

player_class = "tank"
class_colors = {"sniper": (255, 255, 0), "tank": (0, 200, 0), "engineer": (0, 255, 255)}

player_x = 400
player_y = 300
player_speed = 3
player_health = 100
player_max_health = 100
ammo = 30
max_ammo = 30
reload_time = 0
reload_delay = 90
shoot_cooldown = 0
shoot_cooldown_max = 30
score = 0
current_level = 1
game_over = False

level_enemies = []
level_snipers = []
level_boss = []
level_covers = []  # теперь генерируются до спавна противников
level_hostages = []
level_bombs = []
level_items = []

player_armor = 0
player_max_armor = 50
player_inventory = []
level_complete = False
wave_timer = 0
wave_interval = 600
wave_active = False
wave_enemies = 0
sniper_spot_cooldown = 0
boss_defeated = False
boss_health = 300
boss_max_health = 300
minimap_scale = 0.2

shots_fired = []
enemy_shots = []
sniper_shots = []
boss_shots = []
explosions = []
explosion_radius = 25
explosion_time = 30
damage_cooldown = 0
damage_cooldown_time = 10

keys_pressed = {"w": False, "a": False, "s": False, "d": False, "r": False}

tile_size = 40
cols = WIDTH // tile_size
rows = HEIGHT // tile_size
grid_passable = [[True for _ in range(cols)] for _ in range(rows)]

mines = []
mine_explosion_radius = 50  # радиус взрыва мины
mine_explosion_time = 30
mine_spawn_timer = 0
mine_spawn_interval = 600

ENEMY_UPDATE_RATE_BASE = 30
SNIPER_UPDATE_RATE_BASE = 30
BOSS_UPDATE_RATE_BASE = 30
ENEMY_FIRE_RATE_BASE = 60
SNIPER_FIRE_RATE_BASE = 90
BOSS_FIRE_RATE_BASE = 45

player_extra_lives = 0

menu_active = True
selected_class = "tank"
# Переработанные координаты и размеры кнопок главного меню
title_rect = pygame.Rect(WIDTH // 2 - 150, 50, 300, 60)
sniper_button_rect = pygame.Rect(WIDTH // 2 - 250, 150, 150, 50)
tank_button_rect = pygame.Rect(WIDTH // 2 - 75, 150, 150, 50)
engineer_button_rect = pygame.Rect(WIDTH // 2 + 100, 150, 150, 50)
start_button_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT - 150, 120, 50)
exit_button_rect = pygame.Rect(WIDTH // 2 + 30, HEIGHT - 150, 120, 50)
current_class_rect = pygame.Rect(WIDTH // 2 - 75, 220, 150, 40)

sniper_button_color = (200, 200, 200)
tank_button_color = (200, 200, 200)
engineer_button_color = (200, 200, 200)
start_button_color = (200, 200, 200)
exit_button_color = (200, 200, 200)
hover_color = (255, 255, 150)
return_to_menu = False

# Новая переменная для перехода в меню (из паузы)
restart_game = False

ENEMY_UPDATE_RATE = ENEMY_UPDATE_RATE_BASE
SNIPER_UPDATE_RATE = SNIPER_UPDATE_RATE_BASE
BOSS_UPDATE_RATE = BOSS_UPDATE_RATE_BASE
ENEMY_FIRE_RATE = ENEMY_FIRE_RATE_BASE
SNIPER_FIRE_RATE = SNIPER_FIRE_RATE_BASE
BOSS_FIRE_RATE = BOSS_FIRE_RATE_BASE
level_title_timer = 0
mission_accomplished_timer = 0
show_level_title = False
show_mission_accomplished = False
transition_delay = 90
paused = False
show_game_over = False

# Для инженера: количество мин, которые можно установить за игру (максимум 3)
engineer_mines_left = 0


# --- Функции базовой логики и отрисовки ---

def difficulty_scale(lv):
    n = 1 + 0.1 * (lv - 1)
    return n if n < 3 else 3


def load_cover_texture():
    global cover_texture, cover_texture_raw
    cover_texture = cover_texture_raw


def draw_text(txt, x, y, color=WHITE, font=FONT):
    ts = font.render(txt, True, color)
    screen.blit(ts, (x, y))


def reset_keys():
    for k in keys_pressed:
        keys_pressed[k] = False


# --- Обработка событий ---
def handle_input_events():
    global game_over, menu_active, selected_class, return_to_menu, sniper_button_color, tank_button_color, engineer_button_color, start_button_color, exit_button_color, paused, show_game_over, engineer_mines_left, restart_game
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # Если игра на паузе – проверяем возможность возврата в главное меню
        if paused:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    restart_game = True
                    return
        if menu_active:
            mx, my = pygame.mouse.get_pos()
            if sniper_button_rect.collidepoint(mx, my):
                sniper_button_color = hover_color
            else:
                sniper_button_color = (200, 200, 200)
            if tank_button_rect.collidepoint(mx, my):
                tank_button_color = hover_color
            else:
                tank_button_color = (200, 200, 200)
            if engineer_button_rect.collidepoint(mx, my):
                engineer_button_color = hover_color
            else:
                engineer_button_color = (200, 200, 200)
            if start_button_rect.collidepoint(mx, my):
                start_button_color = hover_color
            else:
                start_button_color = (200, 200, 200)
            if exit_button_rect.collidepoint(mx, my):
                exit_button_color = hover_color
            else:
                exit_button_color = (200, 200, 200)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if sniper_button_rect.collidepoint(mx, my):
                        selected_class = "sniper"
                    elif tank_button_rect.collidepoint(mx, my):
                        selected_class = "tank"
                    elif engineer_button_rect.collidepoint(mx, my):
                        selected_class = "engineer"
                    elif start_button_rect.collidepoint(mx, my):
                        menu_active = False
                    elif exit_button_rect.collidepoint(mx, my):
                        pygame.quit()
                        sys.exit()
            return
        if return_to_menu:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game_over_screen_reset()
            continue
        if show_game_over:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game_over_screen_reset()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            continue
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w: keys_pressed["w"] = True
            if event.key == pygame.K_a: keys_pressed["a"] = True
            if event.key == pygame.K_s: keys_pressed["s"] = True
            if event.key == pygame.K_d: keys_pressed["d"] = True
            if event.key == pygame.K_r: keys_pressed["r"] = True
            if event.key == pygame.K_ESCAPE:
                paused = not paused
            # Если выбран класс "инженер" – клавиша M устанавливает мину
            if event.key == pygame.K_e and player_class == "engineer" and engineer_mines_left > 0:
                mines.append([player_x, player_y])
                engineer_mines_left -= 1
                # (Будущая доработка: добавить звук установки мины)
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_w: keys_pressed["w"] = False
            if event.key == pygame.K_a: keys_pressed["a"] = False
            if event.key == pygame.K_s: keys_pressed["s"] = False
            if event.key == pygame.K_d: keys_pressed["d"] = False
            if event.key == pygame.K_r: keys_pressed["r"] = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                shoot_bullet()


def game_over_screen_reset():
    global menu_active, game_over, return_to_menu, score, current_level, level_complete, boss_defeated, show_game_over, player_extra_lives, engineer_mines_left, restart_game, paused
    menu_active = True
    game_over = False
    return_to_menu = False
    show_game_over = False
    score = 0
    current_level = 1
    level_complete = False
    boss_defeated = False
    player_extra_lives = 0
    engineer_mines_left = 0
    restart_game = False
    paused = False


def set_player_class(cls):
    global player_class, player_health, player_max_health, player_armor, player_max_armor, engineer_mines_left
    player_class = cls
    if cls == "sniper":
        player_max_health = 80
        player_health = 80
        player_max_armor = 30
        player_armor = 30
    elif cls == "tank":
        player_max_health = 120
        player_health = 120
        player_max_armor = 60
        player_armor = 60
    elif cls == "engineer":
        player_max_health = 100
        player_health = 100
        player_max_armor = 50
        player_armor = 50
        engineer_mines_left = 3


def reload_weapon():
    global ammo, reload_time
    if ammo < max_ammo and reload_time <= 0:
        reload_time = reload_delay
        reload_sound.play()


def update_reload():
    global ammo, reload_time
    if reload_time > 0:
        reload_time -= 1
        if reload_time <= 0:
            ammo = max_ammo


# Функция для спавна игрока с проверкой столкновения с укрытиями
def random_player_spawn():
    while True:
        x = random.randint(50, WIDTH - 50)
        y = random.randint(50, HEIGHT - 50)
        rect_check = pygame.Rect(x - 20, y - 20, 40, 40)
        collision = False
        for cov in level_covers:
            cx, cy, cw, ch = cov
            rect_cov = pygame.Rect(cx, cy, cw, ch)
            if rect_check.colliderect(rect_cov):
                collision = True
                break
        if not collision:
            return x, y


# Функция создания уровня: сначала генерируются укрытия, затем спавнятся враги с проверкой столкновений с текстурами
def create_level_data(lv):
    global level_enemies, level_snipers, level_boss, level_covers, level_hostages, level_bombs, level_items, wave_enemies, boss_health, boss_max_health
    # Сброс данных уровня
    level_enemies = []
    level_snipers = []
    level_boss = []
    level_hostages = []
    level_bombs = []
    level_items = []
    wave_enemies = 0

    # Сначала генерируем укрытия (баррикады)
    level_covers = []
    cover_count = 5
    for i in range(cover_count):
        while True:
            cx = random.randint(0, cols - 2)
            cy = random.randint(0, rows - 2)
            cw = random.randint(1, 2)
            ch = random.randint(1, 2)
            px = cx * tile_size
            py = cy * tile_size
            w = cw * tile_size
            h = ch * tile_size
            rect_cover = pygame.Rect(px, py, w, h)
            collision = False
            # Проверяем, чтобы укрытия не накладывались друг на друга
            for cov in level_covers:
                cvx, cvy, cvw, cvh = cov
                rect_cov = pygame.Rect(cvx, cvy, cvw, cvh)
                if rect_cover.colliderect(rect_cov):
                    collision = True
                    break
            if not collision:
                level_covers.append([px, py, w, h])
                break

    # Локальная функция для спавна врагов с проверкой столкновения с укрытиями
    def spawn_enemy_avoiding_cover():
        while True:
            x = random.randint(50, WIDTH - 50)
            y = random.randint(50, HEIGHT - 50)
            rect_check = pygame.Rect(x - 12, y - 12, 24, 24)
            collision = False
            for cov in level_covers:
                cx, cy, cw, ch = cov
                rect_cov = pygame.Rect(cx, cy, cw, ch)
                if rect_check.colliderect(rect_cov):
                    collision = True
                    break
            if not collision:
                return x, y

    sc = difficulty_scale(lv)
    if lv < 20:
        enemy_count = min(lv + 3, 15)
        sniper_count = lv // 4
        for i in range(enemy_count):
            ex, ey = spawn_enemy_avoiding_cover()
            eh = int(100 * sc)
            level_enemies.append([ex, ey, eh, [], 0, random.randint(0, int(ENEMY_FIRE_RATE_BASE / sc))])
        for i in range(sniper_count):
            sx, sy = spawn_enemy_avoiding_cover()
            sh = int(80 * sc)
            level_snipers.append([sx, sy, sh, [], 0, random.randint(0, int(SNIPER_FIRE_RATE_BASE / sc))])
        hostage_count = 1 if lv % 2 == 0 else 0
        for i in range(hostage_count):
            hx, hy = spawn_enemy_avoiding_cover()
            level_hostages.append([hx, hy, True])
        bomb_count = 1 if lv % 3 == 0 else 0
        for i in range(bomb_count):
            bx, by = spawn_enemy_avoiding_cover()
            level_bombs.append([bx, by, 300])
        item_count = 2
        for i in range(item_count):
            ix, iy = spawn_enemy_avoiding_cover()
            itype = random.choice(["health", "ammo", "armor", "none", "none", "none"])
            if itype == "none":
                continue
            level_items.append([ix, iy, itype])
    else:
        boss_health = int(300 * sc)
        boss_max_health = int(300 * sc)
        bx, by = spawn_enemy_avoiding_cover()
        level_boss.append([bx, by, boss_health, [], 0, random.randint(0, int(BOSS_FIRE_RATE_BASE / sc))])
        item_count = 4
        for i in range(item_count):
            ix, iy = spawn_enemy_avoiding_cover()
            itype = random.choice(["health", "ammo", "armor", "none"])
            if itype == "none":
                continue
            level_items.append([ix, iy, itype])


def fill_grid_passable():
    global grid_passable
    for r in range(rows):
        for c in range(cols):
            grid_passable[r][c] = True
    for cov in level_covers:
        px, py, w, h = cov
        cx0 = px // tile_size
        cy0 = py // tile_size
        cw = w // tile_size
        ch = h // tile_size
        for ry in range(cy0, cy0 + ch):
            for rx in range(cx0, cx0 + cw):
                if 0 <= rx < cols and 0 <= ry < rows:
                    grid_passable[ry][rx] = False


def get_grid_pos(x, y):
    return int(x // tile_size), int(y // tile_size)


def get_pixel_center(gx, gy):
    px = gx * tile_size + tile_size // 2
    py = gy * tile_size + tile_size // 2
    return px, py


def get_random_tile_near_player(px, py, radius=3, attempts=10):
    gx, gy = get_grid_pos(px, py)
    for i in range(attempts):
        rx = random.randint(gx - radius, gx + radius)
        ry = random.randint(gy - radius, gy + radius)
        if 0 <= rx < cols and 0 <= ry < rows and grid_passable[ry][rx]:
            return rx, ry
    return gx, gy


def bfs_pathfind(startx, starty, endgx, endgy):
    sx, sy = get_grid_pos(startx, starty)
    if sx < 0 or sx >= cols or sy < 0 or sy >= rows: return []
    if endgx < 0 or endgx >= cols or endgy < 0 or endgy >= rows: return []
    if not grid_passable[sy][sx]: return []
    if not grid_passable[endgy][endgx]: return []
    visited = [[False for _ in range(cols)] for _ in range(rows)]
    parent = {}
    q = deque()
    q.append((sx, sy))
    visited[sy][sx] = True
    found = False
    while q:
        cx, cy = q.popleft()
        if cx == endgx and cy == endgy:
            found = True
            break
        for nx, ny in [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]:
            if 0 <= nx < cols and 0 <= ny < rows:
                if not visited[ny][nx] and grid_passable[ny][nx]:
                    visited[ny][nx] = True
                    parent[(nx, ny)] = (cx, cy)
                    q.append((nx, ny))
    if not found: return []
    path = []
    cur = (endgx, endgy)
    while cur in parent:
        path.append(cur)
        cur = parent[cur]
    path.append((sx, sy))
    path.reverse()
    return path


def reset_player():
    global player_x, player_y, player_health, player_max_health, player_armor, ammo
    px, py = random_player_spawn()
    player_x = px
    player_y = py
    player_health = player_max_health
    player_armor = player_max_armor
    ammo = max_ammo


def start_level(lv):
    global level_complete, current_level, boss_defeated, show_level_title, level_title_timer, mission_accomplished_timer, show_mission_accomplished, mines, mine_spawn_timer
    level_complete = False
    boss_defeated = False
    show_level_title = True
    level_title_timer = 120
    mission_accomplished_timer = 0
    show_mission_accomplished = False
    create_level_data(lv)
    reset_player()
    fill_grid_passable()
    mines = []
    mine_spawn_timer = 0


def check_level_complete():
    global level_enemies, level_snipers, level_hostages, level_bombs, level_boss, boss_defeated, level_complete
    if current_level < 20:
        if len(level_enemies) == 0 and len(level_snipers) == 0 and all(not h[2] for h in level_hostages) and all(
                b[2] <= 0 for b in level_bombs):
            level_complete = True
    else:
        if boss_defeated:
            level_complete = True


def take_damage(d):
    global player_health, player_armor, damage_cooldown
    if damage_cooldown > 0: return
    absorbed = 0
    if player_armor > 0:
        absorbed = min(player_armor, d)
        player_armor -= absorbed
    remainder = d - absorbed
    if remainder > 0:
        player_health -= remainder
    damage_cooldown = damage_cooldown_time


def collide_with_covers(px, py, r=10):
    rect_p = pygame.Rect(px - r, py - r, r * 2, r * 2)
    for c in level_covers:
        cx, cy, cw, ch = c
        rect_c = pygame.Rect(cx, cy, cw, ch)
        if rect_p.colliderect(rect_c):
            return True
    return False


def move_player():
    global player_x, player_y
    old_x, old_y = player_x, player_y
    dx = 0
    dy = 0
    if keys_pressed["w"]: dy = -player_speed
    if keys_pressed["s"]: dy = player_speed
    if keys_pressed["a"]: dx = -player_speed
    if keys_pressed["d"]: dx = player_speed
    player_x += dx
    player_y += dy
    if player_x < 10: player_x = 10
    if player_x > WIDTH - 10: player_x = WIDTH - 10
    if player_y < 10: player_y = 10
    if player_y > HEIGHT - 10: player_y = HEIGHT - 10
    if collide_with_covers(player_x, player_y, 10):
        player_x = old_x
        player_y = old_y


def shoot_bullet():
    global shots_fired, ammo, shoot_cooldown
    if shoot_cooldown > 0: return
    if ammo > 0 and reload_time <= 0:
        shoot_sound.play()
        mx, my = pygame.mouse.get_pos()
        angle = math.atan2(my - player_y, mx - player_x)
        speed = 10
        shots_fired.append([player_x, player_y, angle, speed])
        ammo -= 1
        shoot_cooldown = shoot_cooldown_max
    else:
        release_sound.play()


def enemy_shoot(ex, ey):
    angle = math.atan2(player_y - ey, player_x - ex)
    speed = 8
    enemy_shots.append([ex, ey, angle, speed])


def sniper_shoot(sx, sy):
    angle = math.atan2(player_y - sy, player_x - sx)
    speed = 12
    sniper_shots.append([sx, sy, angle, speed])


def boss_shoot(bx, by):
    angle = math.atan2(player_y - by, player_x - bx)
    speed = 10
    boss_shots.append([bx, by, angle, speed])


def explode(entity_x, entity_y, rad, damage):
    global player_x, player_y, explosions
    if damage == 70:
        explosion_sound.play()
    explosions.append([entity_x, entity_y, rad, explosion_time])
    dist = math.hypot(entity_x - player_x, entity_y - player_y)
    if dist < rad:
        take_damage(damage)


def update_bullets():
    global shots_fired, enemy_shots, sniper_shots, boss_shots, level_enemies, level_snipers, level_boss, boss_defeated, score
    new_player_bullets = []
    for b in shots_fired:
        bx, by, ang, spd = b
        bx += math.cos(ang) * spd
        by += math.sin(ang) * spd
        if bx < 0 or bx > WIDTH or by < 0 or by > HEIGHT: continue
        if collide_with_covers(bx, by, 5):
            explode(bx, by, explosion_radius, 0)
            continue
        mine_hit = None
        for m in mines:
            mx, my = m
            if math.hypot(bx - mx, by - my) < 12:
                mine_hit = m
                break
        if mine_hit:
            mines.remove(mine_hit)
            explode(mine_hit[0], mine_hit[1], mine_explosion_radius, 70)
            continue
        hit = False
        for e in level_enemies:
            dist_e = math.hypot(bx - e[0], by - e[1])
            if dist_e < 10:
                e[2] -= 40
                if e[2] <= 0:
                    score += 10
                    level_enemies.remove(e)
                explode(bx, by, explosion_radius, 0)
                hit = True
                break
        if hit: continue
        for s in level_snipers:
            dist_s = math.hypot(bx - s[0], by - s[1])
            if dist_s < 10:
                s[2] -= 50
                if s[2] <= 0:
                    score += 15
                    level_snipers.remove(s)
                explode(bx, by, explosion_radius, 0)
                hit = True
                break
        if hit: continue
        if current_level == 20 and len(level_boss) > 0:
            for bs in level_boss:
                if math.hypot(bx - bs[0], by - bs[1]) < 15:
                    bs[2] -= 20
                    if bs[2] <= 0:
                        boss_defeated = True
                        score += 200
                        level_boss.remove(bs)
                    explode(bx, by, explosion_radius, 0)
                    hit = True
                    break
        if hit: continue
        for h in level_hostages:
            hx, hy, alive = h
            if alive:
                if math.hypot(bx - hx, by - hy) < 10:
                    h[2] = False
                    game_over_screen_trigger()
                    explode(bx, by, explosion_radius, 0)
                    hit = True
                    break
        if hit: continue
        new_player_bullets.append([bx, by, ang, spd])
    shots_fired = new_player_bullets

    new_enemy_bullets = []
    for eb in enemy_shots:
        bx, by, ang, spd = eb
        bx += math.cos(ang) * spd
        by += math.sin(ang) * spd
        if bx < 0 or bx > WIDTH or by < 0 or by > HEIGHT: continue
        if collide_with_covers(bx, by, 5):
            explode(bx, by, explosion_radius, 0)
            continue
        mine_hit = None
        for m in mines:
            mx, my = m
            if math.hypot(bx - mx, by - my) < 12:
                mine_hit = m
                break
        if mine_hit:
            mines.remove(mine_hit)
            explode(mine_hit[0], mine_hit[1], mine_explosion_radius, 50)
            continue
        dist_p = math.hypot(bx - player_x, by - player_y)
        if dist_p < 10:
            explode(bx, by, explosion_radius, 10)
            continue
        for h in level_hostages:
            hx, hy, alive = h
            if alive:
                if math.hypot(bx - hx, by - hy) < 10:
                    h[2] = False
                    game_over_screen_trigger()
                    explode(bx, by, explosion_radius, 0)
                    break
        new_enemy_bullets.append([bx, by, ang, spd])
    enemy_shots = new_enemy_bullets

    new_sniper_bullets = []
    for sb in sniper_shots:
        bx, by, ang, spd = sb
        bx += math.cos(ang) * spd
        by += math.sin(ang) * spd
        if bx < 0 or bx > WIDTH or by < 0 or by > HEIGHT: continue
        if collide_with_covers(bx, by, 5):
            explode(bx, by, explosion_radius, 0)
            continue
        mine_hit = None
        for m in mines:
            mx, my = m
            if math.hypot(bx - mx, by - my) < 12:
                mine_hit = m
                break
        if mine_hit:
            mines.remove(mine_hit)
            explode(mine_hit[0], mine_hit[1], mine_explosion_radius, 50)
            continue
        dist_p = math.hypot(bx - player_x, by - player_y)
        if dist_p < 10:
            explode(bx, by, explosion_radius, 15)
            continue
        for h in level_hostages:
            hx, hy, alive = h
            if alive:
                if math.hypot(bx - hx, by - hy) < 10:
                    h[2] = False
                    game_over_screen_trigger()
                    explode(bx, by, explosion_radius, 0)
                    break
        new_sniper_bullets.append([bx, by, ang, spd])
    sniper_shots = new_sniper_bullets

    new_boss_bullets = []
    for bb in boss_shots:
        bx, by, ang, spd = bb
        bx += math.cos(ang) * spd
        by += math.sin(ang) * spd
        if bx < 0 or bx > WIDTH or by < 0 or by > HEIGHT: continue
        if collide_with_covers(bx, by, 5):
            explode(bx, by, explosion_radius, 0)
            continue
        mine_hit = None
        for m in mines:
            mx, my = m
            if math.hypot(bx - mx, by - my) < 12:
                mine_hit = m
                break
        if mine_hit:
            mines.remove(mine_hit)
            explode(mine_hit[0], mine_hit[1], mine_explosion_radius, 50)
            continue
        dist_p = math.hypot(bx - player_x, by - player_y)
        if dist_p < 15:
            explode(bx, by, explosion_radius, 20)
            continue
        for h in level_hostages:
            hx, hy, alive = h
            if alive:
                if math.hypot(bx - hx, by - hy) < 10:
                    h[2] = False
                    game_over_screen_trigger()
                    explode(bx, by, explosion_radius, 0)
                    break
        new_boss_bullets.append([bx, by, ang, spd])
    boss_shots = new_boss_bullets


def game_over_screen_trigger():
    global game_over, return_to_menu, show_game_over
    game_over = True
    return_to_menu = True
    show_game_over = True


def update_explosions():
    global explosions
    new_exp = []
    for exp in explosions:
        ex, ey, r, t = exp
        t -= 1
        if t > 0:
            new_exp.append([ex, ey, r, t])
    explosions = new_exp


def draw_explosions():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for exp in explosions:
        ex, ey, r, t = exp
        alpha = t / explosion_time
        rr = int(r * (1 - alpha))
        c = (255, 150, 0, int(255 * (1 - alpha)))
        pygame.draw.circle(overlay, c, (int(ex), int(ey)), rr)
    screen.blit(overlay, (0, 0))


def enemy_recalc_path(enemy):
    ex, ey, eh, path, ut, ft = enemy
    rx, ry = get_random_tile_near_player(player_x, player_y)
    new_path = bfs_pathfind(ex, ey, rx, ry)
    enemy[3] = new_path


def enemy_next_move(enemy):
    ex, ey, eh, path, ut, ft = enemy
    if len(path) > 1:
        gx, gy = path[1]
        px, py = get_pixel_center(gx, gy)
        dx = px - ex
        dy = py - ey
        dist = math.hypot(dx, dy)
        if dist > 1:
            step = 1
            nx = ex + (dx / dist) * step
            ny = ey + (dy / dist) * step
            if not collide_with_covers(nx, ny, 10):
                ex, ey = nx, ny
        else:
            path.pop(0)
    enemy[0] = ex
    enemy[1] = ey
    enemy[3] = path


def enemy_ai():
    global level_enemies
    for e in level_enemies:
        e[4] += 1
        e[5] += 1
        if e[4] >= ENEMY_UPDATE_RATE:
            e[4] = 0
            enemy_recalc_path(e)
        enemy_next_move(e)
        dist = math.hypot(e[0] - player_x, e[1] - player_y)
        if dist < 20:
            take_damage(5)
        if dist < 200 and e[5] >= ENEMY_FIRE_RATE:
            e[5] = 0
            enemy_shoot(e[0], e[1])


def sniper_recalc_path(sn):
    sx, sy, sh, path, ut, ft = sn
    if math.hypot(sx - player_x, sy - player_y) > 150:
        rx, ry = get_random_tile_near_player(player_x, player_y)
        new_path = bfs_pathfind(sx, sy, rx, ry)
        sn[3] = new_path
    else:
        sn[3] = []


def sniper_next_move(sn):
    sx, sy, sh, path, ut, ft = sn
    if len(path) > 1:
        gx, gy = path[1]
        px, py = get_pixel_center(gx, gy)
        dx = px - sx
        dy = py - sy
        dist = math.hypot(dx, dy)
        if dist > 1:
            step = 1
            nx = sx + (dx / dist) * step
            ny = sy + (dy / dist) * step
            if not collide_with_covers(nx, ny, 10):
                sx, sy = nx, ny
        else:
            path.pop(0)
    sn[0] = sx
    sn[1] = sy
    sn[3] = path


def sniper_ai():
    global level_snipers, sniper_spot_cooldown
    for s in level_snipers:
        s[4] += 1
        s[5] += 1
        if s[4] >= SNIPER_UPDATE_RATE:
            s[4] = 0
            sniper_recalc_path(s)
        sniper_next_move(s)
        dist = math.hypot(s[0] - player_x, s[1] - player_y)
        if dist < 200:
            if s[5] >= SNIPER_FIRE_RATE:
                s[5] = 0
                sniper_shoot(s[0], s[1])
            if sniper_spot_cooldown <= 0:
                take_damage(5)
                sniper_spot_cooldown = 60


def boss_recalc_path(bs):
    bx, by, bh, path, ut, ft = bs
    rx, ry = get_random_tile_near_player(player_x, player_y, 2)
    new_path = bfs_pathfind(bx, by, rx, ry)
    bs[3] = new_path


def boss_next_move(bs):
    bx, by, bh, path, ut, ft = bs
    if len(path) > 1:
        gx, gy = path[1]
        px, py = get_pixel_center(gx, gy)
        dx = px - bx
        dy = py - by
        dist = math.hypot(dx, dy)
        if dist > 2:
            step = 2
            nx = bx + (dx / dist) * step
            ny = by + (dy / dist) * step
            if not collide_with_covers(nx, ny, 25):
                bx, by = nx, ny
        else:
            path.pop(0)
    bs[0] = bx
    bs[1] = by
    bs[3] = path


def boss_ai():
    global level_boss
    for bs in level_boss:
        bs[4] += 1
        bs[5] += 1
        if bs[4] >= BOSS_UPDATE_RATE:
            bs[4] = 0
            boss_recalc_path(bs)
        boss_next_move(bs)
        dist = math.hypot(bs[0] - player_x, bs[1] - player_y)
        if dist < 40:
            take_damage(15)
        if dist < 250 and bs[5] >= BOSS_FIRE_RATE:
            bs[5] = 0
            boss_shoot(bs[0], bs[1])


def check_player_dead():
    global player_health, game_over, return_to_menu, show_game_over, player_extra_lives
    if player_health <= 0:
        if player_extra_lives > 0:
            player_extra_lives -= 1
            player_health = player_max_health // 2
            return
        game_over = True
        return_to_menu = True
        show_game_over = True


def draw_player():
    color = class_colors.get(player_class, (0, 200, 0))
    pygame.draw.circle(screen, color, (int(player_x), int(player_y)), 10)


def draw_enemies():
    for e in level_enemies:
        pygame.draw.circle(screen, ENEMY_COLOR, (int(e[0]), int(e[1])), 10)


def draw_snipers():
    for s in level_snipers:
        pygame.draw.circle(screen, SNIPER_COLOR, (int(s[0]), int(s[1])), 10)


def draw_boss():
    for bs in level_boss:
        pygame.draw.circle(screen, BOSS_COLOR, (int(bs[0]), int(bs[1])), 25)


def draw_covers():
    global cover_texture
    if cover_texture is None:
        load_cover_texture()
    for c in level_covers:
        px, py, w, h = c
        scaled = pygame.transform.scale(cover_texture, (w, h))
        screen.blit(scaled, (px, py))


def draw_hostages():
    for h in level_hostages:
        if h[2]:
            pygame.draw.circle(screen, HOSTAGE_COLOR, (int(h[0]), int(h[1])), 8)


def draw_bombs():
    for b in level_bombs:
        if b[2] > 0:
            pygame.draw.circle(screen, BOMB_COLOR, (int(b[0]), int(b[1])), 8)


def draw_items():
    for it in level_items:
        ix, iy, itype = it
        if itype == "health":
            rect_img = health_texture.get_rect(center=(ix, iy))
            screen.blit(health_texture, rect_img)
        elif itype == "ammo":
            rect_img = ammo_texture.get_rect(center=(ix, iy))
            screen.blit(ammo_texture, rect_img)
        elif itype == "armor":
            rect_img = armor_texture.get_rect(center=(ix, iy))
            screen.blit(armor_texture, rect_img)


def draw_mines():
    for m in mines:
        mx, my = m
        rect_img = mine_texture.get_rect(center=(mx, my))
        screen.blit(mine_texture, rect_img)


def draw_bullet_lists():
    for b in shots_fired:
        pygame.draw.circle(screen, (255, 255, 0), (int(b[0]), int(b[1])), 3)
    for eb in enemy_shots:
        pygame.draw.circle(screen, (255, 0, 0), (int(eb[0]), int(eb[1])), 3)
    for sb in sniper_shots:
        pygame.draw.circle(screen, (255, 0, 255), (int(sb[0]), int(sb[1])), 3)
    for bb in boss_shots:
        pygame.draw.circle(screen, (255, 165, 0), (int(bb[0]), int(bb[1])), 4)


def update_hostages():
    global level_hostages
    for h in level_hostages:
        hx, hy, alive = h
        if alive:
            dist = math.hypot(hx - player_x, hy - player_y)
            if dist < 20:
                h[2] = False


def update_bombs():
    global level_bombs
    for b in level_bombs:
        bx, by, time_left = b
        if time_left > 0:
            b[2] -= 1
            dist = math.hypot(bx - player_x, by - player_y)
            if dist < 20 and pygame.key.get_pressed()[pygame.K_e]:
                b[2] = 0
            if b[2] <= 0:
                explode_bomb(b)


def explode_bomb(b):
    global level_bombs
    bx, by, t = b
    explode(bx, by, explosion_radius, 50)
    for i in range(len(level_bombs)):
        if level_bombs[i] == b:
            level_bombs[i][2] = 0


def update_items():
    global level_items, player_health, player_max_health, ammo, max_ammo, player_armor, player_max_armor, player_extra_lives
    new_items = []
    for it in level_items:
        ix, iy, itype = it
        dist = math.hypot(ix - player_x, iy - player_y)
        if dist < 20:
            if itype == "health":
                player_health += 30
                if player_health > player_max_health: player_health = player_max_health
            elif itype == "ammo":
                ammo += 10
                if ammo > max_ammo: ammo = max_ammo
            elif itype == "armor":
                player_armor += 20
                if player_armor > player_max_armor: player_armor = player_max_armor
        else:
            new_items.append(it)
    level_items = new_items


def draw_bars():
    health_bar_w = 200
    health_ratio = player_health / player_max_health
    armor_ratio = 0
    if player_max_armor > 0: armor_ratio = player_armor / player_max_armor
    pygame.draw.rect(screen, RED, (10, 10, int(health_bar_w * health_ratio), 10))
    pygame.draw.rect(screen, (0, 0, 150), (10, 25, int(health_bar_w * armor_ratio), 10))
    draw_text("Здоровье: " + str(player_health), 10, 40, WHITE)
    draw_text("Броня: " + str(player_armor), 10, 60, WHITE)
    draw_text("Патроны: " + str(ammo), 10, 80, WHITE)
    draw_text("Счёт: " + str(score), 10, 100, WHITE)
    draw_text("Уровень: " + str(current_level), 10, 120, WHITE)
    draw_text("Жизни: " + str(player_extra_lives), 10, 140, WHITE)
    if reload_time > 0:
        draw_text("Перезарядка...", 10, 160, WHITE)


def draw_bomb_timers():
    for b in level_bombs:
        if b[2] > 0:
            draw_text(str(b[2] // 60), b[0] - 10, b[1] - 20, RED)


def minimap():
    mm_w = int(WIDTH * minimap_scale)
    mm_h = int(HEIGHT * minimap_scale)
    overlay = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    px = int((player_x / WIDTH) * mm_w)
    py = int((player_y / HEIGHT) * mm_h)
    pygame.draw.circle(overlay, class_colors.get(player_class, (0, 200, 0)), (px, py), 2)
    for e in level_enemies:
        ex = int((e[0] / WIDTH) * mm_w)
        ey = int((e[1] / HEIGHT) * mm_h)
        pygame.draw.circle(overlay, ENEMY_COLOR, (ex, ey), 2)
    for s in level_snipers:
        sx = int((s[0] / WIDTH) * mm_w)
        sy = int((s[1] / HEIGHT) * mm_h)
        pygame.draw.circle(overlay, SNIPER_COLOR, (sx, sy), 2)
    for bs in level_boss:
        bx = int((bs[0] / WIDTH) * mm_w)
        by = int((bs[1] / HEIGHT) * mm_h)
        pygame.draw.circle(overlay, BOSS_COLOR, (bx, by), 4)
    for h in level_hostages:
        if h[2]:
            hx = int((h[0] / WIDTH) * mm_w)
            hy = int((h[1] / HEIGHT) * mm_h)
            pygame.draw.circle(overlay, HOSTAGE_COLOR, (hx, hy), 2)
    for b in level_bombs:
        if b[2] > 0:
            bx = int((b[0] / WIDTH) * mm_w)
            by = int((b[1] / HEIGHT) * mm_h)
            pygame.draw.circle(overlay, BOMB_COLOR, (bx, by), 2)
    for m in mines:
        mx = int((m[0] / WIDTH) * mm_w)
        my = int((m[1] / HEIGHT) * mm_h)
        pygame.draw.circle(overlay, (150, 150, 150), (mx, my), 2)
    screen.blit(overlay, (WIDTH - mm_w - 10, 10))


def update_wave():
    global wave_timer, wave_active, wave_enemies, level_enemies
    if current_level < 20:
        if not wave_active:
            wave_timer += 1
            if wave_timer >= wave_interval:
                wave_active = True
                wave_timer = 0
                wave_enemies = random.randint(1, 3)
                for i in range(wave_enemies):
                    ex, ey = random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50)
                    e_health = int(100 * difficulty_scale(current_level))
                    level_enemies.append([ex, ey, e_health, [], 0, random.randint(0,
                                                                                  int(ENEMY_FIRE_RATE_BASE / difficulty_scale(
                                                                                      current_level)))])
        else:
            if wave_enemies > 0:
                if len(level_enemies) <= 0:
                    wave_active = False


def update_mines():
    global mines, mine_spawn_timer
    mine_spawn_timer += 1
    interval = int(mine_spawn_interval / max(1, difficulty_scale(current_level)))
    if mine_spawn_timer >= interval:
        mine_spawn_timer = 0
        if random.random() < 0.5:
            mx, my = random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50)
            mines.append([mx, my])


def draw_menu():
    screen.fill((20, 20, 40))
    shadow_color = (0, 0, 0)
    title_text = "Городская Оборона"
    shadow = FONT.render(title_text, True, shadow_color)
    title_surface = FONT.render(title_text, True, WHITE)
    screen.blit(shadow, (title_rect.x + 3, title_rect.y + 3))
    screen.blit(title_surface, (title_rect.x, title_rect.y))
    prompt_text = "Выберите класс героя:"
    prompt_surface = FONT.render(prompt_text, True, WHITE)
    screen.blit(prompt_surface, (WIDTH // 2 - prompt_surface.get_width() // 2, title_rect.y + title_rect.height + 10))
    pygame.draw.rect(screen, sniper_button_color, sniper_button_rect)
    pygame.draw.rect(screen, tank_button_color, tank_button_rect)
    pygame.draw.rect(screen, engineer_button_color, engineer_button_rect)
    pygame.draw.rect(screen, start_button_color, start_button_rect)
    pygame.draw.rect(screen, exit_button_color, exit_button_rect)
    draw_text("Снайпер", sniper_button_rect.x + 20, sniper_button_rect.y + 15, BLACK)
    draw_text("Тяжёлый", tank_button_rect.x + 20, tank_button_rect.y + 15, BLACK)
    draw_text("Инженер", engineer_button_rect.x + 20, engineer_button_rect.y + 15, BLACK)
    draw_text("Начать игру", start_button_rect.x + 5, start_button_rect.y + 15, BLACK)
    draw_text("Выход", exit_button_rect.x + 25, exit_button_rect.y + 15, BLACK)
    draw_text("Текущий класс: " + selected_class, current_class_rect.x, current_class_rect.y, WHITE)
    pygame.display.flip()


def draw_level_title():
    global level_title_timer
    if level_title_timer > 0:
        text = f"Уровень {current_level}"
        tw = FONT.size(text)[0]
        draw_text(text, WIDTH // 2 - tw // 2, 50, WHITE)


def draw_mission_accomplished():
    global mission_accomplished_timer
    if mission_accomplished_timer > 0:
        text = "Миссия выполнена!"
        tw = FONT.size(text)[0]
        draw_text(text, WIDTH // 2 - tw // 2, HEIGHT // 2 - 20, WHITE)


def pause_screen():
    screen.fill(BLACK)
    big_font = pygame.font.SysFont("Arial", 50, bold=True)
    txt = "ПАУЗА"
    ts = big_font.render(txt, True, WHITE)
    screen.blit(ts, (WIDTH // 2 - ts.get_width() // 2, HEIGHT // 2 - 70))
    small_text1 = "Нажмите ESC, чтобы продолжить"
    small_text2 = "Нажмите R, чтобы выйти в меню"
    st1 = FONT.render(small_text1, True, WHITE)
    st2 = FONT.render(small_text2, True, WHITE)
    screen.blit(st1, (WIDTH // 2 - st1.get_width() // 2, HEIGHT // 2))
    screen.blit(st2, (WIDTH // 2 - st2.get_width() // 2, HEIGHT // 2 + 30))


def game_over_screen():
    screen.fill(BLACK)
    big_font = pygame.font.SysFont("Arial", 50, bold=True)
    txt = "ИГРА ОКОНЧЕНА"
    ts = big_font.render(txt, True, RED)
    screen.blit(ts, (WIDTH // 2 - ts.get_width() // 2, HEIGHT // 2 - 70))

    timer = threading.Timer(3.0, timer_go)
    timer.start()


def timer_go():
    pygame.quit()  # Закрываем pygame
    sys.exit()  # Закрываем программу


# --- Главный игровой цикл ---
def main_loop():
    global current_level, level_complete, game_over, boss_defeated, sniper_spot_cooldown, damage_cooldown, menu_active, selected_class, show_level_title, level_title_timer, show_mission_accomplished, mission_accomplished_timer, return_to_menu, paused, show_game_over, shoot_cooldown, restart_game
    load_cover_texture()
    while menu_active:
        handle_input_events()
        draw_menu()
        clock.tick(60)
    set_player_class(selected_class)
    start_level(current_level)
    while True:
        handle_input_events()
        # Если из режима паузы нажали R для возврата в меню, завершаем игровой цикл
        if restart_game:
            game_over_screen_reset()
            main_loop()  # Перезапуск главного цикла (возврат в главное меню)
            return
        if show_game_over:
            game_over_screen()
            pygame.display.flip()
            clock.tick(60)
            continue
        if paused:
            pause_screen()
            pygame.display.flip()
            clock.tick(60)
            continue
        if level_complete and not show_mission_accomplished:
            show_mission_accomplished = True
            mission_accomplished_timer = 120
        if show_mission_accomplished:
            mission_accomplished_timer -= 1
            if mission_accomplished_timer <= 0:
                current_level += 1
                if current_level > LEVEL_COUNT:
                    screen.fill(BLACK)
                    draw_text("Вы победили!", WIDTH // 2 - 70, HEIGHT // 2, (0, 255, 0))
                    pygame.display.flip()
                    clock.tick(60)
                    continue
                start_level(current_level)
        if show_level_title:
            level_title_timer -= 1
            if level_title_timer <= 0:
                show_level_title = False
        if not show_mission_accomplished and not show_level_title:
            if keys_pressed["r"]:
                reload_weapon()
            move_player()
            update_reload()
            update_bullets()
            update_explosions()
            enemy_ai()
            sniper_ai()
            boss_ai()
            update_hostages()
            update_bombs()
            update_items()
            update_wave()
            update_mines()
            if sniper_spot_cooldown > 0: sniper_spot_cooldown -= 1
            if damage_cooldown > 0: damage_cooldown -= 1
            if shoot_cooldown > 0: shoot_cooldown -= 1
            check_player_dead()
            check_level_complete()
        screen.fill(BG_COLOR)
        draw_covers()
        draw_bombs()
        draw_hostages()
        draw_items()
        draw_enemies()
        draw_snipers()
        draw_boss()
        draw_mines()
        draw_player()
        draw_bullet_lists()
        draw_explosions()
        draw_bomb_timers()
        draw_bars()
        minimap()
        draw_level_title()
        draw_mission_accomplished()
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main_loop()

import pygame
import sys
import random
import math
from collections import deque

pygame.init()
clock = pygame.time.Clock()
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TopDownCityDefense")
FONT = pygame.font.SysFont("Arial", 20)
BG_COLOR = (50, 50, 50)
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
score = 0
current_level = 1
game_over = False
level_enemies = []
level_snipers = []
level_boss = []
level_covers = []
level_hostages = []
level_bombs = []
level_items = []
player_armor = 0
player_max_armor = 50
player_class_list = ["sniper", "tank", "engineer"]
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
explosion_radius = 50
explosion_time = 30
damage_cooldown = 0
damage_cooldown_time = 10
keys_pressed = {"w": False, "a": False, "s": False, "d": False, "r": False, "1": False, "2": False, "3": False}
tile_size = 40
cols = WIDTH // tile_size
rows = HEIGHT // tile_size
grid_passable = [[True for _ in range(cols)] for _ in range(rows)]
ENEMY_UPDATE_RATE = 30
SNIPER_UPDATE_RATE = 30
BOSS_UPDATE_RATE = 30
ENEMY_FIRE_RATE = 60
SNIPER_FIRE_RATE = 90
BOSS_FIRE_RATE = 45


# Враг: [posX, posY, health, path, update_timer, fire_timer]
# Снайпер: [posX, posY, health, path, update_timer, fire_timer]
# Босс: [posX, posY, health, path, update_timer, fire_timer]
def draw_text(txt, x, y, color=WHITE):
    text_surface = FONT.render(txt, True, color)
    screen.blit(text_surface, (x, y))


def reset_keys():
    for k in keys_pressed:
        keys_pressed[k] = False


def handle_input_events():
    global game_over
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w: keys_pressed["w"] = True
            if event.key == pygame.K_a: keys_pressed["a"] = True
            if event.key == pygame.K_s: keys_pressed["s"] = True
            if event.key == pygame.K_d: keys_pressed["d"] = True
            if event.key == pygame.K_r: keys_pressed["r"] = True
            if event.key == pygame.K_1: keys_pressed["1"] = True
            if event.key == pygame.K_2: keys_pressed["2"] = True
            if event.key == pygame.K_3: keys_pressed["3"] = True
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_w: keys_pressed["w"] = False
            if event.key == pygame.K_a: keys_pressed["a"] = False
            if event.key == pygame.K_s: keys_pressed["s"] = False
            if event.key == pygame.K_d: keys_pressed["d"] = False
            if event.key == pygame.K_r: keys_pressed["r"] = False
            if event.key == pygame.K_1: keys_pressed["1"] = False
            if event.key == pygame.K_2: keys_pressed["2"] = False
            if event.key == pygame.K_3: keys_pressed["3"] = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                shoot_bullet()


def change_player_class():
    global player_class, player_health, player_max_health, player_armor, player_max_armor
    if keys_pressed["1"]:
        player_class = "sniper"
        player_max_health = 80
        player_health = 80
        player_max_armor = 30
        player_armor = 30
    elif keys_pressed["2"]:
        player_class = "tank"
        player_max_health = 120
        player_health = 120
        player_max_armor = 60
        player_armor = 60
    elif keys_pressed["3"]:
        player_class = "engineer"
        player_max_health = 100
        player_health = 100
        player_max_armor = 50
        player_armor = 50


def reload_weapon():
    global ammo, reload_time
    if ammo < max_ammo and reload_time <= 0:
        reload_time = reload_delay


def update_reload():
    global ammo, reload_time
    if reload_time > 0:
        reload_time -= 1
        if reload_time <= 0:
            ammo = max_ammo


def create_level_data(lv):
    global level_enemies, level_snipers, level_boss, level_covers, level_hostages, level_bombs, level_items, wave_enemies, boss_health, boss_max_health
    level_enemies = []
    level_snipers = []
    level_boss = []
    level_covers = []
    level_hostages = []
    level_bombs = []
    level_items = []
    wave_enemies = 0
    if lv < 20:
        enemy_count = min(lv * 3 + 5, 30)
        sniper_count = lv // 3
        for i in range(enemy_count):
            ex = random.randint(50, 750)
            ey = random.randint(50, 550)
            level_enemies.append([ex, ey, 100, [], 0, random.randint(0, ENEMY_FIRE_RATE)])
        for i in range(sniper_count):
            sx = random.randint(50, 750)
            sy = random.randint(50, 550)
            level_snipers.append([sx, sy, 80, [], 0, random.randint(0, SNIPER_FIRE_RATE)])
        cover_count = 5
        for i in range(cover_count):
            cx = random.randint(0, cols - 2)
            cy = random.randint(0, rows - 2)
            cw = random.randint(1, 2)
            ch = random.randint(1, 2)
            px = cx * tile_size
            py = cy * tile_size
            w = cw * tile_size
            h = ch * tile_size
            level_covers.append([px, py, w, h])
        hostage_count = 1 if lv % 2 == 0 else 2 if lv % 3 == 0 else 0
        for i in range(hostage_count):
            hx = random.randint(50, 750)
            hy = random.randint(50, 550)
            level_hostages.append([hx, hy, True])
        bomb_count = 1 if lv % 3 == 0 else 0
        for i in range(bomb_count):
            bx = random.randint(50, 750)
            by = random.randint(50, 550)
            level_bombs.append([bx, by, 300])
        item_count = 3
        for i in range(item_count):
            ix = random.randint(50, 750)
            iy = random.randint(50, 550)
            itype = random.choice(["health", "ammo", "armor"])
            level_items.append([ix, iy, itype])
    else:
        boss_health = 300
        boss_max_health = 300
        level_boss.append([400, 300, boss_health, [], 0, random.randint(0, BOSS_FIRE_RATE)])
        cover_count = 5
        for i in range(cover_count):
            cx = random.randint(0, cols - 2)
            cy = random.randint(0, rows - 2)
            cw = random.randint(1, 2)
            ch = random.randint(1, 2)
            px = cx * tile_size
            py = cy * tile_size
            w = cw * tile_size
            h = ch * tile_size
            level_covers.append([px, py, w, h])
        item_count = 5
        for i in range(item_count):
            ix = random.randint(50, 750)
            iy = random.randint(50, 550)
            itype = random.choice(["health", "ammo", "armor"])
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
    gx = int(x // tile_size)
    gy = int(y // tile_size)
    return gx, gy


def get_pixel_center(gx, gy):
    px = gx * tile_size + tile_size // 2
    py = gy * tile_size + tile_size // 2
    return px, py


# Поиск случайной точки рядом с игроком, чтобы враги не толпились прямо в одной точке
def get_random_tile_near_player(px, py, radius=3, attempts=10):
    gx, gy = get_grid_pos(px, py)
    for i in range(attempts):
        rx = random.randint(gx - radius, gx + radius)
        ry = random.randint(gy - radius, gy + radius)
        if 0 <= rx < cols and 0 <= ry < rows and grid_passable[ry][rx]:
            return rx, ry
    return gx, gy


# BFS для поиска пути к случайной точке около игрока
def bfs_pathfind(startx, starty, endgx, endgy):
    sx, sy = get_grid_pos(startx, starty)
    if sx < 0 or sx >= cols or sy < 0 or sy >= rows: return []
    if endgx < 0 or endgx >= cols or endgy < 0 or endgy >= rows: return []
    if not grid_passable[sy][sx]: return []
    if not grid_passable[endgy][endgx]: return []
    visited = [[False for _ in range(cols)] for _ in range(rows)]
    parent = dict()
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
    player_x = WIDTH // 2
    player_y = HEIGHT // 2
    player_health = player_max_health
    player_armor = player_max_armor
    ammo = max_ammo


def start_level(lv):
    global level_complete, current_level, boss_defeated
    level_complete = False
    boss_defeated = False
    create_level_data(lv)
    reset_player()
    fill_grid_passable()


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
    global shots_fired, ammo
    if ammo > 0 and reload_time <= 0:
        mx, my = pygame.mouse.get_pos()
        angle = math.atan2(my - player_y, mx - player_x)
        speed = 10
        shots_fired.append([player_x, player_y, angle, speed])
        ammo -= 1


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


def update_bullets():
    global shots_fired, enemy_shots, sniper_shots, boss_shots, level_enemies, level_snipers, level_boss, boss_defeated, score, explosions
    new_player_bullets = []
    for b in shots_fired:
        bx, by, ang, spd = b
        bx += math.cos(ang) * spd
        by += math.sin(ang) * spd
        if bx < 0 or bx > WIDTH or by < 0 or by > HEIGHT: continue
        if collide_with_covers(bx, by, 5):
            explosions.append([bx, by, explosion_radius, explosion_time])
            continue
        hit = False
        for e in level_enemies:
            if math.hypot(bx - e[0], by - e[1]) < 10:
                e[2] -= 40
                if e[2] <= 0:
                    score += 10
                    level_enemies.remove(e)
                explosions.append([bx, by, explosion_radius, explosion_time])
                hit = True
                break
        if hit: continue
        for s in level_snipers:
            if math.hypot(bx - s[0], by - s[1]) < 10:
                s[2] -= 50
                if s[2] <= 0:
                    score += 15
                    level_snipers.remove(s)
                explosions.append([bx, by, explosion_radius, explosion_time])
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
                    explosions.append([bx, by, explosion_radius, explosion_time])
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
            explosions.append([bx, by, explosion_radius, explosion_time])
            continue
        dist = math.hypot(bx - player_x, by - player_y)
        if dist < 10:
            take_damage(10)
            explosions.append([bx, by, explosion_radius, explosion_time])
            continue
        new_enemy_bullets.append([bx, by, ang, spd])
    enemy_shots = new_enemy_bullets
    new_sniper_bullets = []
    for sb in sniper_shots:
        bx, by, ang, spd = sb
        bx += math.cos(ang) * spd
        by += math.sin(ang) * spd
        if bx < 0 or bx > WIDTH or by < 0 or by > HEIGHT: continue
        if collide_with_covers(bx, by, 5):
            explosions.append([bx, by, explosion_radius, explosion_time])
            continue
        dist = math.hypot(bx - player_x, by - player_y)
        if dist < 10:
            take_damage(15)
            explosions.append([bx, by, explosion_radius, explosion_time])
            continue
        new_sniper_bullets.append([bx, by, ang, spd])
    sniper_shots = new_sniper_bullets
    new_boss_bullets = []
    for bb in boss_shots:
        bx, by, ang, spd = bb
        bx += math.cos(ang) * spd
        by += math.sin(ang) * spd
        if bx < 0 or bx > WIDTH or by < 0 or by > HEIGHT: continue
        if collide_with_covers(bx, by, 5):
            explosions.append([bx, by, explosion_radius, explosion_time])
            continue
        dist = math.hypot(bx - player_x, by - player_y)
        if dist < 15:
            take_damage(20)
            explosions.append([bx, by, explosion_radius, explosion_time])
            continue
        new_boss_bullets.append([bx, by, ang, spd])
    boss_shots = new_boss_bullets


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
    for exp in explosions:
        ex, ey, r, t = exp
        alpha = t / explosion_time
        rr = int(r * (1 - alpha))
        pygame.draw.circle(screen, (255, 150, 0), (int(ex), int(ey)), rr)


# Функция пересчёта пути для врага, чтобы он шел к случайной точке около игрока
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
    global player_health, game_over
    if player_health <= 0:
        game_over = True


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
    for c in level_covers:
        pygame.draw.rect(screen, COVER_COLOR, pygame.Rect(c[0], c[1], c[2], c[3]))


def draw_hostages():
    for h in level_hostages:
        if h[2]:
            pygame.draw.circle(screen, HOSTAGE_COLOR, (int(h[0]), int(h[1])), 8)


def draw_bombs():
    for b in level_bombs:
        if b[2] > 0:
            pygame.draw.circle(screen, BOMB_COLOR, (int(b[0]), int(b[1])), 6)


def draw_items():
    for it in level_items:
        pygame.draw.circle(screen, ITEM_COLOR, (int(it[0]), int(it[1])), 6)


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
    global level_bombs, explosions
    bx, by, t = b
    explosions.append([bx, by, explosion_radius, explosion_time])
    for i in range(len(level_bombs)):
        if level_bombs[i] == b:
            level_bombs[i][2] = 0
    dist = math.hypot(bx - player_x, by - player_y)
    if dist < 50:
        take_damage(50)


def update_items():
    global level_items, player_health, player_max_health, ammo, max_ammo, player_armor, player_max_armor
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
    draw_text("HP:" + str(player_health), 10, 40)
    draw_text("Armor:" + str(player_armor), 10, 60)
    draw_text("Ammo:" + str(ammo), 10, 80)
    draw_text("Score:" + str(score), 10, 100)
    draw_text("Level:" + str(current_level), 10, 120)
    if reload_time > 0:
        draw_text("Reloading...", 10, 140)


def draw_bomb_timers():
    for b in level_bombs:
        if b[2] > 0:
            draw_text(str(b[2] // 60), b[0] - 10, b[1] - 20, RED)


def minimap():
    mm_w = int(WIDTH * minimap_scale)
    mm_h = int(HEIGHT * minimap_scale)
    pygame.draw.rect(screen, BLACK, (WIDTH - mm_w - 10, 10, mm_w, mm_h))
    px = int((player_x / WIDTH) * mm_w)
    py = int((player_y / HEIGHT) * mm_h)
    pygame.draw.circle(screen, class_colors.get(player_class, (0, 200, 0)), (WIDTH - mm_w - 10 + px, 10 + py), 2)
    for e in level_enemies:
        ex = int((e[0] / WIDTH) * mm_w)
        ey = int((e[1] / HEIGHT) * mm_h)
        pygame.draw.circle(screen, ENEMY_COLOR, (WIDTH - mm_w - 10 + ex, 10 + ey), 2)
    for s in level_snipers:
        sx = int((s[0] / WIDTH) * mm_w)
        sy = int((s[1] / HEIGHT) * mm_h)
        pygame.draw.circle(screen, SNIPER_COLOR, (WIDTH - mm_w - 10 + sx, 10 + sy), 2)
    for bs in level_boss:
        bx = int((bs[0] / WIDTH) * mm_w)
        by = int((bs[1] / HEIGHT) * mm_h)
        pygame.draw.circle(screen, BOSS_COLOR, (WIDTH - mm_w - 10 + bx, 10 + by), 4)
    for h in level_hostages:
        if h[2]:
            hx = int((h[0] / WIDTH) * mm_w)
            hy = int((h[1] / HEIGHT) * mm_h)
            pygame.draw.circle(screen, HOSTAGE_COLOR, (WIDTH - mm_w - 10 + hx, 10 + hy), 2)
    for b in level_bombs:
        if b[2] > 0:
            bx = int((b[0] / WIDTH) * mm_w)
            by = int((b[1] / HEIGHT) * mm_h)
            pygame.draw.circle(screen, BOMB_COLOR, (WIDTH - mm_w - 10 + bx, 10 + by), 2)


def update_wave():
    global wave_timer, wave_active, wave_enemies, level_enemies
    if current_level < 20:
        if not wave_active:
            wave_timer += 1
            if wave_timer >= wave_interval:
                wave_active = True
                wave_timer = 0
                wave_enemies = random.randint(3, 6)
                for i in range(wave_enemies):
                    ex = random.randint(50, 750)
                    ey = random.randint(50, 550)
                    level_enemies.append([ex, ey, 100, [], 0, random.randint(0, ENEMY_FIRE_RATE)])
        else:
            if wave_enemies > 0:
                if len(level_enemies) <= 0:
                    wave_active = False


def main_loop():
    global current_level, level_complete, game_over, boss_defeated, sniper_spot_cooldown, damage_cooldown
    start_level(current_level)
    while True:
        handle_input_events()
        if game_over:
            screen.fill(BLACK)
            draw_text("GAME OVER! Press ESC to Quit.", WIDTH // 2 - 150, HEIGHT // 2, RED)
            pygame.display.flip()
            clock.tick(60)
            continue
        if level_complete:
            current_level += 1
            if current_level > LEVEL_COUNT:
                screen.fill(BLACK)
                draw_text("CONGRATS! YOU WON!", WIDTH // 2 - 100, HEIGHT // 2, (0, 255, 0))
                pygame.display.flip()
                clock.tick(60)
                continue
            start_level(current_level)
        change_player_class()
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
        if sniper_spot_cooldown > 0: sniper_spot_cooldown -= 1
        if damage_cooldown > 0: damage_cooldown -= 1
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
        draw_player()
        draw_bullet_lists()
        draw_explosions()
        draw_bomb_timers()
        draw_bars()
        minimap()
        pygame.display.flip()
        clock.tick(60)


main_loop()

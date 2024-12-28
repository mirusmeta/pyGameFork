import pygame
import math

# Инициализация Pygame
pygame.init()

# Параметры экрана
WIDTH, HEIGHT = 800, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Городской бой")

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (200, 200, 200)
BLUE = (0, 0, 255)
DARK_RED = (200, 0, 0)
GREEN = (0, 255, 0)

# Шрифт
FONT = pygame.font.Font(None, 36)
SMALL_FONT = pygame.font.Font(None, 24)

# Уровень
level = 1

# Камера
camera_offset = [0, 0]

# Игрок
player_width, player_height = 40, 40
player_pos = [WIDTH // 2, HEIGHT // 2]
player_speed = 5

# Пули
bullets = []
bullet_speed = 10
bullet_count = 16
MAX_BULLETS = 16

# Загрузка текстуры пули
bullet_image = pygame.image.load("images/bullet.png")
bullet_image = pygame.transform.scale(bullet_image, (40, 20))

# Загрузка звуков
shoot_sound = pygame.mixer.Sound("sounds/shoot.mp3")
reload_sound = pygame.mixer.Sound("sounds/reload.mp3")
release_sound = pygame.mixer.Sound("sounds/release.mp3")

# Размер карты
MAP_WIDTH, MAP_HEIGHT = 1600, 1200
SCENE_WIDTH, SCENE_HEIGHT = 800, 600
SCENE_X, SCENE_Y = (MAP_WIDTH - SCENE_WIDTH) // 2, (MAP_HEIGHT - SCENE_HEIGHT) // 2

# Функция рисования сетки и границы сцены
def draw_scene(surface, offset):
    for x in range(0, MAP_WIDTH, 50):
        pygame.draw.line(surface, GRAY, (x - offset[0], 0 - offset[1]), (x - offset[0], MAP_HEIGHT - offset[1]))
    for y in range(0, MAP_HEIGHT, 50):
        pygame.draw.line(surface, GRAY, (0 - offset[0], y - offset[1]), (MAP_WIDTH - offset[0], y - offset[1]))

    pygame.draw.rect(surface, RED, (SCENE_X - offset[0], SCENE_Y - offset[1], SCENE_WIDTH, SCENE_HEIGHT), 3)

# Функция рисования круглой миникарты
def draw_minimap(surface, player_pos):
    minimap_radius = 75
    minimap_center = (WIDTH - minimap_radius - 20, minimap_radius + 20)
    pygame.draw.circle(surface, WHITE, minimap_center, minimap_radius)
    pygame.draw.circle(surface, RED, minimap_center, minimap_radius, 2)

    pygame.draw.circle(surface, GREEN, minimap_center, 5)

# Функция стрельбы
def shoot_bullet(start_pos, direction):
    global bullet_count
    if bullet_count > 0:
        bullets.append({
            "pos": list(start_pos),
            "dir": direction,
            "angle": direction.angle_to(pygame.math.Vector2(1, 0))
        })
        shoot_sound.play()
        bullet_count -= 1
    else:
        release_sound.play()

# Основной игровой цикл
clock = pygame.time.Clock()
running = True
show_reload_toast = False
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            world_x = mouse_x + camera_offset[0]
            world_y = mouse_y + camera_offset[1]
            direction = pygame.math.Vector2(world_x - player_pos[0], world_y - player_pos[1]).normalize()
            distance = math.hypot(world_x - player_pos[0], world_y - player_pos[1])
            if distance > player_width // 2:
                shoot_bullet(player_pos, direction)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                bullet_count = MAX_BULLETS
                reload_sound.play()
                show_reload_toast = False

    # Управление игроком
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        player_pos[1] -= player_speed
    if keys[pygame.K_s]:
        player_pos[1] += player_speed
    if keys[pygame.K_a]:
        player_pos[0] -= player_speed
    if keys[pygame.K_d]:
        player_pos[0] += player_speed

    # Ограничение движения игрока в границах сцены с учётом его размера
    player_pos[0] = max(SCENE_X + player_width // 2, min(SCENE_X + SCENE_WIDTH - player_width // 2, player_pos[0]))
    player_pos[1] = max(SCENE_Y + player_height // 2, min(SCENE_Y + SCENE_HEIGHT - player_height // 2, player_pos[1]))

    # Центрирование камеры на игроке
    camera_offset[0] = player_pos[0] - WIDTH // 2
    camera_offset[1] = player_pos[1] - HEIGHT // 2

    # Обновление пуль
    for bullet in bullets:
        bullet["pos"][0] += bullet["dir"].x * bullet_speed
        bullet["pos"][1] += bullet["dir"].y * bullet_speed

    # Удаление пуль за пределами карты
    bullets = [bullet for bullet in bullets if 0 <= bullet["pos"][0] <= MAP_WIDTH and 0 <= bullet["pos"][1] <= MAP_HEIGHT]

    # Отрисовка
    SCREEN.fill(WHITE)
    draw_scene(SCREEN, camera_offset)

    # Отрисовка игрока
    pygame.draw.rect(SCREEN, GREEN, (player_pos[0] - player_width // 2 - camera_offset[0],
                                     player_pos[1] - player_height // 2 - camera_offset[1],
                                     player_width, player_height))

    # Отрисовка пуль
    for bullet in bullets:
        rotated_bullet = pygame.transform.rotate(bullet_image, -bullet["angle"])
        bullet_rect = rotated_bullet.get_rect(center=(bullet["pos"][0] - camera_offset[0], bullet["pos"][1] - camera_offset[1]))
        SCREEN.blit(rotated_bullet, bullet_rect)

    # Отображение уровня
    level_text = FONT.render(f"Level: {level}", True, BLACK)
    SCREEN.blit(level_text, (10, 10))

    # Отображение количества пуль
    bullet_color = RED if bullet_count < 3 else BLACK
    bullet_count_text = FONT.render(f"Bullets: {bullet_count}", True, bullet_color)
    SCREEN.blit(bullet_count_text, (10, 50))

    # Показать сообщение о перезарядке
    if bullet_count == 0:
        show_reload_toast = True
    if show_reload_toast:
        reload_text = SMALL_FONT.render("Press R to reload", True, DARK_RED)
        SCREEN.blit(reload_text, (WIDTH // 2 - reload_text.get_width() // 2, HEIGHT - 30))

    # Отрисовка миникарты
    draw_minimap(SCREEN, player_pos)

    # Обновление экрана
    pygame.display.flip()
    clock.tick(60)

pygame.quit()

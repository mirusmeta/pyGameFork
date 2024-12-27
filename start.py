import pygame

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
ORANGE = (255, 165, 0)
BLUE = (0, 0, 255)

# Шрифт
FONT = pygame.font.Font(None, 36)

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

# Функция рисования миникарты
def draw_minimap(surface, player_pos):
    minimap_width, minimap_height = 200, 150
    minimap_x, minimap_y = WIDTH - minimap_width - 10, 10
    pygame.draw.rect(surface, WHITE, (minimap_x, minimap_y, minimap_width, minimap_height))

    # Пропорции миникарты относительно красной зоны
    scale_x = minimap_width / SCENE_WIDTH
    scale_y = minimap_height / SCENE_HEIGHT

    # Рисование зоны сцены
    scene_rect = pygame.Rect(
        minimap_x,
        minimap_y,
        minimap_width,
        minimap_height
    )
    pygame.draw.rect(surface, RED, scene_rect, 2)

    # Рисование игрока на миникарте
    player_marker = pygame.Rect(
        minimap_x + (player_pos[0] - SCENE_X) * scale_x - player_width * scale_x // 2,
        minimap_y + (player_pos[1] - SCENE_Y) * scale_y - player_height * scale_y // 2,
        player_width * scale_x,
        player_height * scale_y
    )
    pygame.draw.rect(surface, BLACK, player_marker)

# Функция стрельбы
def shoot_bullet(start_pos, direction):
    bullets.append({
        "pos": list(start_pos),
        "dir": direction
    })

# Основной игровой цикл
clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            world_x = mouse_x + camera_offset[0]
            world_y = mouse_y + camera_offset[1]
            direction = pygame.math.Vector2(world_x - player_pos[0], world_y - player_pos[1]).normalize()
            shoot_bullet(player_pos, direction)

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
    pygame.draw.rect(SCREEN, BLACK, (player_pos[0] - player_width // 2 - camera_offset[0],
                                     player_pos[1] - player_height // 2 - camera_offset[1],
                                     player_width, player_height))

    # Отрисовка пуль
    for bullet in bullets:
        pygame.draw.rect(SCREEN, ORANGE, (bullet["pos"][0] - camera_offset[0],
                                          bullet["pos"][1] - camera_offset[1],
                                          10, 5))

    # Отображение уровня
    level_text = FONT.render(f"Level: {level}", True, BLACK)
    SCREEN.blit(level_text, (10, 10))

    # Отрисовка миникарты
    draw_minimap(SCREEN, player_pos)

    # Обновление экрана
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
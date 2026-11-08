"""
Константы и настройки игры.
Содержит все конфигурационные параметры: размеры экрана, физические свойства игрока,
оружия, врагов, параметры карты, интерфейса и цветовые палитры.
"""

# Настройки экрана и игрового цикла
WIDTH = 1280
HEIGHT = 720
FPS = 60
GAME_TITLE = "Night Siege: Last Stand"

# Параметры игрока
PLAYER_SPRITE = "player.png"
PLAYER_SPRITE_SIZE = 64
PLAYER_SPEED = 5
PLAYER_RADIUS = 24
PLAYER_MAX_HP = 100
PLAYER_DAMAGE_COOLDOWN = 0.7  # Задержка получения урона (в секундах)
PLAYER_DASH_DISTANCE = 150  # Длина рывка по нажатию Space
PLAYER_DASH_COOLDOWN = 2.5  # Перезарядка рывка в секундах
PLAYER_AIM_LENGTH = 40
PLAYER_AIM_WIDTH = 3
PLAYER_VISIBILITY_RADIUS = 200  # Радиус полной видимости вокруг игрока
PLAYER_VISIBILITY_FADE = 140    # Ширина области размытия темноты
PLAYER_VISIBILITY_FADE_STEPS = 10
PLAYER_STEP_SOUND = "steps_neon.wav"
PLAYER_STEP_SOUND_VOLUME = 0.35
DIAGONAL_SCALE = 0.707  # Множитель скорости при движении по диагонали

# Параметры пуль
BULLET_SPEED = 50
BULLET_SPRITE = "bullet_texture.png"
BULLET_SPRITE_SIZE = (24, 10)
BULLET_RADIUS = 5
BULLET_MAX_DISTANCE = 2000
BULLET_MOVE_STEPS = 8  # Количество шагов проверки коллизий за один кадр (для предотвращения прохождения сквозь стены)
BULLET_DAMAGE = 1
BULLET_SHOT_SOUND = "shot_neon.wav"
BULLET_SHOT_SOUND_VOLUME = 0.45

# Параметры врагов (зомби)
ENEMY_SPRITE = "zombie.png"
ENEMY_SPRITE_SIZE = 60
ENEMY_SPEED = 2
ENEMY_RADIUS = 26
ENEMY_HP = 3
ENEMY_DAMAGE = 15
ENEMY_REPATH_TIME = 0.5  # Частота обновления пути до игрока (в секундах)
ENEMY_WAYPOINT_REACH = 12  # Дистанция, на которой путевая точка считается достигнутой
ENEMY_HIT_TINT = (55, 20, 10, 0)  # Цвет вспышки при получении урона
ENEMY_HIT_FLASH_TIME = 0.15  # Длительность вспышки урона (в секундах)
ENEMY_HP_BAR_WIDTH = 28
ENEMY_HP_BAR_HEIGHT = 4
ENEMY_HP_BAR_OFFSET = ENEMY_SPRITE_SIZE // 2 + 8
ENEMY_HP_BAR_BG = (70, 20, 20)
ENEMY_HP_BAR_FILL = (220, 40, 40)
ZOMBIE_AMBIENT_SOUND = "zombie_ambient_neon.wav"
ZOMBIE_AMBIENT_SOUND_VOLUME = 0.25

# Настройки волн врагов
WAVE_BASE_COUNT = 3  # Количество врагов на первой волне
WAVE_COUNT_PER_LEVEL = 1  # На сколько увеличивается количество врагов с каждой волной
SPAWN_DISTANCE = 120  # Минимальная дистанция спавна врагов от игрока
SPAWN_RETRY_COUNT = 24  # Количество попыток найти точку спавна при коллизиях
SPAWN_MIN_GAP = ENEMY_RADIUS * 2 + 8  # Минимальное расстояние между спавнящимися врагами

# Параметры карты и объектов
MAP_WIDTH = 2200
MAP_HEIGHT = 1600
WALL_THICKNESS = 28
WINDOW_WIDTH = 100
DOOR_WIDTH = 110
FLOOR_TEXTURE = "floor_texture.png"
WALL_TEXTURE = "wall_texture.png"
WINDOW_TEXTURE = "broken_window_texture.png"
BOARD_TEXTURE = "board_texture.png"

# Параметры баррикад на окнах
BOARD_HITS = 8  # Прочность одной доски (количество ударов зомби)
BOARD_SEGMENT_SIZE = 48
BOARD_INTERACT_DISTANCE = 90  # Максимальное расстояние взаимодействия с окном
BOARD_DRAW_MARGIN = 1
BOARD_DRAW_INSET = 2
ZOMBIE_BOARD_ATTACK_COOLDOWN = 1.0  # Задержка между ударами зомби по доскам (в секундах)
ZOMBIE_BOARD_ATTACK_RANGE = 10  # Дальность атаки зомби по доскам
BOARD_HIT_SOUND = "board_hit_neon.wav"
BOARD_HIT_SOUND_VOLUME = 0.7

# Параметры сетки навигации (A*)
NAV_CELL_SIZE = 32
NAV_OBSTACLE_PADDING = 12  # Отступ вокруг стен для безопасного обхода врагами
NAV_SEARCH_RADIUS = 8  # Радиус поиска проходимой ячейки, если старт/финиш заблокированы

# Настройки интерфейса (HUD)
HUD_FONT_SIZE = 28
HUD_X = 10
HUD_HP_Y = 10
HUD_WAVE_Y = 40
HUD_HINT_Y = 70
HUD_SCORE_Y = 100
HUD_DASH_Y = 130

# Настройки меню
MENU_TITLE_FONT_SIZE = 76
MENU_FONT_SIZE = 42
MENU_SMALL_FONT_SIZE = 26
MENU_TITLE_Y = 150
MENU_SUBTITLE_Y = 205
MENU_FIRST_ITEM_Y = 285
MENU_ITEM_GAP = 52
MENU_HINT_Y_OFFSET = 45
MENU_OVERLAY_ALPHA = 180
MENU_DISABLED_COLOR = (120, 120, 120)

# Цветовая палитра (RGB)
COLOR_BG = (12, 16, 24)
COLOR_FLOOR = (45, 42, 38)
COLOR_WALL = (70, 68, 62)
COLOR_WINDOW = (90, 130, 160)
COLOR_WINDOW_BOARDED = (100, 75, 45)
COLOR_PLAYER = (0, 255, 0)
COLOR_PLAYER_AIM = (0, 255, 255)
COLOR_BULLET = (255, 255, 0)
COLOR_ENEMY = (200, 50, 50)
COLOR_UI = (235, 242, 255)
COLOR_UI_ACCENT = (95, 220, 255)
COLOR_UI_WARM = (255, 148, 82)
MENU_PANEL_COLOR = (7, 17, 31)
MENU_PANEL_BORDER = (44, 178, 205)
MENU_SELECTED_COLOR = (20, 78, 96)
MENU_MUTED_COLOR = (120, 145, 160)

"""
Модуль игровой карты и интерактивных окон (баррикад).
Описывает структуру карты (GameMap), стен, полов, окон (Window),
а также логику коллизий круглых объектов со стенами и баррикадами,
и атаки зомби на заколоченные досками окна.
"""

import math
from typing import List, Tuple, Optional

import pygame

from assets import load_image
from settings import (
    BOARD_TEXTURE,
    BOARD_DRAW_INSET,
    BOARD_DRAW_MARGIN,
    BOARD_HITS,
    BOARD_INTERACT_DISTANCE,
    BOARD_SEGMENT_SIZE,
    DOOR_WIDTH,
    ENEMY_RADIUS,
    FLOOR_TEXTURE,
    MAP_HEIGHT,
    MAP_WIDTH,
    WALL_THICKNESS,
    WALL_TEXTURE,
    WINDOW_TEXTURE,
    WINDOW_WIDTH,
    ZOMBIE_BOARD_ATTACK_COOLDOWN,
    ZOMBIE_BOARD_ATTACK_RANGE,
)
from utils import distance, tick_down


def load_texture(filename: str) -> pygame.Surface:
    """
    Вспомогательная функция для загрузки непрозрачных текстур (стен, полов).
    Отключает альфа-канал для оптимизации производительности Pygame.
    """
    return load_image(filename, alpha=False)


def draw_textured_rect(
    screen: pygame.Surface,
    texture: pygame.Surface,
    rect: pygame.Rect,
    camera: "Camera",
) -> None:
    """
    Отрисовывает прямоугольную область, замостив её текстурой.
    Учитывает положение камеры и отсекает отрисовку за пределами экрана.

    :param screen: Экран отрисовки (pygame.Surface).
    :param texture: Текстура для замощения (pygame.Surface).
    :param rect: Мировой прямоугольник области (pygame.Rect).
    :param camera: Объект камеры.
    """
    # Преобразуем мировые координаты прямоугольника в экранные
    screen_rect = pygame.Rect(
        int(rect.x - camera.x),
        int(rect.y - camera.y),
        rect.width,
        rect.height,
    )
    # Отсекаем части прямоугольника, выходящие за границы экрана
    clipped_rect = screen_rect.clip(screen.get_rect())
    if clipped_rect.width <= 0 or clipped_rect.height <= 0:
        return

    tile_width, tile_height = texture.get_size()
    # Вычисляем мировые координаты левого верхнего угла видимой части
    world_left = int(clipped_rect.left + camera.x)
    world_top = int(clipped_rect.top + camera.y)

    # Находим точку начала замощения текстурой (выравнивание по сетке текстуры)
    start_world_x = world_left - world_left % tile_width
    start_world_y = world_top - world_top % tile_height
    start_x = int(start_world_x - camera.x)
    start_y = int(start_world_y - camera.y)

    # Сохраняем старую область отсечения и устанавливаем новую для точной отрисовки
    old_clip = screen.get_clip()
    screen.set_clip(clipped_rect)

    # Замащиваем область текстурой
    for y in range(start_y, clipped_rect.bottom, tile_height):
        for x in range(start_x, clipped_rect.right, tile_width):
            screen.blit(texture, (x, y))

    # Восстанавливаем исходную область отсечения экрана
    screen.set_clip(old_clip)


class Window:
    """
    Класс окна, которое игрок может заколачивать досками (баррикадировать),
    а зомби — атаковать и ломать, чтобы проникнуть внутрь здания.
    """

    def __init__(self, rect: pygame.Rect, side: str) -> None:
        """
        Инициализирует окно.

        :param rect: Прямоугольник окна на карте (pygame.Rect).
        :param side: Сторона света, с которой находится внешняя часть окна ("top", "bottom", "left", "right").
                     Используется для спавна зомби снаружи.
        """
        self.rect = pygame.Rect(rect)
        self.side = side
        # Список досок на окне. Каждое число в списке — прочность (HP) конкретной доски.
        # Первая доска в списке ломается первой.
        self.boards = []
        self._attack_cooldown = 0.0  # Кулдаун атак зомби по этому окну

    @property
    def max_boards(self) -> int:
        """
        Вычисляет максимальное количество досок, которое помещается на окно в зависимости от его размера.
        """
        length = max(self.rect.width, self.rect.height)
        return max(1, length // BOARD_SEGMENT_SIZE)

    @property
    def has_boards(self) -> bool:
        """
        Возвращает True, если на окне есть хотя бы одна доска.
        """
        return bool(self.boards)

    @property
    def is_fully_boarded(self) -> bool:
        """
        Проверяет, заколочено ли окно до предела.
        """
        return len(self.boards) >= self.max_boards

    def blocks_movement(self, for_enemy: bool = False) -> bool:
        """
        Определяет, блокирует ли окно движение.
        Для игрока окно заблокировано всегда (он не может проходить сквозь окна).
        Для зомби окно заблокировано только тогда, когда на нём есть доски.

        :param for_enemy: True, если проверка выполняется для зомби.
        """
        return self.has_boards if for_enemy else True

    def add_board(self) -> bool:
        """
        Добавляет одну доску на окно, если оно ещё не заколочено полностью.

        :return: True, если доска успешно добавлена, иначе False.
        """
        if self.is_fully_boarded:
            return False
        self.boards.append(BOARD_HITS)
        return True

    def damage_board(self, amount: int = 1) -> None:
        """
        Наносит урон первой доске на окне. Если её прочность падает до 0, она ломается (удаляется).

        :param amount: Наносимый урон.
        """
        if not self.boards:
            return
        self.boards[0] -= amount
        if self.boards[0] <= 0:
            self.boards.pop(0)

    def distance_to(self, x: float, y: float) -> float:
        """
        Вычисляет кратчайшее расстояние от точки (x, y) до прямоугольника окна.
        """
        cx = max(self.rect.left, min(x, self.rect.right))
        cy = max(self.rect.top, min(y, self.rect.bottom))
        return distance(x, y, cx, cy)

    def draw(
        self,
        screen: pygame.Surface,
        camera: "Camera",
        window_texture: pygame.Surface,
        vertical_window_texture: pygame.Surface,
        board_texture: pygame.Surface,
        vertical_board_texture: pygame.Surface,
    ) -> None:
        """
        Отрисовывает окно и установленные на нём доски.

        :param screen: Экран отрисовки.
        :param camera: Объект камеры.
        :param window_texture: Текстура горизонтального окна.
        :param vertical_window_texture: Текстура вертикального окна.
        :param board_texture: Текстура горизонтальной доски.
        :param vertical_board_texture: Текстура вертикальной доски.
        """
        horizontal = self.rect.width >= self.rect.height
        # Отрисовываем само разбитое окно
        draw_textured_rect(
            screen,
            window_texture if horizontal else vertical_window_texture,
            self.rect,
            camera,
        )
        if not self.boards:
            return

        # Отрисовываем доски поверх окна
        segment_count = self.max_boards
        segment_length = (
            self.rect.width / segment_count
            if horizontal
            else self.rect.height / segment_count
        )

        for i in range(len(self.boards)):
            if horizontal:
                seg = pygame.Rect(
                    self.rect.x + int(i * segment_length) + BOARD_DRAW_MARGIN,
                    self.rect.y + BOARD_DRAW_MARGIN,
                    int(segment_length) - BOARD_DRAW_INSET,
                    self.rect.height - BOARD_DRAW_INSET,
                )
                texture = board_texture
            else:
                seg = pygame.Rect(
                    self.rect.x + BOARD_DRAW_MARGIN,
                    self.rect.y + int(i * segment_length) + BOARD_DRAW_MARGIN,
                    self.rect.width - BOARD_DRAW_INSET,
                    int(segment_length) - BOARD_DRAW_INSET,
                )
                texture = vertical_board_texture
            draw_textured_rect(screen, texture, seg, camera)

    def spawn_outside(self, offset: float) -> Tuple[float, float]:
        """
        Вычисляет точку спавна врага снаружи здания напротив этого окна.

        :param offset: Расстояние от окна, на котором должен появиться враг.
        :return: Кортеж (x, y) мировых координат точки спавна.
        """
        offsets = {
            "top": (self.rect.centerx, self.rect.top - offset),
            "bottom": (self.rect.centerx, self.rect.bottom + offset),
            "left": (self.rect.left - offset, self.rect.centery),
            "right": (self.rect.right + offset, self.rect.centery),
        }
        return offsets[self.side]


class GameMap:
    """
    Класс игровой карты. Хранит стены, полы, окна, спавн-поинт игрока,
    а также управляет коллизиями и взаимодействием с окнами.
    """

    def __init__(self) -> None:
        """
        Инициализирует карту, загружает текстуры и строит планировку уровня.
        """
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self.walls = []  # Список прямоугольников стен (pygame.Rect)
        self.windows = []  # Список объектов окон (Window)
        self.floor_rects = []  # Список прямоугольников пола (pygame.Rect)
        self.spawn_point = (0.0, 0.0)  # Точка появления игрока

        # Загружаем и подготавливаем текстуры
        self.floor_texture = load_texture(FLOOR_TEXTURE)
        self.wall_texture = load_texture(WALL_TEXTURE)
        self.window_texture = load_texture(WINDOW_TEXTURE)
        self.vertical_window_texture = pygame.transform.rotate(self.window_texture, 90)
        self.board_texture = load_texture(BOARD_TEXTURE)
        self.vertical_board_texture = pygame.transform.rotate(self.board_texture, 90)

        # Строим геометрию уровня
        self._build_layout()

    def _wall(self, x: float, y: float, w: float, h: float) -> None:
        """
        Вспомогательный метод для добавления стены.
        """
        if w > 0 and h > 0:
            self.walls.append(pygame.Rect(x, y, w, h))

    def _corner(self, x: float, y: float) -> None:
        """
        Вспомогательный метод для добавления угловой колонны (квадратной стены).
        """
        self._wall(x, y, WALL_THICKNESS, WALL_THICKNESS)

    def _floor(self, x: float, y: float, w: float, h: float) -> None:
        """
        Вспомогательный метод для добавления прямоугольной зоны пола.
        """
        if w > 0 and h > 0:
            self.floor_rects.append(pygame.Rect(x, y, w, h))

    def _add_window(self, rect: pygame.Rect, side: str) -> None:
        """
        Добавляет новое окно на карту.
        """
        self.windows.append(Window(rect, side))

    def _window_h(self, x_center: float, y: float, side: str) -> None:
        """
        Добавляет горизонтальное окно с центром в x_center.
        """
        self._add_window(
            pygame.Rect(x_center - WINDOW_WIDTH // 2, y, WINDOW_WIDTH, WALL_THICKNESS),
            side,
        )

    def _window_v(self, x: float, y_center: float, side: str) -> None:
        """
        Добавляет вертикальное окно с центром в y_center.
        """
        self._add_window(
            pygame.Rect(x, y_center - WINDOW_WIDTH // 2, WALL_THICKNESS, WINDOW_WIDTH),
            side,
        )

    def _wall_with_openings(
        self,
        start: float,
        end: float,
        fixed: float,
        windows: List[float],
        gaps: List[float],
        horizontal: bool,
        side: str,
    ) -> None:
        """
        Строит стену на отрезке от start до end, автоматически размещая в ней
        окна и дверные проемы (gaps).

        :param start, end: Начальная и конечная координата стены вдоль её направления.
        :param fixed: Фиксированная координата стены по перпендикулярной оси.
        :param windows: Список координат центров окон.
        :param gaps: Список координат центров дверных проемов.
        :param horizontal: True, если стена горизонтальная, False — если вертикальная.
        :param side: Сторона света для окон.
        """
        # Собираем все проемы (окна и двери) в один список и сортируем их по координате
        openings = [(c, WINDOW_WIDTH // 2, "window") for c in windows]
        openings += [(c, DOOR_WIDTH // 2, "door") for c in gaps]
        openings.sort(key=lambda item: item[0])

        cursor = start
        for center, half, kind in openings:
            gap_start = center - half
            gap_end = center + half
            # Строим сплошную стену до начала проема
            if gap_start > cursor:
                if horizontal:
                    self._wall(cursor, fixed, gap_start - cursor, WALL_THICKNESS)
                else:
                    self._wall(fixed, cursor, WALL_THICKNESS, gap_start - cursor)
            # Размещаем окно в проеме, если это окно
            if kind == "window":
                if horizontal:
                    self._window_h(center, fixed, side)
                else:
                    self._window_v(fixed, center, side)
            cursor = gap_end

        # Строим оставшийся кусок стены после последнего проема
        if cursor < end:
            if horizontal:
                self._wall(cursor, fixed, end - cursor, WALL_THICKNESS)
            else:
                self._wall(fixed, cursor, WALL_THICKNESS, end - cursor)

    def _horizontal_wall(
        self,
        x1: float,
        x2: float,
        y: float,
        windows: Tuple[float, ...] = (),
        gaps: Tuple[float, ...] = (),
        side: str = "top",
    ) -> None:
        """
        Строит горизонтальную стену.
        """
        self._wall_with_openings(x1, x2, y, windows, gaps, horizontal=True, side=side)

    def _vertical_wall(
        self,
        y1: float,
        y2: float,
        x: float,
        windows: Tuple[float, ...] = (),
        gaps: Tuple[float, ...] = (),
        side: str = "left",
    ) -> None:
        """
        Строит вертикальную стену.
        """
        self._wall_with_openings(y1, y2, x, windows, gaps, horizontal=False, side=side)

    def _build_layout(self) -> None:
        """
        Проектирует планировку дома выживших на карте: комнаты, внешние и внутренние стены,
        двери и окна. Также задаёт точку спавна игрока в центре дома.
        """
        t = WALL_THICKNESS
        ox, oy = 120, 100  # Смещение дома относительно краев карты
        build_w, build_h = 1640, 1000  # Размеры дома
        bx2 = ox + build_w
        by2 = oy + build_h
        split_x = ox + build_w // 2
        split_y = oy + build_h // 3

        inner_w = build_w - 2 * t
        inner_h = build_h - 2 * t

        # Размечаем зоны полов для комнат
        self._floor(ox + t, oy + t, inner_w, inner_h)
        self._floor(ox + t, oy + t, inner_w, split_y - oy - t)
        self._floor(ox + t, split_y, split_x - ox - t, by2 - split_y - t)
        self._floor(
            split_x + t, split_y, bx2 - split_x - 2 * t, by2 - split_y - t
        )

        # Строим внешние угловые колонны
        self._corner(ox, oy)
        self._corner(bx2 - t, oy)
        self._corner(ox, by2 - t)
        self._corner(bx2 - t, by2 - t)

        # Строим внешние стены с окнами
        self._horizontal_wall(
            ox + t, bx2 - t, oy, windows=[520, 1120], side="top"
        )
        self._horizontal_wall(
            ox + t, bx2 - t, by2 - t, windows=[820], side="bottom"
        )
        self._vertical_wall(
            oy + t, by2 - t, ox, windows=[300, 700], side="left"
        )
        self._vertical_wall(
            oy + t, by2 - t, bx2 - t, windows=[620], side="right"
        )

        # Строим внутренние перегородки и двери между комнатами
        self._corner(split_x - t, split_y - t)
        self._vertical_wall(split_y, by2 - t, split_x, gaps=[split_y + 220])
        self._horizontal_wall(ox + t, split_x, split_y, gaps=[ox + 320])
        self._horizontal_wall(
            split_x + t, bx2 - t, oy + 420, gaps=[split_x + 220]
        )

        # Игрок появляется в центре дома
        self.spawn_point = (ox + build_w // 2, oy + build_h // 2)

    def collision_rects(self, for_enemy: bool = False) -> List[pygame.Rect]:
        """
        Возвращает список всех прямоугольников коллизий на карте в данный момент.
        Включает стены и окна, если они заблокированы для прохода.

        :param for_enemy: True, если коллизии запрашиваются для ИИ зомби.
        """
        rects = list(self.walls)
        for window in self.windows:
            if window.blocks_movement(for_enemy=for_enemy):
                rects.append(window.rect)
        return rects

    @staticmethod
    def _closest_point_on_rect(
        x: float, y: float, rect: pygame.Rect
    ) -> Tuple[float, float]:
        """
        Находит ближайшую к точке (x, y) точку на прямоугольнике rect.
        """
        closest_x = max(rect.left, min(x, rect.right))
        closest_y = max(rect.top, min(y, rect.bottom))
        return closest_x, closest_y

    @classmethod
    def _circle_hits_rect(
        cls, x: float, y: float, radius: float, rect: pygame.Rect
    ) -> bool:
        """
        Проверяет, пересекает ли круг прямоугольник.
        """
        closest_x, closest_y = cls._closest_point_on_rect(x, y, rect)
        dx = x - closest_x
        dy = y - closest_y
        return dx * dx + dy * dy < radius * radius

    def _push_out(
        self, x: float, y: float, radius: float, rect: pygame.Rect
    ) -> Tuple[float, float]:
        """
        Выталкивает круглую сущность из прямоугольника коллизии, если они пересекаются.
        Реализует плавное скольжение вдоль стен.

        :param x, y: Текущие координаты круга.
        :param radius: Радиус круга.
        :param rect: Прямоугольник препятствия.
        :return: Скорректированные координаты (x, y).
        """
        closest_x, closest_y = self._closest_point_on_rect(x, y, rect)
        dx = x - closest_x
        dy = y - closest_y
        dist = math.hypot(dx, dy)
        if dist >= radius:
            return x, y
        if dist == 0:
            # Предотвращаем деление на ноль, если центр круга ровно на границе
            return x + radius, y
        # Вычисляем величину выталкивания
        push = (radius - dist) / dist
        return x + dx * push, y + dy * push

    def resolve_circle_move(
        self,
        x: float,
        y: float,
        radius: float,
        dx: float,
        dy: float,
        for_enemy: bool = False,
    ) -> Tuple[float, float]:
        """
        Перемещает круглую сущность на смещение (dx, dy) с разрешением коллизий
        обособленно по осям X и Y (чтобы скользить вдоль стен).

        :param x, y: Исходные координаты.
        :param radius: Радиус сущности.
        :param dx, dy: Желаемое смещение.
        :param for_enemy: Флаг ИИ врага (влияет на проходимость окон).
        :return: Новые безопасные координаты (x, y).
        """
        rects = self.collision_rects(for_enemy=for_enemy)

        # Движение по оси X и выталкивание из коллизий
        x += dx
        for rect in rects:
            x, y = self._push_out(x, y, radius, rect)

        # Движение по оси Y и выталкивание из коллизий
        y += dy
        for rect in rects:
            x, y = self._push_out(x, y, radius, rect)

        return x, y

    def circle_hits_wall(self, x: float, y: float, radius: float) -> bool:
        """
        Проверяет, касается ли круг стен или окон (используется для уничтожения пуль).
        """
        rects = self.walls + [window.rect for window in self.windows]
        return any(self._circle_hits_rect(x, y, radius, rect) for rect in rects)

    def get_spawn_points_outside(self, offset: float) -> List[Tuple[float, float]]:
        """
        Возвращает список точек для спавна зомби снаружи дома напротив каждого окна.
        """
        return [window.spawn_outside(offset) for window in self.windows]

    def get_window_near(
        self, x: float, y: float, max_dist: float = BOARD_INTERACT_DISTANCE
    ) -> Optional[Window]:
        """
        Находит ближайшее окно к точке (x, y) в пределах дистанции взаимодействия,
        которое ещё не заколочено до конца.

        :param x, y: Координаты игрока.
        :param max_dist: Максимальный радиус взаимодействия.
        :return: Объект Window или None.
        """
        best = None
        best_dist = max_dist
        for window in self.windows:
            if window.is_fully_boarded:
                continue
            dist = window.distance_to(x, y)
            if dist < best_dist:
                best_dist = dist
                best = window
        return best

    def try_board_window(self, x: float, y: float) -> bool:
        """
        Пытается заколотить ближайшее окно доской.

        :param x, y: Координаты игрока.
        :return: True, если доска успешно поставлена, иначе False.
        """
        window = self.get_window_near(x, y)
        return window.add_board() if window else False

    def process_zombie_board_attacks(
        self, enemies: List["Enemy"], dt: float
    ) -> int:
        """
        Обрабатывает атаки зомби на заколоченные окна. Если зомби стоит близко к заколоченному окну,
        он бьёт по доскам, нанося им урон.

        :param enemies: Список всех врагов.
        :param dt: Шаг времени (в секундах).
        :return: Количество успешных ударов по доскам за этот кадр (для воспроизведения звуков).
        """
        # Уменьшаем кулдаун атак на всех окнах
        for window in self.windows:
            window._attack_cooldown = tick_down(window._attack_cooldown, dt)

        hit_count = 0
        attack_range = ENEMY_RADIUS + ZOMBIE_BOARD_ATTACK_RANGE

        # Проверяем каждого живого врага
        for enemy in enemies:
            if not enemy.is_alive:
                continue
            for window in self.windows:
                # Зомби бьёт по окну, только если оно заколочено и кулдаун атаки прошёл
                if not window.has_boards or window._attack_cooldown > 0:
                    continue
                if window.distance_to(enemy.x, enemy.y) > attack_range:
                    continue

                # Наносим урон доске
                window.damage_board(1)
                window._attack_cooldown = ZOMBIE_BOARD_ATTACK_COOLDOWN
                hit_count += 1
                break  # Один зомби может ударить только одно окно за кадр

        return hit_count

    def draw(self, screen: pygame.Surface, camera: "Camera") -> None:
        """
        Отрисовывает карту: полы, стены и окна.

        :param screen: Экран отрисовки.
        :param camera: Объект камеры.
        """
        # Отрисовываем полы комнат
        for floor_rect in self.floor_rects:
            draw_textured_rect(screen, self.floor_texture, floor_rect, camera)
        # Отрисовываем сплошные стены
        for wall in self.walls:
            draw_textured_rect(screen, self.wall_texture, wall, camera)
        # Отрисовываем окна и баррикады
        for window in self.windows:
            window.draw(
                screen,
                camera,
                self.window_texture,
                self.vertical_window_texture,
                self.board_texture,
                self.vertical_board_texture,
            )

"""
Модуль врагов (зомби).
Описывает класс Enemy, наследуемый от CircleEntity.
Управляет искусственным интеллектом зомби: поиском кратчайшего пути к игроку
с помощью алгоритма A*, перемещением с обходом препятствий, получением урона
с визуальной вспышкой и отрисовкой полоски здоровья.
"""

import math

import pygame

from entity import CircleEntity, draw_rotated_sprite, load_sprite
from settings import (
    ENEMY_HIT_FLASH_TIME,
    ENEMY_HIT_TINT,
    ENEMY_HP,
    ENEMY_HP_BAR_BG,
    ENEMY_HP_BAR_FILL,
    ENEMY_HP_BAR_HEIGHT,
    ENEMY_HP_BAR_OFFSET,
    ENEMY_HP_BAR_WIDTH,
    ENEMY_RADIUS,
    ENEMY_REPATH_TIME,
    ENEMY_SPEED,
    ENEMY_SPRITE,
    ENEMY_SPRITE_SIZE,
    ENEMY_WAYPOINT_REACH,
)
from utils import distance, normalize_move, tick_down, to_screen


class Enemy(CircleEntity):
    """
    Класс врага (зомби), преследующего игрока.
    """

    # Статический член класса для кэширования спрайта зомби
    _sprite = None

    def __init__(self, x: float, y: float) -> None:
        """
        Инициализирует врага в заданных мировых координатах.

        :param x, y: Начальные координаты спавна врага.
        """
        super().__init__(x, y, ENEMY_RADIUS, ENEMY_HP)
        self.path = []  # Список ячеек сетки, составляющих путь до игрока
        self.path_index = 0  # Индекс текущей путевой точки в списке пути
        self.repath_timer = 0.0  # Таймер до следующего перерасчёта пути
        self.hit_flash = 0.0  # Таймер эффекта вспышки при получении урона
        self.angle = 0.0  # Направление движения врага в радианах

        # Загружаем спрайт зомби один раз
        if Enemy._sprite is None:
            Enemy._sprite = load_sprite(ENEMY_SPRITE, ENEMY_SPRITE_SIZE)

    def take_damage(self, amount: int) -> None:
        """
        Наносит урон врагу и запускает таймер вспышки получения урона.

        :param amount: Количество наносимого урона.
        """
        was_alive = self.alive
        super().take_damage(amount)
        if was_alive:
            self.hit_flash = ENEMY_HIT_FLASH_TIME

    def _move_toward(self, target_x: float, target_y: float, game_map: "GameMap") -> None:
        """
        Перемещает врага по направлению к целевой точке с проверкой коллизий.

        :param target_x, target_y: Мировые координаты целевой точки.
        :param game_map: Объект игровой карты для разрешения коллизий.
        """
        move_x, move_y = normalize_move(
            target_x - self.x, target_y - self.y, ENEMY_SPEED
        )
        if move_x == 0 and move_y == 0:
            return
        # Поворачиваем зомби в сторону движения
        self.angle = math.atan2(move_y, move_x)
        # Перемещаем врага с коллизиями для врагов учитываются закрытые досками окна
        self.x, self.y = game_map.resolve_circle_move(
            self.x,
            self.y,
            self.radius,
            move_x,
            move_y,
            for_enemy=True,
        )

    def update(
        self,
        player: "Player",
        game_map: "GameMap",
        dt: float,
        navgrid: "NavGrid",
        pathfinder: "AStarPathfinder",
    ) -> None:
        """
        Обновляет состояние врага: уменьшает таймеры, периодически пересчитывает
        путь до игрока, движется по найденным путевым точкам.

        :param player: Объект игрока (цель преследования).
        :param game_map: Объект игровой карты.
        :param dt: Время, прошедшее с предыдущего кадра (в секундах).
        :param navgrid: Сетка навигации для поиска путей.
        :param pathfinder: Поисковик путей на базе алгоритма A*.
        """
        self.hit_flash = tick_down(self.hit_flash, dt)
        if not self.alive:
            return

        # Периодически пересчитываем путь до игрока
        self.repath_timer -= dt
        if self.repath_timer <= 0 or self.path_index >= len(self.path):
            start = navgrid.world_to_cell(self.x, self.y)
            goal = navgrid.world_to_cell(player.x, player.y)
            self.path = pathfinder.find_path(navgrid, start, goal)
            # Начинаем со следующей точки пути, если путь успешно найден
            self.path_index = 1 if len(self.path) > 1 else 0
            self.repath_timer = ENEMY_REPATH_TIME

        # Движение по путевым точкам
        if self.path and self.path_index < len(self.path):
            wx, wy = navgrid.cell_to_world(self.path[self.path_index])
            self._move_toward(wx, wy, game_map)
            # Если приблизились к текущей путевой точке, переключаемся на следующую
            if distance(self.x, self.y, wx, wy) < ENEMY_WAYPOINT_REACH:
                self.path_index += 1
        else:
            # Если путь не найден, движемся напрямую к игроку
            self._move_toward(player.x, player.y, game_map)

    def draw(self, screen: pygame.Surface, camera: "Camera") -> None:
        """
        Отрисовывает врага на экране. При получении урона накладывает красный оттенок.
        Также отрисовывает полоску здоровья над головой врага.

        :param screen: Экран отрисовки (pygame.Surface).
        :param camera: Объект камеры.
        """
        if not self.alive:
            return
        sprite = Enemy._sprite
        # Эффект вспышки при получении урона
        if self.hit_flash > 0:
            sprite = sprite.copy()
            sprite.fill(ENEMY_HIT_TINT, special_flags=pygame.BLEND_RGBA_ADD)
        draw_rotated_sprite(screen, sprite, self.x, self.y, camera, self.angle)
        self._draw_hp_bar(screen, camera)

    def _draw_hp_bar(self, screen: pygame.Surface, camera: "Camera") -> None:
        """
        Отрисовывает полоску здоровья над врагом, если его здоровье не полное.

        :param screen: Экран отрисовки (pygame.Surface).
        :param camera: Объект камеры.
        """
        if not self.alive or self.hp >= self.max_hp:
            return

        # Переводим мировые координаты врага в экранные
        screen_x, screen_y = to_screen(self.x, self.y, camera)
        x = screen_x - ENEMY_HP_BAR_WIDTH // 2
        y = screen_y - ENEMY_HP_BAR_OFFSET

        # Вычисляем ширину заполненной части полоски здоровья
        fill_width = int(ENEMY_HP_BAR_WIDTH * max(0, self.hp) / self.max_hp)

        # Отрисовываем задний фон полоски (красный/темный)
        pygame.draw.rect(
            screen,
            ENEMY_HP_BAR_BG,
            (x, y, ENEMY_HP_BAR_WIDTH, ENEMY_HP_BAR_HEIGHT),
        )
        # Отрисовываем заполненную часть полоски (ярко-красный)
        pygame.draw.rect(
            screen,
            ENEMY_HP_BAR_FILL,
            (x, y, fill_width, ENEMY_HP_BAR_HEIGHT),
        )

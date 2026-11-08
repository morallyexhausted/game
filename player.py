"""
Модуль игрока для игры.
Определяет класс Player, наследуемый от CircleEntity.
Управляет вводом пользователя (движение WASD, прицеливание мышью),
обработкой получения урона с кулдауном и отрисовкой персонажа.
"""

import math

import pygame

from entity import CircleEntity, draw_rotated_sprite, load_sprite
from settings import (
    DIAGONAL_SCALE,
    PLAYER_DAMAGE_COOLDOWN,
    PLAYER_DASH_COOLDOWN,
    PLAYER_DASH_DISTANCE,
    PLAYER_MAX_HP,
    PLAYER_RADIUS,
    PLAYER_SPRITE,
    PLAYER_SPRITE_SIZE,
    PLAYER_SPEED,
)
from utils import angle_to_screen_point, tick_down


class Player(CircleEntity):
    """
    Класс управляемого игроком персонажа.
    """

    # Статический член класса для кэширования спрайта игрока
    _sprite = None

    def __init__(self) -> None:
        """
        Инициализирует игрока в точке (0, 0) со стандартными характеристиками.
        """
        super().__init__(0, 0, PLAYER_RADIUS, PLAYER_MAX_HP)
        self.angle = 0.0  # Угол поворота (направление взгляда) в радианах
        self.is_moving = False  # Флаг, движется ли игрок в данный момент
        self._damage_cooldown = 0.0  # Таймер неуязвимости после получения урона
        self._dash_cooldown = 0.0  # Перезарядка рывка

        # Загружаем спрайт игрока один раз
        if Player._sprite is None:
            Player._sprite = load_sprite(PLAYER_SPRITE, PLAYER_SPRITE_SIZE)

    def take_damage(self, amount: int) -> None:
        """
        Наносит урон игроку, если он жив и не находится в состоянии временной неуязвимости.

        :param amount: Количество наносимого урона.
        """
        if not self.alive or self._damage_cooldown > 0:
            return
        self.hp -= amount
        # Активируем кулдаун получения урона (неуязвимость)
        self._damage_cooldown = PLAYER_DAMAGE_COOLDOWN
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    @property
    def dash_ready(self) -> bool:
        """Возвращает True, если рывок можно использовать."""
        return self.alive and self._dash_cooldown <= 0

    @property
    def dash_cooldown(self) -> float:
        """Оставшееся время до следующего рывка."""
        return self._dash_cooldown

    def dash(self, game_map: "GameMap") -> bool:
        """Делает короткий рывок по направлению движения или прицела.

        Рывок разбит на несколько шагов, поэтому не позволяет проскочить
        сквозь тонкую стену карты.
        """
        if not self.dash_ready:
            return False

        keys = pygame.key.get_pressed()
        direction_x = keys[pygame.K_d] - keys[pygame.K_a]
        direction_y = keys[pygame.K_s] - keys[pygame.K_w]
        if direction_x == 0 and direction_y == 0:
            direction_x = math.cos(self.angle)
            direction_y = math.sin(self.angle)

        direction_length = math.hypot(direction_x, direction_y)
        move_x = direction_x / direction_length * PLAYER_DASH_DISTANCE
        move_y = direction_y / direction_length * PLAYER_DASH_DISTANCE
        for _ in range(12):
            self.x, self.y = game_map.resolve_circle_move(
                self.x,
                self.y,
                self.radius,
                move_x / 12,
                move_y / 12,
                for_enemy=False,
            )

        self._dash_cooldown = PLAYER_DASH_COOLDOWN
        self.is_moving = True
        return True

    def update(self, camera: "Camera", dt: float, game_map: "GameMap") -> None:
        """
        Обновляет состояние игрока: уменьшает кулдаун урона, обрабатывает WASD-движение,
        разрешает коллизии с картой и вычисляет угол поворота к курсору мыши.

        :param camera: Объект камеры для вычисления угла взгляда.
        :param dt: Время, прошедшее с предыдущего кадра (в секундах).
        :param game_map: Объект игровой карты для перемещения с коллизиями.
        """
        # Обновляем таймер неуязвимости
        self._damage_cooldown = tick_down(self._damage_cooldown, dt)
        self._dash_cooldown = tick_down(self._dash_cooldown, dt)
        if not self.alive:
            self.is_moving = False
            return

        # Обработка клавиатурного ввода для движения
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * PLAYER_SPEED
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * PLAYER_SPEED

        # Корректируем скорость при движении по диагонали (чтобы не двигаться быстрее)
        if dx and dy:
            dx *= DIAGONAL_SCALE
            dy *= DIAGONAL_SCALE

        # Перемещаем игрока с проверкой столкновений со стенами и баррикадами
        old_x, old_y = self.x, self.y
        self.x, self.y = game_map.resolve_circle_move(
            self.x, self.y, self.radius, dx, dy, for_enemy=False
        )
        # Проверяем, сдвинулся ли игрок (для воспроизведения звуков шагов)
        self.is_moving = self.x != old_x or self.y != old_y

        # Поворачиваем игрока в сторону курсора мыши
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.angle = angle_to_screen_point(
            self.x, self.y, mouse_x, mouse_y, camera
        )

    def draw(self, screen: pygame.Surface, camera: "Camera") -> None:
        """
        Отрисовывает игрока, повернутого в сторону прицеливания.

        :param screen: Экран отрисовки (pygame.Surface).
        :param camera: Объект камеры.
        """
        if not self.alive:
            return
        draw_rotated_sprite(
            screen, Player._sprite, self.x, self.y, camera, self.angle
        )

"""
Описывает поведение снаряда, выпущенного игроком: его пошаговое движение,
проверку столкновений с врагами и стенами, а также отрисовку на экране.
"""

import math
from typing import List

import pygame

from entity import draw_rotated_sprite, load_sprite
from settings import (
    BULLET_DAMAGE,
    BULLET_MAX_DISTANCE,
    BULLET_MOVE_STEPS,
    BULLET_RADIUS,
    BULLET_SPRITE,
    BULLET_SPRITE_SIZE,
    BULLET_SPEED,
)
from utils import distance


class Bullet:
    """
    Класс пули, летящей в заданном направлении.
    """

    # Статический член класса для хранения загруженного спрайта кэширование
    _sprite = None

    def __init__(self, x: float, y: float, angle: float) -> None:
        """
        Инициализирует пулю в начальной точке с заданным углом полёта.

        :param x, y: Начальные мировые координаты пули (координаты игрока).
        :param angle: Угол направления полёта в радианах.
        """
        self.x = float(x)
        self.y = float(y)
        self.start_x = self.x
        self.start_y = self.y
        self.angle = angle

        # Вычисляем составляющие вектора скорости пули
        self.vx = math.cos(angle) * BULLET_SPEED
        self.vy = math.sin(angle) * BULLET_SPEED
        self.alive = True

        # Загружаем спрайт пули один раз для всех экземпляров класса
        if Bullet._sprite is None:
            Bullet._sprite = load_sprite(BULLET_SPRITE, BULLET_SPRITE_SIZE)

    def update(self, game_map: "GameMap", enemies: List["Enemy"]) -> None:
        """
        Обновляет положение пули, проверяя столкновения с врагами и стенами.
        Для предотвращения «пролёта» сквозь тонкие стены на высокой скорости
        движение за один кадр разбивается на несколько мелких шагов (BULLET_MOVE_STEPS).

        :param game_map: Объект игровой карты для проверки коллизий со стенами.
        :param enemies: Список врагов для проверки попаданий.
        """
        if not self.alive:
            return

        # Пошаговое движение пули за текущий кадр
        for _ in range(BULLET_MOVE_STEPS):
            next_x = self.x + self.vx / BULLET_MOVE_STEPS
            next_y = self.y + self.vy / BULLET_MOVE_STEPS

            # Проверяем попадание во врагов на этом шаге
            for enemy in enemies:
                if enemy.is_alive and enemy.hits_circle(next_x, next_y, BULLET_RADIUS):
                    enemy.take_damage(BULLET_DAMAGE)
                    self.alive = False
                    return

            # Проверяем попадание в стену на этом шаге
            if game_map.circle_hits_wall(next_x, next_y, BULLET_RADIUS):
                self.alive = False
                return

            # Сдвигаем пулю в новую точку
            self.x = next_x
            self.y = next_y

        # Проверяем, не улетела ли пуля дальше максимальной дистанции
        dist = distance(self.start_x, self.start_y, self.x, self.y)
        if dist >= BULLET_MAX_DISTANCE:
            self.alive = False

    def draw(self, screen: pygame.Surface, camera: "Camera") -> None:
        """
        Отрисовывает пулю на экране с учётом её угла полёта и смещения камеры.

        :param screen: Экран отрисовки (pygame.Surface).
        :param camera: Объект камеры.
        """
        if not self.alive:
            return
        draw_rotated_sprite(
            screen, Bullet._sprite, self.x, self.y, camera, self.angle
        )

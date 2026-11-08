"""
Модуль базовых игровых сущностей и функций отрисовки спрайтов.
Содержит базовый класс CircleEntity для всех круглых физических объектов (игрок, зомби),
а также вспомогательные функции для масштабирования и вращения спрайтов.
"""

import math
from typing import Union, Tuple

import pygame

from assets import load_image
from utils import circles_overlap, to_screen


def load_sprite(filename: str, size: Union[int, Tuple[int, int]]) -> pygame.Surface:
    """
    Загружает спрайт из файлов активов и масштабирует его до нужного размера.

    :param filename: Имя файла изображения.
    :param size: Размер в пикселях. Может быть целым числом (для квадратных спрайтов)
                 или кортежем (ширина, высота).
    :return: Масштабированный pygame.Surface.
    """
    sprite = load_image(filename)
    if isinstance(size, int):
        size = (size, size)
    return pygame.transform.smoothscale(sprite, size)


def draw_rotated_sprite(
    screen: pygame.Surface,
    sprite: pygame.Surface,
    x: float,
    y: float,
    camera: "Camera",
    angle: float,
) -> None:
    """
    Отрисовывает спрайт, повернутый на заданный угол, центрируя его по мировым координатам.

    :param screen: Экран отрисовки (pygame.Surface).
    :param sprite: Исходный спрайт (pygame.Surface).
    :param x, y: Мировые координаты центра объекта.
    :param camera: Объект камеры.
    :param angle: Угол поворота в радианах.
    """
    # Поворачиваем спрайт переводя радианы в градусы и меняя направление вращения под Pygame
    rotated = pygame.transform.rotate(sprite, -math.degrees(angle))
    # Получаем прямоугольник повернутого спрайта и центрируем его на экранных координатах объекта
    rect = rotated.get_rect(center=to_screen(x, y, camera))
    screen.blit(rotated, rect)


class CircleEntity:
    """
    Базовый класс для всех круглых игровых сущностей (игрока, врагов).
    Управляет координатами, здоровьем, состоянием жизни и коллизиями.
    """

    def __init__(self, x: float, y: float, radius: float, hp: int) -> None:
        """
        Инициализирует круглую сущность.

        :param x, y: Начальные мировые координаты центра.
        :param radius: Физический радиус коллизии.
        :param hp: Максимальное и текущее здоровье.
        """
        self.x = float(x)
        self.y = float(y)
        self.radius = radius
        self.max_hp = hp
        self.hp = hp
        self.alive = True

    @property
    def is_alive(self) -> bool:
        """
        Возвращает True, если сущность жива.
        """
        return self.alive

    def take_damage(self, amount: int) -> None:
        """
        Наносит урон сущности, уменьшая здоровье. Если здоровье падает до 0, сущность погибает.

        :param amount: Количество наносимого урона.
        """
        if not self.alive:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def hits_circle(self, x: float, y: float, radius: float) -> bool:
        """
        Проверяет коллизию данной сущности с другим кругом.

        :param x, y: Координаты центра другого круга.
        :param radius: Радиус другого круга.
        :return: True при наличии коллизии, иначе False.
        """
        return circles_overlap(self.x, self.y, self.radius, x, y, radius)

    def draw_circle(
        self, screen: pygame.Surface, camera: "Camera", color: Tuple[int, int, int]
    ) -> None:
        """
        Отрисовывает отладочный круг на месте сущности.

        :param screen: Экран отрисовки (pygame.Surface).
        :param camera: Объект камеры.
        :param color: Цвет круга (RGB).
        """
        if not self.alive:
            return
        pygame.draw.circle(
            screen, color, to_screen(self.x, self.y, camera), self.radius
        )

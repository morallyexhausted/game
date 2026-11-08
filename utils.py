"""
Вспомогательные математические и геометрические утилиты для игры.
Содержит функции для расчёта расстояний, углов, коллизий и трансформации координат.
"""

import math
from typing import Tuple


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Вычисляет евклидово расстояние между двумя точками (x1, y1) и (x2, y2).
    """
    return math.hypot(x2 - x1, y2 - y1)


def circles_overlap(
    x1: float, y1: float, r1: float, x2: float, y2: float, r2: float
) -> bool:
    """
    Проверяет, пересекаются ли два круга.

    :param x1, y1, r1: Координаты центра и радиус первого круга.
    :param x2, y2, r2: Координаты центра и радиус второго круга.
    :return: True, если круги пересекаются или соприкасаются, иначе False.
    """
    return distance(x1, y1, x2, y2) <= r1 + r2


def to_screen(x: float, y: float, camera: "Camera") -> Tuple[int, int]:
    """
    Преобразует глобальные мировые координаты в экранные координаты с учётом камеры.

    :param x, y: Мировые координаты объекта.
    :param camera: Объект камеры.
    :return: Кортеж (screen_x, screen_y) в формате целых чисел.
    """
    return int(x - camera.x), int(y - camera.y)


def angle_to_screen_point(
    x: float, y: float, screen_x: int, screen_y: int, camera: "Camera"
) -> float:
    """
    Вычисляет угол (в радианах) от объекта в мировых координатах до точки на экране.
    Используется для направления взгляда игрока на курсор мыши.

    :param x, y: Мировые координаты объекта (например, игрока).
    :param screen_x, screen_y: Экранные координаты целевой точки (например, мыши).
    :param camera: Объект камеры.
    :return: Угол в радианах от -pi до pi.
    """
    return math.atan2(screen_y + camera.y - y, screen_x + camera.x - x)


def normalize_move(
    dx: float, dy: float, speed: float
) -> Tuple[float, float]:
    """
    Нормализует вектор движения и масштабирует его под заданную скорость.
    Гарантирует, что объект не будет двигаться быстрее своей максимальной скорости,
    даже если целевая точка находится дальше.

    :param dx, dy: Смещение по осям X и Y.
    :param speed: Максимальная скорость движения.
    :return: Кортеж (move_x, move_y) — нормализованное смещение.
    """
    dist = math.hypot(dx, dy)
    if dist == 0:
        return 0.0, 0.0
    step = min(speed, dist)
    return dx / dist * step, dy / dist * step


def tick_down(timer: float, dt: float) -> float:
    """
    Уменьшает таймер на прошедшее время dt, не позволяя ему стать меньше 0.0.

    :param timer: Текущее значение таймера.
    :param dt: Время, прошедшее с предыдущего кадра.
    :return: Новое значение таймера.
    """
    return max(0.0, timer - dt) if timer > 0 else 0.0


def clamp(value: float, low: float, high: float) -> float:
    """
    Ограничивает числовое значение в пределах [low, high].
    """
    return max(low, min(value, high))

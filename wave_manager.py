"""
Модуль управления волнами врагов для игры.
Описывает класс WaveManager, который отвечает за генерацию врагов (зомби)
в начале каждой волны, выбор безопасных точек спавна за пределами видимости игрока,
обновление состояния всех врагов и проверку условий завершения волны.
"""

import math
import random

from typing import List, Tuple

from enemy import Enemy
from settings import (
    SPAWN_DISTANCE,
    SPAWN_MIN_GAP,
    SPAWN_RETRY_COUNT,
    WAVE_BASE_COUNT,
    WAVE_COUNT_PER_LEVEL,
)
from utils import distance


class WaveManager:
    """
    Класс менеджера волн, координирующий спавн и жизненный цикл врагов.
    """

    def __init__(self, game_map: "GameMap") -> None:
        """
        Инициализирует менеджер волн.

        :param game_map: Объект игровой карты.
        """
        self.game_map = game_map
        self.wave = 0  # Номер текущей волны
        self.enemies = []  # Список живых врагов в текущей волне

    def start_next_wave(self, player_x: float, player_y: float) -> None:
        """
        Запускает следующую волну врагов, увеличивая их количество.

        :param player_x, player_y: Текущие координаты игрока (для предотвращения спавна прямо на игроке).
        """
        self.wave += 1
        # Рассчитываем количество врагов для текущей волны
        count = WAVE_BASE_COUNT + (self.wave - 1) * WAVE_COUNT_PER_LEVEL
        self.enemies = []

        # Спавним каждого врага в безопасном месте
        for _ in range(count):
            x, y = self._spawn_position(player_x, player_y, self.enemies)
            self.enemies.append(Enemy(x, y))

    def _spawn_position(
        self, player_x: float, player_y: float, existing_enemies: List["Enemy"]
    ) -> Tuple[float, float]:
        """
        Находит подходящую точку спавна для нового врага.
        Точка выбирается за пределами окон на безопасном расстоянии от игрока.

        :param player_x, player_y: Координаты игрока.
        :param existing_enemies: Список уже заспавненных врагов в этой волне.
        :return: Кортеж (x, y) мировых координат для спавна.
        """
        # Получаем список точек за окнами, которые находятся достаточно далеко от игрока
        points = self.game_map.get_spawn_points_outside(SPAWN_DISTANCE)
        if not points:
            # Резервный вариант, если точки не найдены
            points = [(player_x + SPAWN_DISTANCE, player_y)]

        # Перемешиваем точки для случайного выбора
        random.shuffle(points)
        min_distance = SPAWN_MIN_GAP

        # Пытаемся найти свободную точку среди стандартных мест спавна
        for point in points:
            if self._is_spawn_free(point, existing_enemies, min_distance):
                return point

        # Если все стандартные точки заняты, генерируем случайную точку со смещением
        base_x, base_y = random.choice(points)
        for _ in range(SPAWN_RETRY_COUNT):
            angle = random.uniform(0, math.tau)
            offset = random.uniform(min_distance, min_distance * 3)
            point = (
                base_x + math.cos(angle) * offset,
                base_y + math.sin(angle) * offset,
            )
            if self._is_spawn_free(point, existing_enemies, min_distance):
                return point

        return base_x, base_y

    @staticmethod
    def _is_spawn_free(
        point: Tuple[float, float], enemies: List["Enemy"], min_distance: float
    ) -> bool:
        """
        Проверяет, свободна ли точка от других врагов.

        :param point: Проверяемая точка (x, y).
        :param enemies: Список существующих врагов.
        :param min_distance: Минимально допустимое расстояние до другого врага.
        :return: True, если точка свободна, иначе False.
        """
        x, y = point
        return all(
            distance(x, y, enemy.x, enemy.y) >= min_distance
            for enemy in enemies
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
        Обновляет состояние всех активных врагов.

        :param player: Объект игрока.
        :param game_map: Объект игровой карты.
        :param dt: Шаг времени (в секундах).
        :param navgrid: Сетка навигации.
        :param pathfinder: Поисковик путей A*.
        """
        for enemy in self.enemies:
            enemy.update(player, game_map, dt, navgrid, pathfinder)

    def remove_dead(self) -> None:
        """
        Удаляет погибших врагов из списка активных.
        """
        self.enemies = [enemy for enemy in self.enemies if enemy.is_alive]

    def wave_cleared(self) -> bool:
        """
        Проверяет, зачищена ли текущая волна (все враги мертвы).

        :return: True, если в волне были враги и все они погибли.
        """
        return self.enemies and all(not enemy.is_alive for enemy in self.enemies)

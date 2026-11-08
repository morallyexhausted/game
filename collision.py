"""
Модуль обработки столкновений (коллизий).
Содержит функции для проверки урона игроку со стороны зомби и очистки списков от уничтоженных объектов.
"""

from typing import List, Any

from settings import ENEMY_DAMAGE, PLAYER_RADIUS

def check_enemy_player_collisions(enemies: List["Enemy"], player: "Player") -> None:
    """
    Проверяет столкновение каждого живого врага с игроком.
    Если враг касается игрока, игрок получает урон.

    :param enemies: Список всех врагов на уровне.
    :param player: Объект игрока.
    """
    if not player.alive:
        return
    for enemy in enemies:
        # Если враг жив и соприкасается с физическим телом игрока
        if enemy.is_alive and enemy.hits_circle(
            player.x, player.y, PLAYER_RADIUS
        ):
            player.take_damage(ENEMY_DAMAGE)


def cleanup_alive(items: List[Any]) -> None:
    """
    Удаляет «мертвые» объекты из переданного списка на месте (in-place).
    Используется для очистки уничтоженных пуль и врагов.

    :param items: Изменяемый список объектов (каждый должен иметь свойство alive).
    """
    items[:] = [item for item in items if item.alive]

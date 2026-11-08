"""
Модуль управления звуком для игры.
Описывает класс SoundManager, который инициализирует аудиомикшер Pygame,
загружает звуковые эффекты (выстрелы, шаги, удары по доскам, рычание зомби)
и управляет их воспроизведением и остановкой на аудиоканалах.
"""

import pygame

from assets import load_sound
from settings import (
    BOARD_HIT_SOUND,
    BOARD_HIT_SOUND_VOLUME,
    BULLET_SHOT_SOUND,
    BULLET_SHOT_SOUND_VOLUME,
    PLAYER_STEP_SOUND,
    PLAYER_STEP_SOUND_VOLUME,
    ZOMBIE_AMBIENT_SOUND,
    ZOMBIE_AMBIENT_SOUND_VOLUME,
)


class SoundManager:
    """
    Класс менеджера звуков, отвечающий за аудиоэффекты и фоновые шумы в игре.
    """

    def __init__(self) -> None:
        """
        Инициализирует микшер Pygame и предварительно загружает все звуковые ресурсы.
        """
        pygame.mixer.init()

        # Звук выстрела игрока
        self.shot_sound = load_sound(
            BULLET_SHOT_SOUND, BULLET_SHOT_SOUND_VOLUME
        )

        # Звук удара зомби по деревянной доске баррикады
        self.board_hit_sound = load_sound(
            BOARD_HIT_SOUND, BOARD_HIT_SOUND_VOLUME
        )

        # Звук шагов игрока и канал для его зацикленного воспроизведения
        self.step_sound = load_sound(PLAYER_STEP_SOUND, PLAYER_STEP_SOUND_VOLUME)
        self.step_channel = None

        # Звук фонового рычания зомби и канал для его зацикленного воспроизведения
        self.zombie_ambient_sound = load_sound(
            ZOMBIE_AMBIENT_SOUND, ZOMBIE_AMBIENT_SOUND_VOLUME
        )
        self.zombie_ambient_channel = None

    def play_shot(self) -> None:
        """
        Воспроизводит одиночный звук выстрела.
        """
        self.shot_sound.play()

    def play_board_hit(self) -> None:
        """
        Воспроизводит одиночный звук удара по деревянной баррикаде.
        """
        self.board_hit_sound.play()

    def start_steps(self) -> None:
        """
        Запускает зацикленное воспроизведение звука шагов игрока,
        если оно ещё не запущено на канале.
        """
        if self.step_channel is not None and self.step_channel.get_busy():
            return
        # loops=-1 запускает бесконечный цикл воспроизведения звука
        self.step_channel = self.step_sound.play(loops=-1)

    def stop_steps(self) -> None:
        """
        Останавливает воспроизведение звука шагов игрока.
        """
        if self.step_channel is not None:
            self.step_channel.stop()
            self.step_channel = None

    def start_zombie_ambient(self) -> None:
        """
        Запускает зацикленное фоновое рычание зомби,
        если оно ещё не запущено.
        """
        if (
            self.zombie_ambient_channel is not None
            and self.zombie_ambient_channel.get_busy()
        ):
            return
        self.zombie_ambient_channel = self.zombie_ambient_sound.play(loops=-1)

    def stop_zombie_ambient(self) -> None:
        """
        Останавливает воспроизведение фонового рычания зомби.
        """
        if self.zombie_ambient_channel is not None:
            self.zombie_ambient_channel.stop()
            self.zombie_ambient_channel = None

    def stop_all(self) -> None:
        """
        Останавливает все зацикленные звуки (шаги, фоновый звук зомби).
        Используется при выходе в меню или завершении игры.
        """
        self.stop_steps()
        self.stop_zombie_ambient()

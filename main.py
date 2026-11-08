"""
Главный модуль запуска игры.
Содержит игровой цикл, инициализацию Pygame, обработку событий клавиатуры и мыши,
обновление игровых состояний (меню, игра, пауза, конец игры) и отрисовку
всех визуальных элементов, включая HUD и эффект динамической темноты вокруг игрока.
"""

import pygame
from typing import List, Tuple, Optional

from bullet import Bullet
from camera import Camera
from collision import check_enemy_player_collisions, cleanup_alive
from map import GameMap
from navigation import AStarPathfinder, NavGrid
from player import Player
from settings import (
    BOARD_HITS,
    COLOR_BG,
    COLOR_UI,
    FPS,
    GAME_TITLE,
    HEIGHT,
    HUD_FONT_SIZE,
    HUD_HINT_Y,
    HUD_HP_Y,
    HUD_DASH_Y,
    HUD_SCORE_Y,
    HUD_WAVE_Y,
    HUD_X,
    MAP_HEIGHT,
    MAP_WIDTH,
    MENU_DISABLED_COLOR,
    MENU_FIRST_ITEM_Y,
    MENU_FONT_SIZE,
    MENU_HINT_Y_OFFSET,
    MENU_ITEM_GAP,
    MENU_OVERLAY_ALPHA,
    MENU_SMALL_FONT_SIZE,
    MENU_SUBTITLE_Y,
    MENU_TITLE_FONT_SIZE,
    MENU_TITLE_Y,
    PLAYER_VISIBILITY_FADE,
    PLAYER_VISIBILITY_FADE_STEPS,
    PLAYER_VISIBILITY_RADIUS,
    COLOR_UI_ACCENT,
    WIDTH,
)
from sound_manager import SoundManager
from utils import angle_to_screen_point
from wave_manager import WaveManager


# Константы состояний игры
STATE_MENU = "menu"          # Главное меню
STATE_PLAYING = "playing"    # Игровой процесс
STATE_PAUSED = "paused"      # Пауза
STATE_GAME_OVER = "game_over"  # Экран поражения


class Game:
    """
    Основной класс игры, управляющий инициализацией, игровым циклом,
    состояниями и взаимодействием всех систем.
    """

    def __init__(self) -> None:
        """
        Инициализирует Pygame, создает игровое окно, шрифты и менеджеры.
        """
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()

        # Загрузка шрифтов для различных элементов интерфейса
        self.font = pygame.font.SysFont(None, HUD_FONT_SIZE)
        self.title_font = pygame.font.SysFont(None, MENU_TITLE_FONT_SIZE)
        self.menu_font = pygame.font.SysFont(None, MENU_FONT_SIZE)
        self.small_font = pygame.font.SysFont(None, MENU_SMALL_FONT_SIZE)

        self.running = True  # Флаг работы приложения
        self.state = STATE_MENU  # Начальное состояние игры
        self.menu_index = 0  # Текущий выбранный пункт меню

        # Игровые объекты (инициализируются при старте новой игры)
        self.game_map = None
        self.navgrid = None
        self.pathfinder = None
        self.player = None
        self.camera = None
        self.wave_manager = None
        self.sound_manager = SoundManager()
        self.bullets = []  # Список активных пуль на экране
        self.score = 0
        self.kills = 0

    def _start_new_game(self) -> None:
        """
        Инициализирует новую игровую сессию: создает карту, сетку навигации,
        игрока, камеру и запускает первую волну зомби.
        """
        self.game_map = GameMap()
        self.navgrid = NavGrid(MAP_WIDTH, MAP_HEIGHT)
        self.pathfinder = AStarPathfinder()

        # Строим сетку путей на основе геометрии карты
        self.navgrid.rebuild_from_map(self.game_map)

        self.player = Player()
        # Спавним игрока в безопасной точке по центру карты
        self.player.x, self.player.y = self.game_map.spawn_point
        self.camera = Camera()
        self.wave_manager = WaveManager(self.game_map)
        self.bullets = []
        self.score = 0
        self.kills = 0

        # Запускаем первую волну зомби
        self.wave_manager.start_next_wave(self.player.x, self.player.y)
        self.state = STATE_PLAYING
        self.menu_index = 0

        # Включаем фоновые звуки зомби
        self.sound_manager.start_zombie_ambient()

    def _stop_gameplay_sounds(self) -> None:
        """
        Останавливает все зацикленные игровые звуки (шаги, эмбиент зомби).
        """
        self.sound_manager.stop_steps()
        self.sound_manager.stop_zombie_ambient()

    def _game_over(self) -> None:
        """
        Переводит игру в состояние конца игры (поражения).
        """
        self.state = STATE_GAME_OVER
        self.menu_index = 0
        self._stop_gameplay_sounds()

    @property
    def _can_continue(self) -> bool:
        """
        Проверяет, можно ли продолжить текущую игру (игрок создан и жив).
        """
        return self.player is not None and self.player.alive

    def _menu_items(self) -> List[Tuple[str, str, bool]]:
        """
        Возвращает список пунктов меню для текущего состояния игры.
        Каждая запись в списке: (Название, Идентификатор действия, Доступность пункта).
        """
        if self.state == STATE_PAUSED:
            return [
                ("Продолжить", "continue", True),
                ("Новая игра", "new_game", True),
                ("В главное меню", "main_menu", True),
                ("Выход", "quit", True),
            ]

        if self.state == STATE_GAME_OVER:
            return [
                ("Новая игра", "new_game", True),
                ("В главное меню", "main_menu", True),
                ("Выход", "quit", True),
            ]

        return [
            ("Новая игра", "new_game", True),
            ("Продолжить", "continue", self._can_continue),
            ("Выход", "quit", True),
        ]

    def _move_menu_selection(self, step: int) -> None:
        """
        Перемещает выделение пункта меню вверх или вниз, пропуская недоступные пункты.

        :param step: Шаг смещения (например, -1 для движения вверх, 1 — вниз).
        """
        items = self._menu_items()
        if not items:
            return

        for _ in items:
            self.menu_index = (self.menu_index + step) % len(items)
            # Если пункт меню доступен для выбора, останавливаемся на нём
            if items[self.menu_index][2]:
                return

    def _activate_menu_item(self) -> None:
        """
        Выполняет действие, соответствующее выбранному пункту меню.
        """
        items = self._menu_items()
        if not items:
            return

        _, action, enabled = items[self.menu_index]
        if not enabled:
            return

        if action == "new_game":
            self._start_new_game()
        elif action == "continue":
            self.state = STATE_PLAYING
            self.menu_index = 0
            self.sound_manager.start_zombie_ambient()
        elif action == "main_menu":
            self.state = STATE_MENU
            self.menu_index = 0
            self._stop_gameplay_sounds()
        elif action == "quit":
            self.running = False
            self.sound_manager.stop_all()

    def _handle_menu_event(self, event: pygame.event.Event) -> None:
        """
        Обрабатывает нажатия клавиш при нахождении в меню.

        :param event: Событие pygame.event.Event.
        """
        if event.type != pygame.KEYDOWN:
            return

        if event.key in (pygame.K_w, pygame.K_UP):
            self._move_menu_selection(-1)
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            self._move_menu_selection(1)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self._activate_menu_item()
        elif event.key == pygame.K_ESCAPE:
            if self.state == STATE_PAUSED and self._can_continue:
                self.state = STATE_PLAYING
                self.sound_manager.start_zombie_ambient()
            elif self.state == STATE_MENU:
                self.running = False

    def _handle_events(self) -> None:
        """
        Главный диспетчер событий Pygame. Распределяет события между меню и игровым процессом.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            # Если мы не в игре, события обрабатывает меню
            if self.state != STATE_PLAYING:
                self._handle_menu_event(event)
                continue

            # Поставить игру на паузу по кнопке Esc
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state = STATE_PAUSED
                self.menu_index = 0
                self._stop_gameplay_sounds()
                continue

            # Space — короткий рывок для выхода из окружения
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self._dash()
                continue

            if not self.player.alive:
                continue

            # ЛКМ — выстрел пулей
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._shoot()

            # Клавиша E — заколотить ближайшее окно доской
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                self.game_map.try_board_window(self.player.x, self.player.y)

    def _dash(self) -> None:
        """Пытается выполнить рывок и оставляет управление откликающимся."""
        if not self.player.dash(self.game_map):
            return
        self.camera.update(self.player, self.game_map)

    def _shoot(self) -> None:
        """
        Создает новую пулю, летящую из позиции игрока в направлении курсора мыши,
        и воспроизводит звук выстрела.
        """
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # Вычисляем точный угол полета пули с учетом смещения камеры
        angle = angle_to_screen_point(
            self.player.x, self.player.y, mouse_x, mouse_y, self.camera
        )
        self.bullets.append(Bullet(self.player.x, self.player.y, angle))
        self.sound_manager.play_shot()

    def _update(self, dt: float) -> None:
        """
        Обновляет физику, логику и положения всех игровых объектов.

        :param dt: Шаг времени (в секундах).
        """
        if self.state != STATE_PLAYING:
            return
        if not self.player.alive:
            self._game_over()
            return

        # Обновление игрока и звуков шагов
        self.player.update(self.camera, dt, self.game_map)
        if self.player.is_moving:
            self.sound_manager.start_steps()
        else:
            self.sound_manager.stop_steps()

        # Обновление камеры (следование за игроком)
        self.camera.update(self.player, self.game_map)

        # Обновление волны врагов (ИИ, поиск путей)
        self.wave_manager.update(
            self.player, self.game_map, dt, self.navgrid, self.pathfinder
        )

        # Обработка ударов зомби по баррикадам окон
        board_hit_count = self.game_map.process_zombie_board_attacks(
            self.wave_manager.enemies, dt
        )
        for _ in range(board_hit_count):
            self.sound_manager.play_board_hit()

        # Обновление летящих пуль и подсчёт поверженных зомби
        alive_before = sum(enemy.is_alive for enemy in self.wave_manager.enemies)
        for bullet in self.bullets:
            bullet.update(self.game_map, self.wave_manager.enemies)
        alive_after = sum(enemy.is_alive for enemy in self.wave_manager.enemies)
        defeated = alive_before - alive_after
        if defeated > 0:
            self.kills += defeated
            self.score += defeated * 10

        # Проверка коллизий зомби с игроком (нанесение урона)
        check_enemy_player_collisions(self.wave_manager.enemies, self.player)

        # Удаление уничтоженных пуль
        cleanup_alive(self.bullets)

        if not self.player.alive:
            self._game_over()
            return

        # Если все зомби мертвы, запускаем следующую волну, иначе чистим трупы
        if self.wave_manager.wave_cleared():
            self.score += self.wave_manager.wave * 25
            self.wave_manager.start_next_wave(self.player.x, self.player.y)
        else:
            self.wave_manager.remove_dead()

    def _draw_hud(self, hint: str = "") -> None:
        """
        Отрисовывает интерфейс игрока (HUD): здоровье, текущую волну и подсказки.

        :param hint: Текст подсказки (например, о возможности заколотить окно).
        """
        # Отрисовка HP игрока
        self.screen.blit(
            self.font.render(f"HP: {self.player.hp}", True, COLOR_UI),
            (HUD_X, HUD_HP_Y),
        )
        # Отрисовка номера волны
        self.screen.blit(
            self.font.render(f"Wave: {self.wave_manager.wave}", True, COLOR_UI),
            (HUD_X, HUD_WAVE_Y),
        )
        self.screen.blit(
            self.font.render(
                f"Score: {self.score}   Kills: {self.kills}", True, COLOR_UI_ACCENT
            ),
            (HUD_X, HUD_SCORE_Y),
        )
        dash_text = (
            "Space: DASH READY"
            if self.player.dash_ready
            else f"Space: dash in {self.player.dash_cooldown:.1f}s"
        )
        self.screen.blit(
            self.font.render(dash_text, True, COLOR_UI_ACCENT),
            (HUD_X, HUD_DASH_Y),
        )
        # Отрисовка подсказки взаимодействия
        if hint:
            self.screen.blit(
                self.font.render(hint, True, COLOR_UI),
                (HUD_X, HUD_HINT_Y),
            )

    def _draw_darkness(self) -> None:
        """
        Отрисовывает эффект динамической темноты вокруг игрока.
        Создает эффект фонарика/ограниченной видимости с мягким размытием по краям.
        """
        darkness = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        # Заполняем экран сплошной черной маской
        darkness.fill((0, 0, 0, 255))

        # Переводим координаты игрока в экранные
        player_pos = (
            int(self.player.x - self.camera.x),
            int(self.player.y - self.camera.y),
        )

        # Рисуем концентрические круги с разной прозрачностью для эффекта мягкого размытия (fade)
        for i in range(PLAYER_VISIBILITY_FADE_STEPS, 0, -1):
            radius = (
                PLAYER_VISIBILITY_RADIUS
                + PLAYER_VISIBILITY_FADE * i // PLAYER_VISIBILITY_FADE_STEPS
            )
            alpha = 255 * i // PLAYER_VISIBILITY_FADE_STEPS
            pygame.draw.circle(darkness, (0, 0, 0, alpha), player_pos, radius)

        # Вырезаем полностью прозрачный круг в центре, где игрок видит всё четко
        pygame.draw.circle(darkness, (0, 0, 0, 0), player_pos, PLAYER_VISIBILITY_RADIUS)

        # Накладываем маску темноты на экран
        self.screen.blit(darkness, (0, 0))

    def _draw_game(self) -> None:
        """
        Отрисовывает все игровые объекты в мире.
        """
        # Заливаем фон
        self.screen.fill(COLOR_BG)
        # Отрисовываем карту (пол, стены, окна)
        self.game_map.draw(self.screen, self.camera)

        # Отрисовываем зомби
        for enemy in self.wave_manager.enemies:
            enemy.draw(self.screen, self.camera)
        # Отрисовываем игрока
        if self.player.alive:
            self.player.draw(self.screen, self.camera)
        # Отрисовываем летящие пули
        for bullet in self.bullets:
            bullet.draw(self.screen, self.camera)

        # Накладываем эффект темноты поверх игрового мира
        if self.player.alive:
            self._draw_darkness()

        # Формируем и выводим подсказку, если игрок стоит рядом с окном
        hint = ""
        window_near = self.game_map.get_window_near(
            self.player.x, self.player.y
        )
        if self.player.alive and window_near:
            hint = f"E — поставить доску ({BOARD_HITS} удара на доску)"
        self._draw_hud(hint)

    def _draw_centered_text(
        self,
        text: str,
        font: pygame.font.Font,
        y: int,
        color: Tuple[int, int, int] = COLOR_UI,
    ) -> None:
        """
        Вспомогательный метод для отрисовки текста, выровненного по центру экрана по оси X.

        :param text: Текст для вывода.
        :param font: Шрифт Pygame.
        :param y: Координата Y для размещения текста.
        :param color: Цвет текста (RGB).
        """
        surface = font.render(text, True, color)
        self.screen.blit(surface, surface.get_rect(center=(WIDTH // 2, y)))

    def _draw_menu(self, title: str, subtitle: str = "") -> None:
        """
        Отрисовывает интерфейс меню поверх игрового экрана (с полупрозрачным затемнением).

        :param title: Главный заголовок меню.
        :param subtitle: Подзаголовок меню.
        """
        # Создаем полупрозрачную маску затемнения игрового фона
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, MENU_OVERLAY_ALPHA))
        self.screen.blit(overlay, (0, 0))

        # Отрисовываем заголовки
        self._draw_centered_text(title, self.title_font, MENU_TITLE_Y)
        if subtitle:
            self._draw_centered_text(subtitle, self.small_font, MENU_SUBTITLE_Y)

        # Отрисовываем пункты меню с выделением текущего стрелочками
        items = self._menu_items()
        y = MENU_FIRST_ITEM_Y
        for index, (label, _, enabled) in enumerate(items):
            prefix = "> " if index == self.menu_index else "  "
            prefix_end = " <" if index == self.menu_index else "  "
            color = COLOR_UI if enabled else MENU_DISABLED_COLOR
            self._draw_centered_text(
                f"{prefix}{label}{prefix_end}", self.menu_font, y, color
            )
            y += MENU_ITEM_GAP

        # Отрисовываем подсказку по управлению внизу экрана
        self._draw_centered_text(
            "W/S или стрелки - выбор, Enter - подтвердить, Esc - назад",
            self.small_font,
            HEIGHT - MENU_HINT_Y_OFFSET,
        )

    def _draw(self) -> None:
        """
        Главный метод отрисовки кадра. Выбирает, что рисовать в зависимости от состояния.
        """
        if self.game_map is not None:
            self._draw_game()
        else:
            self.screen.fill(COLOR_BG)

        # Рисуем оверлей меню поверх игры, если игра остановлена или завершена
        if self.state == STATE_MENU:
            self._draw_menu(GAME_TITLE, "Выживи против волн зомби и набери максимум очков")
        elif self.state == STATE_PAUSED:
            self._draw_menu("Пауза", "Игра остановлена")
        elif self.state == STATE_GAME_OVER:
            self._draw_menu("Game Over", "Зомби добрались до тебя")

        # Переключаем буфер экрана для отображения кадра
        pygame.display.flip()

    def run(self) -> None:
        """
        Главный игровой цикл. Контролирует FPS, вызывает обновление логики и отрисовку.
        """
        while self.running:
            # Рассчитываем время dt, прошедшее между кадрами (в секундах)
            dt = self.clock.tick(FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()

        # Останавливаем все звуки перед выходом
        self.sound_manager.stop_all()
        pygame.quit()


if __name__ == "__main__":
    # Точка входа в программу
    Game().run()

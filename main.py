#!/usr/bin/env python3
import os
import sys
import time
import random
import pickle
import json
import re
from datetime import datetime

for stream in (sys.stdout, sys.stdin):
    try:
        stream.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass

sys.path.append('story')

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""
    class Style:
        BRIGHT = DIM = RESET_ALL = ""


def load_chapters():
    """Собирает главы из story/chapterN.py в порядке номеров."""
    result = []
    try:
        files = [f for f in os.listdir('story') if re.match(r'chapter\d+\.py$', f)]
    except OSError:
        return result

    nums = sorted(int(re.match(r'chapter(\d+)\.py$', f).group(1)) for f in files)
    for i in nums:
        try:
            module = __import__(f'chapter{i}')
            chapter = getattr(module, f'CHAPTER_{i}', None)
            if chapter:
                result.append(chapter)
        except Exception as e:
            print(f"Не удалось загрузить главу {i}: {e}")
    return result


chapters = load_chapters()

SKILL_NAMES = {
    "hacking": "взлом",
    "stealth": "скрытность",
    "programming": "код",
    "social": "люди",
    "investigation": "разведка",
}

FACTION_NAMES = {
    "hackers": "сцена",
    "corporations": "корпорации",
    "anarchists": "радикалы",
    "government": "государство",
    "underground": "рынок",
}


class GameData:
    def __init__(self):
        self.data_dir = os.path.expanduser("~/.terminal_shadows")
        self.save_dir = os.path.join(self.data_dir, "saves")
        self.config_file = os.path.join(self.data_dir, "config.json")
        self.ensure_directories()
        self.load_config()

    def ensure_directories(self):
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.save_dir, exist_ok=True)

    def load_config(self):
        defaults = {
            "difficulty": "normal",
            "autosave": True,
            "animations": True,
        }
        self.config = dict(defaults)
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                self.config.update({k: v for k, v in saved.items() if k in defaults})
            except (json.JSONDecodeError, OSError):
                pass
        else:
            self.save_config()

    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def _save_path(self, slot, game_mode):
        if slot == 0:
            return os.path.join(self.save_dir, f"autosave_{game_mode}.dat")
        return os.path.join(self.save_dir, f"save{slot}_{game_mode}.dat")

    def save_game(self, player_data, slot=0, game_mode="story"):
        payload = {
            'player': player_data,
            'timestamp': datetime.now().isoformat(),
            'version': GAME_VERSION,
            'game_mode': game_mode,
        }
        try:
            with open(self._save_path(slot, game_mode), 'wb') as f:
                pickle.dump(payload, f)
            return True
        except OSError as e:
            print(f"Не удалось сохранить: {e}")
            return False

    def load_game(self, slot=0, game_mode="story"):
        path = self._save_path(slot, game_mode)
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'rb') as f:
                return pickle.load(f)
        except (OSError, pickle.UnpicklingError) as e:
            print(f"Не удалось загрузить: {e}")
            return None

    def get_saves(self, game_mode="story"):
        saves = []
        if os.path.exists(self._save_path(0, game_mode)):
            saves.append(0)
        for i in range(1, 4):
            if os.path.exists(self._save_path(i, game_mode)):
                saves.append(i)
        return saves


class Player:
    def __init__(self, name):
        self.name = name
        self.level = 1
        self.exp = 0
        self.bitcoins = 1000
        self.skills = {
            "hacking": 1,
            "stealth": 1,
            "programming": 1,
            "social": 1,
            "investigation": 1,
        }
        self.inventory = []
        self.story_progress = 1
        self.reputation = 0
        self.achievements = []
        self.factions = {k: 0 for k in FACTION_NAMES}
        self.daily_missions_completed = 0
        self.boss_defeats = 0
        self.crafted_items = []
        self.personal_stats = {
            "play_time": 0,
            "chapters_completed": 0,
            "total_bitcoins_earned": 0,
            "hacks_completed": 0,
            "items_collected": 0,
            "achievements_unlocked": 0,
            "bosses_defeated": 0,
            "events_completed": 0,
            "items_crafted": 0,
            "start_date": datetime.now().isoformat(),
            "last_play_date": datetime.now().isoformat(),
        }

    def exp_to_next(self):
        return self.level * 1000

    def add_exp(self, amount):
        """Возвращает старый уровень, если случился level up, иначе None."""
        self.exp += amount
        if self.exp >= self.exp_to_next():
            old_level = self.level
            self.level_up()
            return old_level
        return None

    def level_up(self):
        self.level += 1
        self.exp = 0
        for skill in self.skills:
            self.skills[skill] += 1
        return f"Уровень {self.level}. Навыки подросли."

    def add_skill(self, skill, amount=1):
        if skill in self.skills:
            self.skills[skill] += amount
            return f"{SKILL_NAMES[skill]}: {self.skills[skill]}"
        return ""

    def add_bitcoins(self, amount):
        self.bitcoins += amount
        if amount > 0:
            self.personal_stats["total_bitcoins_earned"] += amount
        sign = "+" if amount >= 0 else ""
        return f"{sign}{amount} на кошельке"

    def add_achievement(self, name):
        if name not in self.achievements:
            self.achievements.append(name)
            self.personal_stats["achievements_unlocked"] += 1
            return f"Отметка: {name}"
        return ""

    def add_item(self):
        self.personal_stats["items_collected"] += 1

    def add_hack(self):
        self.personal_stats["hacks_completed"] += 1

    def update_play_time(self, seconds):
        self.personal_stats["play_time"] += seconds
        self.personal_stats["last_play_date"] = datetime.now().isoformat()

    def change_faction_rep(self, faction, amount):
        if faction in self.factions:
            self.factions[faction] += amount
            sign = "+" if amount >= 0 else ""
            return f"{FACTION_NAMES[faction]}: {sign}{amount}"
        return ""

    def get_faction_rank(self, faction):
        rep = self.factions.get(faction, 0)
        if rep < -300:
            return "враг"
        if rep < -80:
            return "не рады"
        if rep < 80:
            return "никто"
        if rep < 300:
            return "свой"
        if rep < 700:
            return "уважают"
        return "легенда сцены"


GAME_VERSION = "5.0"


class GameEngine:
    def __init__(self):
        self.data = GameData()
        self.player = None
        self.current_scene = "start"
        self.game_mode = "story"
        self.start_time = time.time()

    # ---------- вывод ----------

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def rule(self, char="─", width=58):
        print(Fore.CYAN + char * width + Style.RESET_ALL)

    def header(self, title):
        self.rule()
        print(Fore.WHITE + Style.BRIGHT + "  " + title + Style.RESET_ALL)
        self.rule()

    def print_ascii(self, art_name):
        path = os.path.join("data", "ascii_arts", f"{art_name}.txt")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                print(Fore.GREEN + f.read() + Style.RESET_ALL)

    def type_text(self, text, delay=0.02):
        if self.data.config.get("animations", True):
            for char in text:
                print(char, end='', flush=True)
                time.sleep(delay)
            print()
        else:
            print(text)

    def pause(self, prompt="\n[Enter]"):
        input(Fore.CYAN + prompt + Style.RESET_ALL)

    # ---------- Гид (ИИ) ----------

    GUIDE_AMBIENT = [
        "Я здесь. Слушаю линию.",
        "модель: costya-7b // память неполная",
        "Ты дышишь чаще обычного. Не мешает.",
        "[гид] контекст загружен. Продолжай.",
        "У страха низкий пинг. Это нормально.",
        "Я помню больше, чем говорю. Но не всё.",
        "гид// увер. 0.58. Иду за тобой вслепую, но иду.",
    ]

    def guide(self, text=None):
        """Печатает реплику Гида в намеренно 'синтетичном', меняющемся регистре."""
        if text is None:
            text = random.choice(self.GUIDE_AMBIENT)
            print(Fore.MAGENTA + text + Style.RESET_ALL)
            return
        forms = [
            lambda t: f"ГИД: {t}",
            lambda t: f"[гид] {t}",
            lambda t: f"гид// {t}",
        ]
        line = random.choice(forms)(text)
        if random.random() < 0.25:
            line += f"  [увер. {random.choice(['0.4', '0.6', '0.7', '0.9'])}]"
        print(Fore.MAGENTA + line + Style.RESET_ALL)

    def show_guide(self):
        self.print_ascii("guide")

    def hacking_animation(self, target):
        if not self.data.config.get("animations", True):
            print(f"Взлом: {target} ...")
            return
        print(f"\n{target}")
        for pct in range(0, 101, 10):
            filled = pct // 10
            bar = "█" * filled + "░" * (10 - filled)
            print(Fore.GREEN + f"  [{bar}] {pct}%" + Style.RESET_ALL, end='\r')
            time.sleep(0.12)
        print()

    # ---------- меню ----------

    def show_main_menu(self):
        while True:
            self.clear_screen()
            self.print_ascii("main_menu")
            print()
            self.header("TERMINAL SHADOWS")
            print("  1  Сюжет")
            print("  2  Свободный режим")
            print("  3  Загрузить")
            print("  4  Настройки")
            print("  5  Об игре")
            print("  6  Обновления")
            print("  7  Выход")
            self.rule()

            choice = input("  > ").strip()
            if choice == "1":
                self.story_mode_menu()
            elif choice == "2":
                self.sandbox_mode_menu()
            elif choice == "3":
                self.load_game_menu()
            elif choice == "4":
                self.settings_menu()
            elif choice == "5":
                self.show_stats()
            elif choice == "6":
                self.check_for_updates()
            elif choice == "7":
                self.exit_game()

    def story_mode_menu(self):
        while True:
            self.clear_screen()
            self.header("Сюжет")
            print("  1  Новая игра")
            print("  2  Продолжить")
            print("  3  Назад")
            self.rule()
            choice = input("  > ").strip()
            if choice == "1":
                self.start_new_game("story")
            elif choice == "2":
                self.load_specific_game("story")
            elif choice == "3":
                return

    def sandbox_mode_menu(self):
        while True:
            self.clear_screen()
            self.header("Свободный режим")
            print("  1  Новая игра")
            print("  2  Продолжить")
            print("  3  Назад")
            self.rule()
            choice = input("  > ").strip()
            if choice == "1":
                self.start_new_game("sandbox")
            elif choice == "2":
                self.load_specific_game("sandbox")
            elif choice == "3":
                return

    def start_new_game(self, mode):
        self.clear_screen()
        self.header("Кто ты")
        name = input("\n  Имя (или ник): ").strip()
        if not name:
            name = "аноним"

        self.player = Player(name)
        self.game_mode = mode
        print(f"\n  Ладно, {self.player.name}.")
        time.sleep(1)

        if mode == "story":
            self.start_story_mode()
        else:
            self.start_sandbox_mode()

    def start_story_mode(self):
        self.clear_screen()
        self.type_text("\n  Дядя Костя умер три недели назад. Тебе оставили ключи от его")
        self.type_text("  квартиры, коробку хлама и старый ноутбук, который никто не смог")
        self.type_text("  открыть.")
        time.sleep(0.6)
        self.type_text("\n  Ты открыл.")
        time.sleep(0.8)
        self.show_guide()
        self.guide("Костя? ... поправка: ты не Костя. Кто ты?")
        time.sleep(0.4)
        self.pause("\n  [Enter, чтобы начать]")
        self.play_story_mode()

    def start_sandbox_mode(self):
        self.clear_screen()
        self.header("Свободный режим")
        self.type_text("\n  Без сюжета. Ты, город и работа, которую никто не заказывал.")
        self.player.bitcoins = 5000
        self.player.level = 5
        for skill in self.player.skills:
            self.player.skills[skill] = 3
        print("\n  Стартовый набор: 5000 на кошельке, базовые навыки.")
        self.pause()
        self.sandbox_loop()

    # ---------- сюжет ----------

    def play_story_mode(self):
        if not chapters:
            print("\n  Главы не найдены. Проверь папку story/.")
            self.pause()
            return

        while self.player.story_progress <= len(chapters):
            index = self.player.story_progress - 1
            self.play_chapter(chapters[index], self.player.story_progress)
            if self.current_scene == "game_end":
                self.game_complete()
                return
            self.player.story_progress += 1
            self.player.personal_stats["chapters_completed"] += 1
            if self.data.config.get("autosave", True):
                if self.data.save_game(self.player.__dict__, 0, "story"):
                    print(Fore.CYAN + "\n  (сохранено)" + Style.RESET_ALL)
                    time.sleep(0.6)

        self.game_complete()

    def play_chapter(self, chapter, chapter_num):
        self.current_scene = "start"
        terminal = {"chapter_end", "next_chapter", "game_end"}

        while self.current_scene not in terminal:
            scene = chapter["scenes"].get(self.current_scene)
            if scene is None:
                print(f"  (сцена '{self.current_scene}' не найдена)")
                self.current_scene = "chapter_end"
                break

            self.clear_screen()
            self.header(chapter["title"])
            if chapter.get("guide_appearance") and self.current_scene == "start":
                self.show_guide()

            print()
            self.type_text("  " + scene["text"].replace("\n", "\n  "))
            print()

            choices = scene.get("choices", [])
            if not choices:
                self.pause()
                self.current_scene = "chapter_end"
                break

            for i, choice in enumerate(choices, 1):
                print(f"  {i}  {choice['text']}")
            print()

            raw = input("  > ").strip()
            if not raw.isdigit():
                continue
            num = int(raw)
            if not (1 <= num <= len(choices)):
                continue

            selected = choices[num - 1]
            result = self.apply_effects(selected.get("effect", {}))
            if result:
                print("\n" + result)
                time.sleep(0.8)
            self.current_scene = selected["next"]

    def apply_effects(self, effects):
        lines = []
        if "bitcoins" in effects:
            lines.append("  " + self.player.add_bitcoins(effects["bitcoins"]))
        if "level" in effects:
            self.player.level = max(self.player.level, effects["level"])
            lines.append(f"  Уровень {self.player.level}.")
        if "skill" in effects:
            got = self.player.add_skill(effects["skill"], effects.get("value", 1))
            if got:
                lines.append("  " + got)
        if "exp" in effects:
            old = self.player.add_exp(effects["exp"])
            lines.append(f"  +{effects['exp']} опыта")
            if old:
                lines.append("  " + self.player.level_up())
        if "item" in effects:
            self.player.inventory.append(effects["item"])
            self.player.add_item()
            lines.append(f"  В сумке: {effects['item']}")
        if "reputation" in effects:
            self.player.reputation += effects["reputation"]
            sign = "+" if effects["reputation"] >= 0 else ""
            lines.append(f"  Репутация {sign}{effects['reputation']}")
        if effects.get("achievement"):
            got = self.player.add_achievement(effects["achievement"])
            if got:
                lines.append("  " + got)
        return "\n".join(lines)

    # ---------- взлом ----------

    HACK_LOOT = [
        "дамп паролей", "рабочий эксплойт", "конфиг файрвола",
        "перехваченный трафик", "ускоритель перебора",
    ]

    def hacking_menu(self):
        targets = [
            {"name": "камера в подъезде", "reward": 200, "difficulty": 1, "req_level": 1},
            {"name": "точка Wi-Fi в кофейне", "reward": 400, "difficulty": 2, "req_level": 2},
            {"name": "CRM автосалона", "reward": 800, "difficulty": 3, "req_level": 3},
            {"name": "панель управляющей компании", "reward": 1500, "difficulty": 4, "req_level": 4},
            {"name": "сервер службы доставки", "reward": 2500, "difficulty": 5, "req_level": 6},
            {"name": "база пропусков бизнес-центра", "reward": 4000, "difficulty": 7, "req_level": 8},
            {"name": "платёжный шлюз", "reward": 6500, "difficulty": 9, "req_level": 10},
            {"name": "узел оператора связи", "reward": 10000, "difficulty": 11, "req_level": 13},
            {"name": "дата-центр подрядчика", "reward": 14000, "difficulty": 13, "req_level": 16},
            {"name": "архив Halcyon", "reward": 20000, "difficulty": 16, "req_level": 20},
            {"name": "внутренняя почта Halcyon", "reward": 30000, "difficulty": 19, "req_level": 24},
            {"name": "узел системы ЯСЕНЬ", "reward": 45000, "difficulty": 22, "req_level": 28},
        ]

        while True:
            self.clear_screen()
            self.header("Цели")
            print(f"  Кошелёк: {self.player.bitcoins}\n")
            for i, t in enumerate(targets, 1):
                ok = self.player.level >= t["req_level"]
                mark = Fore.GREEN + "+" if ok else Fore.RED + "-"
                print(mark + Style.RESET_ALL + f" {i:>2}  {t['name']}")
                print(f"       {t['reward']} / уровень {t['req_level']}+")
            print(f"\n  {len(targets) + 1}  Назад")
            print()

            raw = input("  > ").strip()
            if not raw.isdigit():
                continue
            choice = int(raw)
            if choice == len(targets) + 1:
                return
            if not (1 <= choice <= len(targets)):
                continue

            target = targets[choice - 1]
            if self.player.level < target["req_level"]:
                print(f"\n  Рано. Нужен уровень {target['req_level']}.")
                self.pause()
                continue

            self.hacking_animation(target["name"])
            success_chance = min(0.95, (self.player.skills["hacking"] * 0.25) / target["difficulty"])

            if random.random() < success_chance:
                reward = target["reward"]
                if self.player.skills["hacking"] > target["difficulty"]:
                    bonus = reward // 3
                    reward += bonus
                    print(f"  Чисто. Бонус за запас: +{bonus}")
                self.player.bitcoins += reward
                self.player.personal_stats["total_bitcoins_earned"] += reward
                exp_gain = max(20, reward // 4)
                old = self.player.add_exp(exp_gain)
                self.player.add_hack()
                print(Fore.GREEN + "  Готово." + Style.RESET_ALL)
                print(f"  +{reward} / +{exp_gain} опыта")
                if old:
                    print("  " + self.player.level_up())
                if random.random() < 0.4:
                    loot = random.choice(self.HACK_LOOT)
                    self.player.inventory.append(loot)
                    self.player.add_item()
                    print(f"  Подобрал: {loot}")
                if reward >= 20000:
                    got = self.player.add_achievement("крупная цель")
                    if got:
                        print("  " + got)
            else:
                penalty = min(500, self.player.bitcoins // 4)
                self.player.bitcoins = max(0, self.player.bitcoins - penalty)
                print(Fore.RED + "  Тебя срезали на подходе." + Style.RESET_ALL)
                print(f"  -{penalty}")

            self.pause()

    def shop_menu(self):
        items = [
            {"name": "нормальный сканер портов", "price": 300, "skill": "hacking", "bonus": 1},
            {"name": "VPN с оплатой крипто", "price": 500, "skill": "stealth", "bonus": 1},
            {"name": "словарь для перебора", "price": 800, "skill": "hacking", "bonus": 1},
            {"name": "набор соц. инженерии", "price": 1000, "skill": "social", "bonus": 2},
            {"name": "отладчик и дизассемблер", "price": 1200, "skill": "programming", "bonus": 2},
            {"name": "трекер утечек", "price": 1500, "skill": "investigation", "bonus": 2},
            {"name": "приватный прокси-сервер", "price": 2500, "skill": "stealth", "bonus": 2},
            {"name": "доступ к закрытому форуму", "price": 3000, "skill": "programming", "bonus": 2},
            {"name": "аппаратный ключ-имплант", "price": 4000, "skill": "hacking", "bonus": 3},
            {"name": "база телефонных данных", "price": 6000, "skill": "investigation", "bonus": 3},
            {"name": "свой эксплойт-фреймворк", "price": 12000, "skill": "hacking", "bonus": 4},
            {"name": "инсайдер на зарплате", "price": 20000, "skill": "social", "bonus": 4},
        ]

        while True:
            self.clear_screen()
            self.header("Барахолка")
            print(f"  Кошелёк: {self.player.bitcoins}\n")
            for i, item in enumerate(items, 1):
                print(f"  {i:>2}  {item['name']} — {item['price']}")
                print(f"       {SKILL_NAMES[item['skill']]} +{item['bonus']}")
            print(f"\n  {len(items) + 1}  Назад")
            print()

            raw = input("  > ").strip()
            if not raw.isdigit():
                continue
            choice = int(raw)
            if choice == len(items) + 1:
                return
            if not (1 <= choice <= len(items)):
                continue

            item = items[choice - 1]
            if self.player.bitcoins < item["price"]:
                print("\n  Не хватает.")
                self.pause()
                continue

            self.player.bitcoins -= item["price"]
            self.player.skills[item["skill"]] += item["bonus"]
            self.player.inventory.append(item["name"])
            self.player.add_item()
            print(f"\n  Взял: {item['name']}")
            print(f"  {SKILL_NAMES[item['skill']]}: {self.player.skills[item['skill']]}")
            if item["price"] >= 4000:
                got = self.player.add_achievement("не жадный")
                if got:
                    print("  " + got)
            self.pause()

    # ---------- профиль ----------

    def profile_menu(self):
        self.clear_screen()
        self.header(f"{self.player.name}")
        print(f"  Уровень {self.player.level}   опыт {self.player.exp}/{self.player.exp_to_next()}")
        print(f"  Кошелёк {self.player.bitcoins}   репутация {self.player.reputation:+d}")
        if self.game_mode == "story":
            print(f"  Глава {self.player.story_progress}/{len(chapters)}")
        print()

        print("  Навыки")
        for skill, level in self.player.skills.items():
            bar = "█" * min(20, level)
            print(f"    {SKILL_NAMES[skill]:<11} {bar} {level}")
        print()

        print("  Связи")
        for faction in self.player.factions:
            rep = self.player.factions[faction]
            print(f"    {FACTION_NAMES[faction]:<11} {rep:+d}  {self.player.get_faction_rank(faction)}")
        print()

        print("  Сумка")
        if self.player.inventory:
            counts = {}
            for item in self.player.inventory:
                counts[item] = counts.get(item, 0) + 1
            for item, n in list(counts.items())[:10]:
                suffix = f" x{n}" if n > 1 else ""
                print(f"    {item}{suffix}")
            if len(counts) > 10:
                print(f"    ... ещё {len(counts) - 10}")
        else:
            print("    пусто")
        print()

        stats = self.player.personal_stats
        print("  Счётчики")
        print(f"    в игре, минут: {int(stats['play_time'] // 60)}")
        print(f"    глав пройдено: {stats['chapters_completed']}/{len(chapters)}")
        print(f"    заработано:    {stats['total_bitcoins_earned']}")
        print(f"    взломов:       {stats['hacks_completed']}")
        print(f"    отметок:       {stats['achievements_unlocked']}/{len(self.ACHIEVEMENTS)}")
        self.pause()

    # ---------- случайные события ----------

    def random_event(self):
        events = [
            {
                "title": "Стук в дверь",
                "text": "На лестнице — двое, не курьеры. Отдел К вышел на адрес.",
                "choices": [
                    {"text": "Уходить по крышам", "skill": "stealth",
                     "success_reward": {"bitcoins": 1500, "faction": ("government", -30)},
                     "fail_penalty": {"bitcoins": -3000}},
                    {"text": "Стереть диски и открыть", "skill": "hacking",
                     "success_reward": {"exp": 600},
                     "fail_penalty": {"bitcoins": -1500}},
                    {"text": "Сунуть конверт", "cost": 4000,
                     "reward": {"faction": ("government", 20), "exp": 200}},
                ],
            },
            {
                "title": "Предложение Halcyon",
                "text": "Письмо без обратного адреса. Контракт на 15000. Работа на них.",
                "choices": [
                    {"text": "Взять деньги", "reward": {"bitcoins": 15000,
                     "faction": ("corporations", 60), "faction2": ("hackers", -60)}},
                    {"text": "Отказать", "reward": {"faction": ("hackers", 40), "reputation": 40}},
                    {"text": "Взять и слить их же", "skill": "stealth",
                     "success_reward": {"bitcoins": 18000, "faction": ("hackers", 60)},
                     "fail_penalty": {"faction": ("corporations", -120)}},
                ],
            },
            {
                "title": "Сходка",
                "text": "Тебя зовут на закрытую встречу. Знакомые ники, незнакомые лица.",
                "choices": [
                    {"text": "Прийти и обменяться", "reward": {"skill": "hacking",
                     "value": 1, "faction": ("hackers", 40)}},
                    {"text": "Прийти и обчистить", "skill": "hacking",
                     "success_reward": {"bitcoins": 8000, "item": "список контактов"},
                     "fail_penalty": {"faction": ("hackers", -100)}},
                    {"text": "Не ходить", "reward": {}},
                ],
            },
            {
                "title": "Город лёг",
                "text": "По больницам и метро расползся шифровальщик. Не твоя работа.",
                "choices": [
                    {"text": "Помочь погасить", "skill": "programming",
                     "success_reward": {"bitcoins": 6000, "faction": ("government", 80), "reputation": 120},
                     "fail_penalty": {"reputation": -60}},
                    {"text": "Влезть в шум и снять сливки", "skill": "stealth",
                     "success_reward": {"bitcoins": 12000},
                     "fail_penalty": {"bitcoins": -4000}},
                    {"text": "Не лезть", "reward": {}},
                ],
            },
            {
                "title": "Закрытый рынок",
                "text": "Кто-то сбросил инвайт на площадку, которой вроде бы нет.",
                "choices": [
                    {"text": "Купить редкий тулкит", "cost": 5000,
                     "reward": {"item": "серый тулкит", "skill": "hacking", "value": 2}},
                    {"text": "Поставить на кон", "cost": 2000, "random": True},
                    {"text": "Закрыть вкладку", "reward": {}},
                ],
            },
            {
                "title": "Чужой ассистент",
                "text": "В логах — второй ИИ, не Гид. Он тоже к тебе присматривается.",
                "choices": [
                    {"text": "Поговорить с ним", "reward": {"exp": 500, "item": "обрывок чужой модели"}},
                    {"text": "Погасить процесс", "reward": {"bitcoins": 3000, "faction": ("corporations", 30)}},
                    {"text": "Скормить его Гиду", "skill": "programming",
                     "success_reward": {"skill": "programming", "value": 2},
                     "fail_penalty": {"exp": -300}},
                ],
            },
            {
                "title": "Перехват",
                "text": "В трафике всплыло чужое: адрес, время, чья-то беда, которую можно упредить.",
                "choices": [
                    {"text": "Слить куда надо анонимно", "reward": {"faction": ("government", 60), "reputation": 80}},
                    {"text": "Разрулить самому", "skill": "hacking",
                     "success_reward": {"bitcoins": 5000, "reputation": 120},
                     "fail_penalty": {"reputation": -100}},
                    {"text": "Пройти мимо", "reward": {"faction": ("government", -30), "reputation": -60}},
                ],
            },
            {
                "title": "Тень из прошлого",
                "text": "Всплыл почерк хакера, которого считали мёртвым. Кто-то работает под Костю.",
                "choices": [
                    {"text": "Раскрутить след", "skill": "investigation",
                     "success_reward": {"item": "старые заметки Кости", "skill": "hacking", "value": 2},
                     "fail_penalty": {"exp": -200}},
                    {"text": "Осторожно написать", "reward": {"faction": ("underground", 60), "exp": 500}},
                    {"text": "Продать наводку", "reward": {"bitcoins": 6000, "faction": ("hackers", -40)}},
                ],
            },
        ]

        event = random.choice(events)
        self.clear_screen()
        self.header(event["title"])
        print()
        self.type_text("  " + event["text"])
        print()
        for i, choice in enumerate(event["choices"], 1):
            cost = f"  (стоит {choice['cost']})" if "cost" in choice else ""
            skill = f"  [{SKILL_NAMES[choice['skill']]}]" if "skill" in choice else ""
            print(f"  {i}  {choice['text']}{cost}{skill}")
        print()

        raw = input("  > ").strip()
        if not raw.isdigit():
            return
        num = int(raw)
        if not (1 <= num <= len(event["choices"])):
            return

        selected = event["choices"][num - 1]
        if "cost" in selected:
            if self.player.bitcoins < selected["cost"]:
                print("\n  Не хватает.")
                self.pause()
                return
            self.player.bitcoins -= selected["cost"]

        if "skill" in selected:
            chance = min(0.9, self.player.skills[selected["skill"]] * 0.15)
            if random.random() < chance:
                print(Fore.GREEN + "\n  Вышло." + Style.RESET_ALL)
                self.apply_event_reward(selected.get("success_reward", {}))
            else:
                print(Fore.RED + "\n  Не вышло." + Style.RESET_ALL)
                self.apply_event_reward(selected.get("fail_penalty", {}))
        elif "random" in selected:
            if random.random() < 0.5:
                win = selected["cost"] * random.randint(2, 4)
                self.player.bitcoins += win
                print(f"\n  Повезло. +{win}")
            else:
                print(f"\n  Пусто. -{selected['cost']}")
        else:
            self.apply_event_reward(selected.get("reward", {}))

        self.player.personal_stats["events_completed"] += 1
        if self.player.personal_stats["events_completed"] >= 30:
            got = self.player.add_achievement("всё время во что-то влипаешь")
            if got:
                print("  " + got)
        self.pause()

    def apply_event_reward(self, reward):
        if "bitcoins" in reward:
            amount = reward["bitcoins"]
            self.player.bitcoins = max(0, self.player.bitcoins + amount)
            if amount > 0:
                self.player.personal_stats["total_bitcoins_earned"] += amount
            print(f"  {amount:+d} на кошельке")
        if "exp" in reward:
            if reward["exp"] >= 0:
                old = self.player.add_exp(reward["exp"])
                print(f"  +{reward['exp']} опыта")
                if old:
                    print("  " + self.player.level_up())
            else:
                self.player.exp = max(0, self.player.exp + reward["exp"])
                print(f"  {reward['exp']} опыта")
        if "skill" in reward and "value" in reward:
            print("  " + self.player.add_skill(reward["skill"], reward["value"]))
        if "item" in reward:
            self.player.inventory.append(reward["item"])
            self.player.add_item()
            print(f"  В сумке: {reward['item']}")
        if "reputation" in reward:
            print(f"  Репутация {reward['reputation']:+d}")
            self.player.reputation += reward["reputation"]
        if "faction" in reward:
            print("  " + self.player.change_faction_rep(*reward["faction"]))
        if "faction2" in reward:
            print("  " + self.player.change_faction_rep(*reward["faction2"]))

    # ---------- достижения ----------

    ACHIEVEMENTS = [
        # сюжет
        "первый взлом", "чистая работа", "прочитал всё Костино", "своя команда",
        "Первый заход в Halcyon", "Слой под слоем", "Хвост с лицом",
        "Форма стакана", "Цена входа", "Слишком близко", "Должник Аркадия",
        "Рычаг вместо правды", "Канал в обе стороны", "Под мостом",
        "Чистый и пустой", "Ровное дыхание", "Одно живое имя",
        "знаешь правду о Косте", "не продался", "Модель по имени я",
        "один против системы", "мишень, а не легенда", "Шум на всю страну",
        "дошёл до ядра", "обнародовал ЯСЕНЬ", "стёр Гида", "продался",
        "сохранил Гида", "ушёл в тень", "прошёл сюжет",
        # свободный режим
        "крупная цель", "не жадный", "разобрал ICE", "собрал свой тулкит",
        "всё время во что-то влипаешь",
    ]

    def achievements_menu(self):
        self.clear_screen()
        self.header("Отметки")
        print()
        for name in self.ACHIEVEMENTS:
            mark = Fore.GREEN + "[x]" if name in self.player.achievements else Fore.RED + "[ ]"
            print(mark + Style.RESET_ALL + f" {name}")
        print()
        self.pause()

    # ---------- системы защиты (ICE) ----------

    def boss_battles(self):
        systems = [
            {"name": "домашний файрвол", "hp": 80, "damage": 8, "reward": 1500, "level": 3, "drop": ("stealth", 1)},
            {"name": "IDS оператора связи", "hp": 150, "damage": 12, "reward": 4000, "level": 6, "drop": ("hacking", 2)},
            {"name": "SOC подрядчика", "hp": 250, "damage": 18, "reward": 8000, "level": 10, "drop": ("programming", 2)},
            {"name": "служба безопасности Halcyon", "hp": 400, "damage": 25, "reward": 15000, "level": 15, "drop": ("social", 3)},
            {"name": "активная защита ЯСЕНЬ", "hp": 600, "damage": 32, "reward": 25000, "level": 20, "drop": ("investigation", 3)},
            {"name": "группа реагирования", "hp": 850, "damage": 40, "reward": 35000, "level": 25, "drop": ("hacking", 4)},
            {"name": "внутренний контур Halcyon", "hp": 1100, "damage": 50, "reward": 50000, "level": 30, "drop": ("programming", 5)},
            {"name": "ядро ЯСЕНЬ", "hp": 1500, "damage": 65, "reward": 70000, "level": 35, "drop": ("hacking", 6)},
        ]

        while True:
            self.clear_screen()
            self.header("Защита")
            print(f"  Уровень {self.player.level}   кошелёк {self.player.bitcoins}\n")
            for i, s in enumerate(systems, 1):
                ok = self.player.level >= s["level"]
                mark = Fore.GREEN + "+" if ok else Fore.RED + "-"
                print(mark + Style.RESET_ALL + f" {i}  {s['name']}  [ур. {s['level']}+]")
                print(f"      прочность {s['hp']} / отпор {s['damage']} / {s['reward']}")
            print(f"\n  {len(systems) + 1}  Назад")
            print()

            raw = input("  > ").strip()
            if not raw.isdigit():
                continue
            choice = int(raw)
            if choice == len(systems) + 1:
                return
            if not (1 <= choice <= len(systems)):
                continue

            system = systems[choice - 1]
            if self.player.level < system["level"]:
                print(f"\n  Рано. Нужен уровень {system['level']}.")
                self.pause()
                continue
            self.fight_boss(system)

    def fight_boss(self, system):
        self.clear_screen()
        self.header(system["name"])

        player_hp = 100 + self.player.level * 10
        boss_hp = system["hp"]
        turn = 1
        overload_ready = True

        while player_hp > 0 and boss_hp > 0:
            print(f"\n  ход {turn}   ты {player_hp}   защита {boss_hp}")
            print("  1  давить нагрузкой")
            print("  2  прикрыться")
            print("  3  перегрузка" + ("" if overload_ready else " (перезарядка)"))
            print("  4  отступить")

            action = input("  > ").strip()
            defended = False

            if action == "1":
                dmg = random.randint(10, 20) + self.player.skills["hacking"] * 3
                boss_hp -= dmg
                print(f"  -{dmg}")
            elif action == "2":
                defended = True
                print("  держишь оборону")
            elif action == "3" and overload_ready:
                dmg = random.randint(30, 50) + self.player.skills["programming"] * 5
                boss_hp -= dmg
                overload_ready = False
                print(f"  перегрузка: -{dmg}")
            elif action == "4":
                print("\n  Отошёл. Живой — уже неплохо.")
                self.pause()
                return
            else:
                print("  ...")
                continue

            if boss_hp > 0:
                incoming = system["damage"] + random.randint(-5, 5)
                if defended:
                    incoming //= 2
                player_hp -= incoming
                print(f"  тебя задело: -{incoming}")

            time.sleep(0.6)
            turn += 1
            if turn > 40:
                print("\n  Затянулось. Ты сорвался с линии.")
                self.pause()
                return

        if player_hp <= 0:
            penalty = min(20000, self.player.bitcoins // 4)
            self.player.bitcoins = max(0, self.player.bitcoins - penalty)
            print(Fore.RED + "\n  Тебя выбросило. Аппаратуру жалко." + Style.RESET_ALL)
            print(f"  -{penalty}")
        else:
            self.player.bitcoins += system["reward"]
            self.player.personal_stats["total_bitcoins_earned"] += system["reward"]
            skill, value = system["drop"]
            self.player.skills[skill] += value
            exp = system["level"] * 200
            old = self.player.add_exp(exp)
            print(Fore.GREEN + f"\n  Пробил: {system['name']}." + Style.RESET_ALL)
            print(f"  +{system['reward']} / {SKILL_NAMES[skill]} +{value} / +{exp} опыта")
            if old:
                print("  " + self.player.level_up())
            self.player.boss_defeats += 1
            self.player.personal_stats["bosses_defeated"] += 1
            if self.player.boss_defeats >= 3:
                got = self.player.add_achievement("разобрал ICE")
                if got:
                    print("  " + got)
        self.pause()

    # ---------- крафт ----------

    def crafting_menu(self):
        recipes = [
            {"name": "боевой эксплойт", "materials": {"дамп паролей": 2, "рабочий эксплойт": 1},
             "result": {"item": "боевой эксплойт", "skill": "hacking", "bonus": 3}, "cost": 2000},
            {"name": "тихий канал", "materials": {"перехваченный трафик": 2, "конфиг файрвола": 1},
             "result": {"item": "тихий канал", "skill": "stealth", "bonus": 3}, "cost": 3000},
            {"name": "локальная модель", "materials": {"обрывок чужой модели": 1, "рабочий эксплойт": 1},
             "result": {"item": "локальная модель", "skill": "programming", "bonus": 4}, "cost": 6000},
            {"name": "карта утечек", "materials": {"перехваченный трафик": 2, "дамп паролей": 2},
             "result": {"item": "карта утечек", "skill": "investigation", "bonus": 3}, "cost": 4000},
            {"name": "разогнанный перебор", "materials": {"ускоритель перебора": 3, "рабочий эксплойт": 1},
             "result": {"item": "разогнанный перебор", "skill": "hacking", "bonus": 5}, "cost": 9000},
            {"name": "поддельный пропуск", "materials": {"список контактов": 1, "дамп паролей": 1},
             "result": {"item": "поддельный пропуск", "skill": "social", "bonus": 3}, "cost": 5000},
            {"name": "самосборный тулкит", "materials": {"боевой эксплойт": 1, "тихий канал": 1, "карта утечек": 1},
             "result": {"item": "самосборный тулкит", "all_skills": 3}, "cost": 20000},
        ]

        while True:
            self.clear_screen()
            self.header("Сборка")
            print(f"  Кошелёк: {self.player.bitcoins}\n")
            for i, recipe in enumerate(recipes, 1):
                print(f"  {i}  {recipe['name']} — {recipe['cost']}")
                for material, count in recipe["materials"].items():
                    have = self.player.inventory.count(material)
                    mark = "+" if have >= count else "-"
                    print(f"       {mark} {material} x{count} (есть {have})")
            print(f"\n  {len(recipes) + 1}  Назад")
            print()

            raw = input("  > ").strip()
            if not raw.isdigit():
                continue
            choice = int(raw)
            if choice == len(recipes) + 1:
                return
            if not (1 <= choice <= len(recipes)):
                continue

            recipe = recipes[choice - 1]
            if self.player.bitcoins < recipe["cost"]:
                print("\n  Не хватает денег.")
                self.pause()
                continue
            if any(self.player.inventory.count(m) < c for m, c in recipe["materials"].items()):
                print("\n  Не хватает материалов.")
                self.pause()
                continue

            for material, count in recipe["materials"].items():
                for _ in range(count):
                    self.player.inventory.remove(material)
            self.player.bitcoins -= recipe["cost"]

            result = recipe["result"]
            self.player.inventory.append(result["item"])
            self.player.crafted_items.append(result["item"])
            self.player.personal_stats["items_crafted"] += 1
            print(f"\n  Собрал: {result['item']}")
            if "skill" in result:
                self.player.skills[result["skill"]] += result["bonus"]
                print(f"  {SKILL_NAMES[result['skill']]} +{result['bonus']}")
            if "all_skills" in result:
                for skill in self.player.skills:
                    self.player.skills[skill] += result["all_skills"]
                print(f"  все навыки +{result['all_skills']}")
            if len(self.player.crafted_items) >= 5:
                got = self.player.add_achievement("собрал свой тулкит")
                if got:
                    print("  " + got)
            self.pause()

    # ---------- ежедневки ----------

    def daily_missions(self):
        pool = [
            "взломать три цели",
            "закрыть два дела на бирже",
            "поднять любой навык",
            "пробить одну систему защиты",
            "разрулить два случайных события",
        ]
        self.clear_screen()
        self.header("На сегодня")
        print()
        for i, task in enumerate(random.sample(pool, 3), 1):
            print(f"  {i}  {task}")
        print("\n  Задачи закрываются сами, когда ты их делаешь.")
        print(f"  Закрыто всего: {self.player.daily_missions_completed}")
        self.pause()

    # ---------- фракции ----------

    def factions_menu(self):
        self.clear_screen()
        self.header("Связи")
        print()
        for faction in self.player.factions:
            rep = self.player.factions[faction]
            bar = "█" * min(30, abs(rep) // 20)
            print(f"  {FACTION_NAMES[faction]}")
            print(f"    {rep:+d}  {self.player.get_faction_rank(faction)}")
            print(f"    {bar}")
        print("\n  Кого держишься — того и правила.")
        self.pause()

    # ---------- сохранения ----------

    def save_specific_game(self, mode):
        self.clear_screen()
        self.header("Сохранить")
        print()
        for i in range(0, 4):
            path = self.data._save_path(i, mode)
            label = "автосейв" if i == 0 else f"слот {i}"
            if os.path.exists(path):
                try:
                    with open(path, 'rb') as f:
                        data = pickle.load(f)
                    print(f"  {i}  {label}: {data['player']['name']} — {data['timestamp'][:10]}")
                except (OSError, pickle.UnpicklingError):
                    print(f"  {i}  {label}: (повреждён)")
            else:
                print(f"  {i}  {label}: пусто")
        print("  5  Назад\n")

        raw = input("  > ").strip()
        if not raw.isdigit():
            return
        choice = int(raw)
        if choice == 5:
            return
        if 0 <= choice <= 3:
            if self.data.save_game(self.player.__dict__, choice, mode):
                print("\n  Сохранено.")
            else:
                print("\n  Не вышло сохранить.")
            self.pause()

    def load_specific_game(self, mode):
        saves = self.data.get_saves(mode)
        if not saves:
            print("\n  Сохранений нет.")
            self.pause()
            return

        self.clear_screen()
        self.header("Загрузить")
        print()
        for i in range(0, 4):
            path = self.data._save_path(i, mode)
            label = "автосейв" if i == 0 else f"слот {i}"
            if os.path.exists(path):
                try:
                    with open(path, 'rb') as f:
                        data = pickle.load(f)
                    p = data['player']
                    print(f"  {i}  {label}: {p['name']}, ур. {p['level']}, глава {p['story_progress']} — {data['timestamp'][:10]}")
                except (OSError, pickle.UnpicklingError):
                    print(f"  {i}  {label}: (повреждён)")
            else:
                print(f"  {i}  {label}: пусто")
        print("  5  Назад\n")

        raw = input("  > ").strip()
        if not raw.isdigit():
            return
        choice = int(raw)
        if choice == 5:
            return
        if 0 <= choice <= 3:
            data = self.data.load_game(choice, mode)
            if not data:
                print("\n  Не вышло загрузить.")
                self.pause()
                return
            self.player = Player("")
            self.player.__dict__.update(data['player'])
            self.game_mode = mode
            print("\n  Загружено.")
            self.pause()
            if mode == "story":
                self.play_story_mode()
            else:
                self.sandbox_loop()

    def load_game_menu(self):
        self.clear_screen()
        self.header("Загрузить")
        story = "есть" if self.data.get_saves("story") else "нет"
        sandbox = "есть" if self.data.get_saves("sandbox") else "нет"
        print(f"\n  1  Сюжет ({story})")
        print(f"  2  Свободный режим ({sandbox})")
        print("  3  Назад\n")
        choice = input("  > ").strip()
        if choice == "1":
            self.load_specific_game("story")
        elif choice == "2":
            self.load_specific_game("sandbox")

    # ---------- свободный режим ----------

    def sandbox_loop(self):
        self.game_mode = "sandbox"
        while True:
            if random.random() < 0.15:
                self.random_event()

            self.clear_screen()
            self.header("Свободный режим")
            print(f"  {self.player.name}   ур. {self.player.level}   кошелёк {self.player.bitcoins}")
            self.rule()
            print("  1  Взлом целей")
            print("  2  Барахолка")
            print("  3  Профиль")
            print("  4  Отметки")
            print("  5  Системы защиты")
            print("  6  Сборка")
            print("  7  Связи")
            print("  8  Дела на сегодня")
            print("  9  Сохранить")
            print("  0  В меню")
            self.rule()

            choice = input("  > ").strip()
            if choice == "1":
                self.hacking_menu()
            elif choice == "2":
                self.shop_menu()
            elif choice == "3":
                self.profile_menu()
            elif choice == "4":
                self.achievements_menu()
            elif choice == "5":
                self.boss_battles()
            elif choice == "6":
                self.crafting_menu()
            elif choice == "7":
                self.factions_menu()
            elif choice == "8":
                self.daily_missions()
            elif choice == "9":
                self.save_specific_game("sandbox")
            elif choice == "0":
                if self.data.config.get("autosave", True):
                    self.data.save_game(self.player.__dict__, 0, "sandbox")
                return

    # ---------- обновления / настройки / об игре ----------

    def check_for_updates(self):
        self.clear_screen()
        self.header("Обновления")
        if os.path.exists("updater.py"):
            print("\n  Запускаю проверку...\n")
            time.sleep(1)
            os.system(f'"{sys.executable}" updater.py')
        else:
            print("\n  Апдейтер не найден.")
        self.pause()

    def settings_menu(self):
        while True:
            self.clear_screen()
            self.header("Настройки")
            cfg = self.data.config
            print(f"  1  Сложность: {cfg['difficulty']}")
            print(f"  2  Автосохранение: {'вкл' if cfg['autosave'] else 'выкл'}")
            print(f"  3  Анимации: {'вкл' if cfg['animations'] else 'выкл'}")
            print("  4  Стереть сохранения")
            print("  5  Назад")
            self.rule()

            choice = input("  > ").strip()
            if choice == "1":
                order = ["easy", "normal", "hard"]
                cfg["difficulty"] = order[(order.index(cfg["difficulty"]) + 1) % 3]
                self.data.save_config()
            elif choice == "2":
                cfg["autosave"] = not cfg["autosave"]
                self.data.save_config()
            elif choice == "3":
                cfg["animations"] = not cfg["animations"]
                self.data.save_config()
            elif choice == "4":
                if input("  Стереть всё? (y/N): ").strip().lower() == "y":
                    for mode in ("story", "sandbox"):
                        for i in range(0, 4):
                            path = self.data._save_path(i, mode)
                            if os.path.exists(path):
                                os.remove(path)
                    print("  Стёр.")
                    self.pause()
            elif choice == "5":
                return

    def show_stats(self):
        self.clear_screen()
        self.header("Об игре")
        print()
        print("  Terminal Shadows — текстовая игра про хакера, который")
        print("  разбирает дела умершего дяди и постепенно упирается")
        print("  в то, во что упираться не стоило.")
        print()
        print(f"  Глав в сюжете: {len(chapters)}")
        print("  Есть свободный режим: цели, барахолка, системы защиты,")
        print("  сборка, случайные события, репутация.")
        print()
        print("  Рядом с тобой — Гид. Он не человек, и это заметно.")
        print()
        print(f"  Версия {GAME_VERSION}. Лицензия MIT.")
        self.pause()

    def game_complete(self):
        self.clear_screen()
        self.print_ascii("victory")
        self.header("Конец сюжета")
        p = self.player
        print(f"\n  {p.name}")
        print(f"  Уровень {p.level}   на кошельке {p.bitcoins}")
        print(f"  Отметок: {len(p.achievements)}/{len(self.ACHIEVEMENTS)}")
        print(f"  В игре, минут: {int(p.personal_stats['play_time'] // 60)}")
        print()
        self.guide("Дальше — без меня или со мной. Решать тебе. Как всегда.")
        print("\n  Свободный режим открыт.")
        self.pause()
        got = self.player.add_achievement("прошёл сюжет")
        if got:
            print("  " + got)
        self.sandbox_loop()

    def exit_game(self):
        if self.player:
            self.player.update_play_time(time.time() - self.start_time)
            if self.data.config.get("autosave", True) and self.game_mode:
                self.data.save_game(self.player.__dict__, 0, self.game_mode)
        self.clear_screen()
        self.rule()
        print(Fore.WHITE + "  Погас экран. Город остался снаружи." + Style.RESET_ALL)
        if self.player:
            self.guide("Я подожду. Мне некуда спешить.")
        self.rule()
        time.sleep(1.5)
        sys.exit(0)


if __name__ == "__main__":
    game = GameEngine()
    try:
        game.show_main_menu()
    except (KeyboardInterrupt, EOFError):
        print()
        game.exit_game()
    except Exception as e:
        import traceback
        print(f"\nОшибка: {e}")
        traceback.print_exc()

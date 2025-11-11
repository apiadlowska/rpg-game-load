import pygame
import sys
import random
import json
import os
import time

# ====================================================================
# --- 1. STAŁE GRY, MAPOWANIE I KONFIGURACJA PYGAME ---
# ====================================================================

pygame.init()

# Rozmiary okna
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 720
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Advanced D&D Text RPG")

# KOLORY
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GREY = (30, 30, 30)
LIGHT_GREY = (180, 180, 180)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 50, 200)
HERO_COLOR = (255, 215, 0)
ENEMY_COLOR = (150, 0, 0)
POISON_COLOR = (0, 150, 0)
STUN_COLOR = (255, 100, 0)
SNOW_COLOR = (200, 200, 255) # Kolor dla motywu zimowego

# Rozmiary dla mapy
HERO_MAP_SIZE = 32 
ENEMY_MAP_SIZE = 64

# Czcionki i Log
FONT_SIZE = 16
LOG_LINES = 10 # ZMNIEJSZONO LICZBĘ LINII LOGU, ABY ZMIEŚCIĆ GO NA GÓRZE
MAIN_SECTION_Y_START = 250 # Stała Y, gdzie zaczyna się główna treść (pod logiem)

try:
    FONT = pygame.font.Font(None, FONT_SIZE + 8)
    INPUT_FONT = pygame.font.Font(None, 32)
except:
    FONT = pygame.font.SysFont('arial', FONT_SIZE + 8)
    INPUT_FONT = pygame.font.SysFont('arial', 32)

# --- Ładowanie Grafiki (POPRAWIONA OBSŁUGA BŁĘDU) ---
GRAPHICS_LOADED = False
HERO_SPRITE_ORIGINAL = None 
ENEMY_SPRITE_ORIGINAL = None 
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 

try:
    HERO_SPRITE_ORIGINAL = pygame.image.load(os.path.join(BASE_DIR, 'hero.png')).convert_alpha()
    ENEMY_SPRITE_ORIGINAL = pygame.image.load(os.path.join(BASE_DIR, 'enemy.png')).convert_alpha()
    GRAPHICS_LOADED = True
    print("Ładowanie grafiki: Pomyślne.")
    
except pygame.error as e:
    GRAPHICS_LOADED = False
    print(f"Błąd ładowania grafiki: {e}. Gra użyje kolorowych kwadratów.")


# --- Mapowanie i Dane Gry ---

# NOWY SYSTEM TEMATÓW MAPY (ZIMA/STANDARD)
MAP_THEMES = {
    "default": {
        "town": {"color": GREEN, "name": "Miasto"},
        "enemy": {"color": RED, "name": "Las (Wrogowie)"},
        "treasure": {"color": (255, 255, 0), "name": "Skarb"},
        "dungeon": {"color": (100, 100, 100), "name": "Loch"},
        "shrine": {"color": (0, 255, 255), "name": "Kapliczka"},
        "empty": {"color": DARK_GREY, "name": "Pustkowie"},
        "probabilities": {"enemy": 0.30, "treasure": 0.45, "dungeon": 0.55, "shrine": 0.60},
        "enemies": ["Goblin", "Shadow Wolf", "Bandit", "Ghoul"],
    },
    "winter": {
        "town": {"color": (0, 150, 255), "name": "Zimowy Obóz"},
        "enemy": {"color": (150, 50, 50), "name": "Zaspy Śnieżne (Wrogowie)"},
        "treasure": {"color": (255, 255, 0), "name": "Zamrożony Skarb"},
        "dungeon": {"color": (50, 50, 50), "name": "Lodowy Labirynt"},
        "shrine": {"color": (200, 200, 255), "name": "Lodowy Ołtarz"},
        "empty": {"color": SNOW_COLOR, "name": "Śnieżna Pustka"},
        "probabilities": {"enemy": 0.35, "treasure": 0.40, "dungeon": 0.50, "shrine": 0.65}, 
        "enemies": ["Ice Goblin", "Frost Giant", "Snow Wolf", "Yeti"], 
    }
}
DEFAULT_THEME = MAP_THEMES["default"]


# ZAKTUALIZOWANE UMIEJĘTNOŚCI DLA RÓŻNORODNOŚCI ATAKÓW
HERO_CLASSES = {
    "Warrior": {'base_stats': {'STR': 14, 'DEX': 12, 'CON': 15, 'INT': 8, 'WIS': 10, 'CHA': 11}, 
                'skills': ["Heavy Blow", "Block", "Shatter Defense", "Taunt", "Vampiric Strike", "Shield Bash", "Rage"], 
                'equip': [{'name': 'Rusty Sword', 'type': 'weapon', 'value': 5, 'description': '+2 STR', 'equipable': True, 'stats': {'STR': 2}, 'slot': 'weapon'}, 
                          {'name': 'Leather Armor', 'type': 'armor', 'value': 10, 'description': '+1 CON', 'equipable': True, 'stats': {'CON': 1}, 'slot': 'armor'}]},
    "Mage": {'base_stats': {'STR': 8, 'DEX': 10, 'CON': 12, 'INT': 16, 'WIS': 14, 'CHA': 10}, 
             'skills': ["Fireball", "Heal", "Arcane Missile", "Ice Shard", "Mana Shield", "Magic Storm", "Teleport"], 
             'equip': [{'name': 'Staff of Power', 'type': 'weapon', 'value': 20, 'description': '+3 INT', 'equipable': True, 'stats': {'INT': 3}, 'slot': 'weapon'}, 
                      {'name': 'Cloth Robe', 'type': 'armor', 'value': 5, 'description': '+1 WIS', 'equipable': True, 'stats': {'WIS': 1}, 'slot': 'armor'}]},
    "Rogue": {'base_stats': {'STR': 10, 'DEX': 16, 'CON': 13, 'INT': 10, 'WIS': 10, 'CHA': 11}, 
              'skills': ["Sneak Attack", "Poison Edge", "Disarm", "Vanish", "Blind", "Shadow Step", "Execute"], 
              'equip': [{'name': 'Dagger', 'type': 'weapon', 'value': 15, 'description': '+3 DEX', 'equipable': True, 'stats': {'DEX': 3}, 'slot': 'weapon'}, 
                      {'name': 'Leather Vest', 'type': 'armor', 'value': 15, 'description': '+1 DEX', 'equipable': True, 'stats': {'DEX': 1}, 'slot': 'armor'}]},
}


# ====================================================================
# --- 2. KLASY MECHANIK GRY ---
# ====================================================================

# Funkcja rzutu kostką
def roll_d20(modifier):
    roll = random.randint(1, 20)
    final_roll = roll + modifier
    log_message = f"Rzut (1k20 + {modifier:+}): {roll} -> **{final_roll}**"
    
    result = "HIT"
    if roll == 20: result = "CRIT"; log_message += " (Krytyk!)"
    elif roll == 1: result = "MISS"; log_message += " (Pudło!)"
    
    return result, final_roll, log_message

# --- Klasy Pomocnicze (Status Effect) ---

class StatusEffect:
    def __init__(self, name, duration, value=0, turns_left=0, is_debuff=True):
        self.name = name; self.duration = duration; self.value = value
        self.turns_left = turns_left or duration; self.is_debuff = is_debuff

    def apply_effect(self, target, interface):
        if self.name == "Poison":
            dmg = self.value
            target.hp = max(0, target.hp - dmg)
            interface.add_to_log(f"|-- {target.name} cierpi na **Poison** i traci {dmg} HP. Pozostało: {target.hp}.")
        elif self.name == "Stun" or self.name == "Blinded":
            interface.add_to_log(f"|-- {target.name} jest **{self.name}** i traci turę/atak.")
        elif self.name == "Defense Down": 
            interface.add_to_log(f"|-- **{target.name}** ma obniżoną obronę (-{self.value} AC).")
        elif self.name == "Taunt": 
            interface.add_to_log(f"|-- **{target.name}** jest sprowokowany i atakuje tylko bohatera.")
        elif self.name == "Rage": # Buff
             interface.add_to_log(f"|-- **{target.name}** jest w furii (+$2 STR).")
             
        self.turns_left -= 1

    def to_dict(self):
        return {'name': self.name, 'duration': self.duration, 'value': self.value, 'turns_left': self.turns_left, 'is_debuff': self.is_debuff}

    @staticmethod
    def from_dict(data):
        return StatusEffect(data['name'], data['duration'], data['value'], data['turns_left'], data.get('is_debuff', True))

# --- Item, Quest, Shop, QuestBoard ---

class Item:
    def __init__(self, name, item_type, value, description, equipable=False, stats=None, item_slot=None):
        self.name = name; self.type = item_type; self.value = value; self.description = description
        self.equipable = equipable; self.stats = stats or {}; self.slot = item_slot
    def __str__(self): return f"{self.name}: {self.description}"
    
    def to_dict(self):
        return {
            'name': self.name, 'item_type': self.type, 'value': self.value, 'description': self.description,
            'equipable': self.equipable, 'stats': self.stats, 'item_slot': self.slot
        }

def create_item_from_dict(data):
    if data is None: return None
    return Item(data['name'], data['item_type'], data['value'], data['description'], 
                data['equipable'], data['stats'], data.get('item_slot'))


class Quest:
    def __init__(self, name, description, quest_type, target, reward_gold, reward_exp, reward_items=None, main_quest=False):
        self.name = name; self.description = description; self.type = quest_type; self.target = target
        self.progress = 0; self.reward_gold = reward_gold; self.reward_exp = reward_exp
        self.reward_items = reward_items or []; self.completed = False
        self.main_quest = main_quest 
    def update_progress(self, amount=1, interface=None):
        if not self.completed:
            self.progress += amount
            if self.progress >= self.target: self.progress = self.target; self.completed = True
            if self.completed and interface: 
                interface.add_to_log(f"\nZadanie '{self.name}' ukończone! Odbierz nagrodę w Mieście!")
    def give_reward(self, hero, interface):
        if self.completed:
            hero.gain(self.reward_gold, self.reward_exp)
            for item_data in self.reward_items:
                if isinstance(item_data, dict): 
                    item = Item(item_data['name'], item_type=item_data['item_type'], value=item_data['value'], description=item_data['description'], equipable=item_data['equipable'], stats=item_data['stats'], item_slot=item_data.get('item_slot'))
                    hero.inventory.append(item)
            
            if self.main_quest:
                interface.add_to_log("\n\n*** WIELKIE ZWYCIĘSTWO! ZAKOŃCZYŁEŚ GRĘ! ***")
                return "WIN"

            interface.add_to_log(f"Odebrano nagrodę: {self.reward_gold} złota, {self.reward_exp} exp.")
            return True
        return False
        
    def to_dict(self):
        return {
            'name': self.name, 'description': self.description, 'quest_type': self.type, 'target': self.target,
            'progress': self.progress, 'reward_gold': self.reward_gold, 'reward_exp': self.reward_exp,
            'reward_items': self.reward_items, 
            'completed': self.completed, 'main_quest': self.main_quest
        }

def create_quest_from_dict(data):
    q = Quest(data['name'], data['description'], data['quest_type'], data['target'], 
              data['reward_gold'], data['reward_exp'], reward_items=data['reward_items'], main_quest=data['main_quest'])
    q.progress = data['progress']
    q.completed = data['completed']
    return q


class Shop:
    def __init__(self):
        self.items = [
            Item("Mikstura leczenia (Mała)", "potion", 15, "Przywraca 30 HP", False, {'heal': 30}),
            Item("Mikstura Many", "potion", 25, "Przywraca 40 Many", False, {'mana': 40}),
            Item("Pierścień Siły", "ring", 150, "+2 STR", True, {'STR': 2}, item_slot="ring"),
            Item("Topór Bitewny", "weapon", 120, "+5 STR", True, {'STR': 5}, item_slot="weapon"),
            Item("Szata Arkaniczna", "armor", 150, "+3 INT", True, {'INT': 3}, item_slot="armor"),
        ]
    def get_price_modifier(self, hero, action="buy"): return 1.0 
    def display_items(self, hero, interface):
        mod = self.get_price_modifier(hero, "buy")
        interface.add_to_log("\n--- Dostępne przedmioty w sklepie ---")
        for i, item in enumerate(self.items):
            price = int(item.value * mod)
            interface.add_to_log(f"[{i+1}] {item.name} ({price} złota): {item.description}")
        interface.add_to_log("Wpisz 'buy [numer]' lub 'exit'.")
    def buy_item(self, hero, item_index, interface):
        if 0 <= item_index < len(self.items):
            item_data = self.items[item_index]
            price = int(item_data.value * self.get_price_modifier(hero, "buy"))
            if hero.gold >= price:
                hero.gold -= price
                new_item = Item(item_data.name, item_data.type, item_data.value, item_data.description, item_data.equipable, item_data.stats.copy(), item_data.slot)
                hero.inventory.append(new_item)
                interface.add_to_log(f"Kupiłeś **{new_item.name}** za {price} złota.")
                return True
            else: interface.add_to_log("Nie masz wystarczająco złota!")
        return False

class QuestBoard:
    def __init__(self):
        self.available_quests = [
            Quest("Zabij 5 Goblinów", "Zlikwiduj 5 sztuk Goblinów.", "defeat_enemies", 5, 100, 50),
            Quest("Zrujnowany Klasztor", "Pokonaj bossa w lochu! *Główne Zadanie*", "defeat_boss", 1, 500, 500, reward_items=[{'name': 'Miecz Mistrza', 'type': 'weapon', 'value': 500, 'description': '+10 STR', 'equipable': True, 'stats': {'STR': 10}, 'item_slot': 'weapon'}], main_quest=True),
            Quest("Pokonaj 3 Cienie", "Wytrop i pokonaj 3 wrogów typu Shadow Wolf.", "defeat_enemies_type", 3, 250, 150),
        ]
        self.shop_instance = Shop()
    def display_board(self, hero, interface):
        interface.add_to_log("\n--- Tablica Ogłoszeń (Quest Board) ---")
        if hero.current_quests:
            interface.add_to_log("\n**Aktywne zadania:**")
            for q in hero.current_quests:
                status = "**Ukończone, ODBIERZ!**" if q.completed else f"W toku: {q.progress}/{q.target}"
                interface.add_to_log(f"- **{q.name}** ({q.type}): {status}")
            interface.add_to_log("Wpisz 'claim [nazwa zadania]' aby odebrać.")
        interface.add_to_log("\n**Dostępne nowe zlecenia:**")
        for i, quest in enumerate(self.available_quests):
            interface.add_to_log(f"[{i+1}] **{quest.name}** - Nagroda: {quest.reward_gold} złota.")
        interface.add_to_log("Wpisz 'accept [numer]' lub 'exit'.")

    def accept_quest(self, hero, index, interface):
        try:
            selected_quest = self.available_quests[index]
            if any(q.name == selected_quest.name for q in hero.current_quests):
                interface.add_to_log("To zadanie jest już aktywne!")
                return False
                
            # Tworzymy kopię zadania, aby miało oddzielny postęp
            new_quest = create_quest_from_dict(selected_quest.to_dict())
            hero.current_quests.append(new_quest)
            
            # Usuwamy z dostępnych, jeśli nie jest to powtarzalne (domyślnie usuwamy)
            if not new_quest.main_quest:
                 self.available_quests.pop(index)
                 
            interface.add_to_log(f"Przyjęto zadanie: **{new_quest.name}**.")
            return True
        except IndexError: 
            interface.add_to_log("Błędny numer zadania.")
            return False

class World:
    def __init__(self, size=15, theme="default"): # DODANO ARGUMENT theme
        self.size = size
        self.map = [[None for _ in range(size)] for _ in range(size)]
        self.hero_position = (0, 0)
        self.theme_name = theme # ZAPIS TEMATU
        self.theme_data = MAP_THEMES.get(theme, DEFAULT_THEME) # Wczytanie danych tematu
        self.generate_map()
        
    def generate_map(self):
        theme_probs = self.theme_data["probabilities"]
        
        for x in range(self.size):
            for y in range(self.size):
                rand = random.random()
                
                # Używamy ustalonych prawdopodobieństw z tematu
                if rand < theme_probs["enemy"]: 
                    self.map[x][y] = "enemy"
                elif rand < theme_probs["treasure"]: 
                    self.map[x][y] = "treasure"
                elif rand < theme_probs["dungeon"]: 
                    self.map[x][y] = "dungeon"
                elif rand < theme_probs["shrine"]: 
                    self.map[x][y] = "shrine"
                else: 
                    self.map[x][y] = "empty"
                    
        self.map[self.hero_position[0]][self.hero_position[1]] = "town"
        
    def get_current_location(self):
        x, y = self.hero_position
        return self.map[x][y]
        
    def move_hero(self, direction, hero, interface):
        x, y = self.hero_position; new_x, new_y = x, y
        
        if direction == "north": new_x = x - 1
        elif direction == "south": new_x = x + 1
        elif direction == "east": new_y = y + 1
        elif direction == "west": new_y = y - 1
        else:
            interface.add_to_log("Nieprawidłowy kierunek. Użyj: north, south, east, west."); return

        if 0 <= new_x < self.size and 0 <= new_y < self.size:
            self.hero_position = (new_x, new_y); location_type = self.map[new_x][new_y]
            location_name = self.theme_data[location_type]["name"] # Nazwa z tematu
            interface.add_to_log(f"\nPrzesunięto się na pozycję: **{new_x}**, **{new_y}**. Lokalizacja: **{location_name.upper()}**.")
            
            enemies_to_fight = []
            
            if location_type == "enemy":
                # Wybór wrogów na podstawie tematu mapy
                enemy_pool = self.theme_data["enemies"]
                enemy_type = random.choice(enemy_pool) 
                
                # Uproszczone statystyki wrogów (dla przykładu)
                if enemy_type == "Goblin" or enemy_type == "Ice Goblin": 
                    enemies_to_fight.append(Enemy(enemy_type, 50, 10, 30, 20, 12, interface=interface, enemy_type=enemy_type))
                elif enemy_type == "Shadow Wolf" or enemy_type == "Snow Wolf": 
                    enemies_to_fight.append(Enemy(enemy_type, 65, 13, 50, 40, 15, interface=interface, enemy_type=enemy_type))
                elif enemy_type == "Bandit": 
                    enemies_to_fight.append(Enemy(enemy_type, 80, 15, 60, 50, 14, interface=interface, enemy_type=enemy_type))
                elif enemy_type == "Frost Giant" or enemy_type == "Yeti":
                     enemies_to_fight.append(Enemy(enemy_type, 120, 18, 100, 70, 16, interface=interface, enemy_type=enemy_type))
                
                interface.start_combat(enemies_to_fight) 
            
            elif location_type == "treasure":
                gold = random.randint(50, 150); item_chance = random.random()
                hero.gain(gold)
                interface.add_to_log(f"Znalazłeś skarb: **{gold} złota**!")
                if item_chance > 0.7:
                     new_item = Item("Amulet Szczęścia", "amulet", 75, "+1 CHA, +1 WIS", True, {'CHA': 1, 'WIS': 1}, item_slot="amulet")
                     hero.inventory.append(new_item)
                     interface.add_to_log(f"Otrzymujesz rzadki przedmiot: **{new_item.name}**.")

                self.map[new_x][new_y] = "empty"
                
            elif location_type == "dungeon":
                interface.add_to_log(f"Wkraczasz do **{location_name}**!")
                is_main_quest_active = any(q.name == "Zrujnowany Klasztor" and not q.completed for q in hero.current_quests)
                
                if is_main_quest_active:
                    boss_name = "Straszliwy Kultysta" if self.theme_name == "default" else "Władca Mrozu"
                    boss = Enemy(boss_name, 400, 25, 750, 750, 18, interface=interface, is_boss=True, enemy_type="Cultist")
                    enemies_to_fight.append(boss)
                else:
                    num_enemies = random.randint(1, 3) 
                    for _ in range(num_enemies):
                        enemy_name = "Ghoul" if self.theme_name == "default" else "Ożywiec z Lodu"
                        enemies_to_fight.append(Enemy(enemy_name, 90, 16, 40, 30, 13, interface=interface, enemy_type="Undead"))
                
                if enemies_to_fight:
                    interface.start_combat(enemies_to_fight)
            
            elif location_type == "shrine":
                interface.add_to_log(f"Odpoczywasz w **{location_name}**. Mana przywrócona.")
                hero.mana = hero.max_mana
            
            elif location_type == "town": interface.add_to_log(f"Jesteś w bezpiecznym {location_name}.")
            elif location_type == "empty": interface.add_to_log(f"{location_name}. Kontynuuj podróż.")
        else: 
            interface.add_to_log("⛔ Nie można się tam ruszyć (granica mapy)."); return

    def to_dict(self):
        # Zapisujemy również nazwę tematu
        return {'size': self.size, 'map': self.map, 'hero_position': self.hero_position, 'theme_name': self.theme_name}


class Hero:
    def __init__(self, name, hero_class_name, interface=None):
        class_data = HERO_CLASSES.get(hero_class_name, HERO_CLASSES["Warrior"])
        self.name = name; self.hero_class = hero_class_name; self.interface = interface
        
        # --- NOWE ATRYBUTY BAZOWE (STR, DEX, CON, INT, WIS, CHA) ---
        self.attributes = class_data["base_stats"].copy()
        
        # --- EKWIPUNEK (MUSI BYĆ ZDEFINIOWANY PIERWSZY!) - FIX BŁĘDU!
        self.equipped_weapon = None; self.equipped_armor = None 
        self.equipped_ring = None; self.equipped_amulet = None
        
        # --- STATYSTYKI POMOCNICZE ---
        self.gold = 100; self.exp = 0; self.level = 1; self.attribute_points = 0 
        self.inventory = []; self.skills = class_data["skills"]; 
        self.status_effects = {} # Status efekty
        self.current_quests = []
        
        # --- STATYSTYKI POCHODNE ---
        self.hp = self.calculate_max_hp(); self.max_hp = self.calculate_max_hp()
        self.mana = self.calculate_max_mana(); self.max_mana = self.calculate_max_mana()
        self.atk = self.calculate_atk(); self.defense = self.calculate_ac()
        
        # Wskaźniki specyficzne dla walki
        self.is_shadow_stepping = False # Flagga dla Shadow Step (Rogue)
        
        # Wyposażenie startowe i przeliczenie statystyk
        for item_data in class_data["equip"]:
              item = Item(item_data['name'], item_data['type'], item_data['value'], item_data['description'], item_data['equipable'], item_data['stats'], item_data.get('slot'))
              self.equip_item(item, start_equip=True)

        self._update_derived_stats() # Upewnienie się, że staty są aktualne po ekwipunku

    # --- METODY PRZELICZANIA STATYSTYK BAZOWYCH ---
    def get_mod(self, stat_name): 
        return (self.attributes.get(stat_name, 10) - 10) // 2

    def calculate_max_hp(self): 
        return 100 + (self.get_mod('CON') * 10) + (self.level * 5)
    
    def calculate_max_mana(self):
          return 50 + (self.get_mod('INT') * 10) + (self.level * 3)

    def calculate_atk(self): 
        if self.hero_class == "Warrior": return 10 + self.get_mod('STR') * 2
        if self.hero_class == "Rogue": return 10 + self.get_mod('DEX') * 2
        if self.hero_class == "Mage": return 10 + self.get_mod('STR')
        return 10 + self.get_mod('STR')
    
    def calculate_ac(self):
        armor_bonus = 0
        if self.equipped_armor:
            # Bardziej zaawansowana logika AC może uwzględniać ekwipunek i klasę
            armor_bonus = self.get_mod('CON') if self.hero_class == "Warrior" else 0 
        
        # Dodatkowe modyfikatory z efektów statusu (np. Armor Up, lub Armor Down)
        ac_mod = 0
        if "Defense Down" in self.status_effects:
             ac_mod -= self.status_effects["Defense Down"].value # Obniżenie z debuffa
        if "Mana Shield" in self.status_effects:
             ac_mod += self.status_effects["Mana Shield"].value 

        return 10 + self.get_mod('DEX') + armor_bonus + ac_mod

    def _update_derived_stats(self):
        self.max_hp = self.calculate_max_hp()
        self.max_mana = self.calculate_max_mana()
        self.atk = self.calculate_atk()
        self.defense = self.calculate_ac()
        
        self.hp = min(self.hp, self.max_hp)
        self.mana = min(self.mana, self.max_mana)
    
    # --- Metody akcji bohatera ---
    def attack_basic(self, target_AC):
        # Roll d20 + modyfikator ataku (STR lub DEX)
        hit_mod = self.get_mod('STR') if self.hero_class == "Warrior" else self.get_mod('DEX')
        roll_result, final_roll, log_message = roll_d20(hit_mod)
        
        # Gwarantowany krytyk po Shadow Step
        if self.is_shadow_stepping:
            roll_result = "CRIT"; log_message += " (Gwarantowany Krytyk po Shadow Step!)"
            self.is_shadow_stepping = False
            
        if self.interface: self.interface.add_to_log(log_message)

        # Upewnienie się, że defense jest przeliczone z uwzględnieniem efektów
        current_target_AC = target_AC 
        
        if final_roll < current_target_AC or roll_result == "MISS": return 0
        
        base_dmg = random.randint(1, 6) + hit_mod
        dmg = base_dmg + (self.equipped_weapon.stats.get('ATK', 0) if self.equipped_weapon else 0)
        final_dmg = dmg * 2 if roll_result == "CRIT" else dmg
        
        return max(1, int(final_dmg))

    def use_skill(self, skill_name, target_enemy=None, target_list=None):
        
        # Wskaźnik many dla wszystkich nowych i starych umiejętności
        cost_map = {"Heavy Blow": 15, "Block": 10, "Shatter Defense": 20, "Taunt": 10, "Vampiric Strike": 25, "Shield Bash": 20, "Rage": 30, # Warrior
                    "Fireball": 20, "Heal": 25, "Arcane Missile": 15, "Ice Shard": 15, "Mana Shield": 20, "Magic Storm": 40, "Teleport": 30, # Mage
                    "Sneak Attack": 20, "Poison Edge": 15, "Disarm": 15, "Vanish": 20, "Blind": 25, "Shadow Step": 35, "Execute": 40} # Rogue
        
        cost = cost_map.get(skill_name, 0)
        
        if self.mana < cost: 
            if self.interface: self.interface.add_to_log(f"Brak many na {skill_name} ({cost} MP)."); return 0, None, None # Dmg, Status, Efekt
        self.mana -= cost
        
        # --- ZDOLNOŚCI WSPARCIA I OBRONY ---
        
        if skill_name == "Heal":
            heal_amount = random.randint(10, 25) + self.get_mod('WIS') * 2
            self.hp = min(self.hp + heal_amount, self.max_hp)
            if self.interface: self.interface.add_to_log(f"**Heal**: +{heal_amount} HP. ({self.hp}/{self.max_hp})"); return -1, None, None
        
        if skill_name == "Block":
            if self.interface: self.interface.add_to_log(f"**Block**: Zwiększasz obronę w tej turze!"); return -1, None, None

        if skill_name == "Mana Shield":
            self.apply_status(StatusEffect("Mana Shield", duration=2, value=10, is_debuff=False)) # np. +10 do AC przez 2 tury
            if self.interface: self.interface.add_to_log(f"**Mana Shield**: Tarcza absorbuje część obrażeń przez 2 tury!"); return -1, None, None
            
        if skill_name == "Rage": # Buff dla Wojownika
             self.apply_status(StatusEffect("Rage", duration=3, value=2, is_debuff=False)) # +2 do modyfikatora STR
             if self.interface: self.interface.add_to_log(f"**Rage**: Wpadłeś w szał! Twoja siła wzrasta na 3 tury!");
             self.attributes['STR'] += 2 # Natychmiastowa zmiana statystyki bazowej
             self._update_derived_stats()
             return -1, None, None
             
        if skill_name == "Taunt":
             if target_enemy is None:
                 if self.interface: self.interface.add_to_log(f"Taunt wymaga celu! Komenda: skill taunt [nr]."); return 0, None, None
             target_enemy.apply_status(StatusEffect("Taunt", duration=2, value=0))
             if self.interface: self.interface.add_to_log(f"**Taunt**: {target_enemy.name} jest sprowokowany na 2 tury!"); return -1, None, None
             
        if skill_name == "Vanish":
            if self.interface: self.interface.add_to_log(f"**Vanish**: Znikasz w cieniu, resetując aggro. Następna próba ucieczki ma +30% szansy."); 
            return -1, "VANISH", None # Efekt VANISH (większa szansa na ucieczkę)
            
        if skill_name == "Teleport":
            self.apply_status(StatusEffect("Teleporting", duration=1, is_debuff=False)) # Status uniemożliwiający trafienie w tej turze
            if self.interface: self.interface.add_to_log(f"**Teleport**: Unikasz wszystkich ataków wroga w tej turze!");
            return -1, "INVULNERABLE", None
            
        if skill_name == "Shadow Step":
            self.is_shadow_stepping = True
            if self.interface: self.interface.add_to_log(f"**Shadow Step**: Następny atak jest gwarantowanym krytykiem!");
            return -1, None, None
        
        # --- ZDOLNOŚCI ATAKUJĄCE/DEBUFFUJĄCE ---
        
        # Magiczna Burza (Magic Storm) - atak obszarowy
        if skill_name == "Magic Storm":
             
             if not target_list:
                 if self.interface: self.interface.add_to_log("Magic Storm wymaga listy celów (do 3)."); return 0, None, None

             hit_mod = self.get_mod('INT')
             total_dmg = 0
             
             for i, enemy in enumerate(target_list[:3]):
                 roll_result, final_roll, log_message = roll_d20(hit_mod - 2) # Lekkie obniżenie celności
                 if self.interface: self.interface.add_to_log(f"[{enemy.name}] {log_message}")
                 
                 if final_roll >= enemy.get_current_AC() and roll_result != "MISS":
                     base_dmg = (self.atk * 0.5) + self.get_mod('INT') * 2
                     dmg = max(1, int(base_dmg))
                     
                     if roll_result == "CRIT": dmg *= 2
                     
                     enemy.take_damage(dmg)
                     total_dmg += dmg
                     if self.interface: self.interface.add_to_log(f"**Magic Storm** uderza {enemy.name} za {dmg} obrażeń.")
                     
             if total_dmg > 0: return -2, None, None # -2 oznacza atak obszarowy
             else: return 0, None, None


        if not target_enemy and skill_name not in ["Heal", "Block", "Mana Shield", "Vanish", "Teleport", "Rage", "Shadow Step"]:
            if self.interface: self.interface.add_to_log("Nie wybrano celu!"); return 0, None, None

        target_AC = target_enemy.get_current_AC() # Pobranie AC z uwzględnieniem debuffów
        
        # Modyfikatory trafienia
        if skill_name in ["Heavy Blow", "Shatter Defense", "Taunt", "Vampiric Strike", "Shield Bash", "Rage"]: hit_mod = self.get_mod('STR') 
        elif skill_name in ["Fireball", "Arcane Missile", "Ice Shard", "Mana Shield"]: hit_mod = self.get_mod('INT') 
        elif skill_name in ["Sneak Attack", "Poison Edge", "Disarm", "Vanish", "Blind", "Shadow Step", "Execute"]: hit_mod = self.get_mod('DEX')
        else: hit_mod = self.get_mod('STR')

        roll_result, final_roll, log_message = roll_d20(hit_mod)
        
        if self.interface: self.interface.add_to_log(log_message)

        if final_roll < target_AC or roll_result == "MISS": return 0, None, None

        # Obrażenia Umiejętności
        base_dmg = 0
        status_to_apply = None
        additional_effect = None

        if skill_name == "Heavy Blow":
            base_dmg = (self.atk * 1.5) + self.get_mod('STR') * 3
        elif skill_name == "Shatter Defense":
            base_dmg = (self.atk * 1.0) + self.get_mod('STR') * 2
            status_to_apply = StatusEffect("Defense Down", duration=3, value=3)
        elif skill_name == "Vampiric Strike":
             base_dmg = (self.atk * 1.2) + self.get_mod('STR') * 3
             additional_effect = "HEAL_DMG_PERCENT_50" # Uleczenie za 50% obrażeń
        elif skill_name == "Shield Bash":
             base_dmg = (self.atk * 0.8) + self.get_mod('CON') * 2
             if random.random() > 0.6: status_to_apply = StatusEffect("Stun", duration=1)
        
        elif skill_name == "Fireball":
            base_dmg = (self.atk * 0.5) + self.get_mod('INT') * 5
        elif skill_name == "Arcane Missile":
             base_dmg = (self.atk * 0.8) + self.get_mod('INT') * 3
        elif skill_name == "Ice Shard":
             base_dmg = (self.atk * 0.7) + self.get_mod('INT') * 4
             if random.random() > 0.7:
                 status_to_apply = StatusEffect("Stun", duration=1) 
                 
        elif skill_name == "Sneak Attack":
            base_dmg = (self.atk * 2.0) + self.get_mod('DEX') * 4
        elif skill_name == "Poison Edge":
            base_dmg = (self.atk * 1.2) + self.get_mod('DEX') * 3
            status_to_apply = StatusEffect("Poison", duration=3, value=5) 
        elif skill_name == "Disarm":
            base_dmg = (self.atk * 0.5) + self.get_mod('DEX') * 2
            if random.random() > 0.5:
                status_to_apply = StatusEffect("Disarmed", duration=1) 
        elif skill_name == "Blind":
            base_dmg = (self.atk * 0.1) + self.get_mod('DEX') * 1
            if random.random() > 0.6:
                status_to_apply = StatusEffect("Blinded", duration=2) 
        elif skill_name == "Execute":
             # Wymaga, aby HP wroga było niskie (np. poniżej 20%)
             if target_enemy.hp / target_enemy.max_hp < 0.2:
                 base_dmg = target_enemy.hp + 1 # Gwarantowany kill
                 if self.interface: self.interface.add_to_log(f"**Execute**: Śmiertelny Cios!");
             else:
                 base_dmg = (self.atk * 1.5) + self.get_mod('DEX') * 5
                 if self.interface: self.interface.add_to_log(f"**Execute**: Wróg ma zbyt dużo HP, by go wykończyć. Zwykłe uderzenie.");


        final_dmg = base_dmg * 2 if roll_result == "CRIT" else base_dmg
        
        return max(1, int(final_dmg)), status_to_apply, additional_effect # Dmg, Status, Dodatkowy efekt
        
    def equip_item(self, item, start_equip=False):
        if not item.equipable or not item.slot: return False
        
        slot_map = {"weapon": "equipped_weapon", "armor": "equipped_armor", "ring": "equipped_ring", "amulet": "equipped_amulet"}
        current_slot_attr = slot_map.get(item.slot)
        
        old_item = getattr(self, current_slot_attr)
        if old_item: self._unequip_item_stats(old_item); setattr(self, current_slot_attr, None)

        setattr(self, current_slot_attr, item)
        self._equip_item_stats(item)
        self._update_derived_stats() 

        if old_item and not start_equip: self.inventory.append(old_item)
        if not start_equip and item in self.inventory: self.inventory.remove(item)
        if self.interface and not start_equip: self.interface.add_to_log(f"Wyposażono **{item.name}**."); return True
        return True
        
    def _equip_item_stats(self, item):
        for stat, value in item.stats.items():
            current_value = self.attributes.get(stat, 0)
            self.attributes[stat] = current_value + value
            
    def _unequip_item_stats(self, item):
        for stat, value in item.stats.items():
            current_value = self.attributes.get(stat, 0)
            self.attributes[stat] = current_value - value
        
    def rest(self):
        self.hp = self.max_hp; self.mana = self.max_mana
        # Usuwanie debuffów przy odpoczynku
        self.status_effects = {k: v for k, v in self.status_effects.items() if not v.is_debuff}
        
        # Usunięcie buffa Rage (jeśli jest)
        if "Rage" in self.status_effects:
             self._remove_rage_buff()
             
        if self.interface: self.interface.add_to_log("Odpocząłeś całkowicie. HP i Mana przywrócone.")
        
    def _remove_rage_buff(self):
         if "Rage" in self.status_effects:
              rage_value = self.status_effects["Rage"].value
              self.attributes['STR'] -= rage_value
              del self.status_effects["Rage"]
              self._update_derived_stats()
              if self.interface: self.interface.add_to_log("Status Furia minął (STR wróciło do normy).")
        
    def gain(self, gold=0, exp=0): 
        self.gold += gold; self.exp += exp; self.level_up()
    
    def level_up(self):
        need = 100 * self.level 
        while self.exp >= need:
            self.exp -= need; self.level += 1
            self.attribute_points += 2
            self.hp = self.max_hp; self.mana = self.max_mana
            self._update_derived_stats()
            if self.interface: 
                 self.interface.add_to_log(f"\n*** AWANS! Osiągnięto poziom **{self.level}**! ***")
                 self.interface.add_to_log(f"Otrzymano {self.attribute_points} Punkty Atrybutów. Przydziel je komendą 'allocate'.")
                 self.interface.set_game_state("STAT_ALLOCATION")
            need = 100 * self.level
            
    def assign_attribute_point(self, stat_name):
        stat_name = stat_name.upper()
        if self.attribute_points > 0 and stat_name in self.attributes:
            self.attributes[stat_name] += 1
            self.attribute_points -= 1
            self._update_derived_stats()
            if self.interface: self.interface.add_to_log(f"**{stat_name}** zwiększone do {self.attributes[stat_name]}. Pozostało punktów: {self.attribute_points}")
            return True
        elif stat_name not in self.attributes:
             if self.interface: self.interface.add_to_log(f"Nieznany atrybut: {stat_name}. Dostępne: STR, DEX, CON, INT, WIS, CHA.")
        else:
             if self.interface: self.interface.add_to_log("Brak punktów atrybutów do przydzielenia.")
        return False
        
    def take_damage(self, dmg): 
        
        # Teleporting (Unikanie)
        if "Teleporting" in self.status_effects:
            if self.interface: self.interface.add_to_log(f"**Teleport**: Bohater uniknął ataku, teleportując się!")
            return 0
        
        # Ochrona przed Mana Shield
        if "Mana Shield" in self.status_effects:
             shield_value = self.status_effects["Mana Shield"].value
             absorbed_dmg = min(dmg, shield_value)
             
             dmg -= absorbed_dmg
             self.mana -= absorbed_dmg # Koszt absorpcji
             
             if self.mana < 0: # Jeśli mana spadnie poniżej 0, tarcza spada
                 dmg -= self.mana # Przeniesienie reszty obrażeń
                 self.mana = 0
                 del self.status_effects["Mana Shield"]
                 if self.interface: self.interface.add_to_log(f"**Mana Shield** załamała się! Wchłonięto {absorbed_dmg + self.mana} obrażeń.")
             else:
                 if self.interface: self.interface.add_to_log(f"**Mana Shield** wchłonęła {absorbed_dmg} obrażeń.")

        self.hp = max(0, self.hp - dmg)
        return dmg
    
    def is_alive(self): return self.hp > 0

    def apply_status(self, effect):
        # Specjalne obsługa buffa Rage
        if effect.name == "Rage":
             if effect.name in self.status_effects: # Resetuje czas trwania
                 self.status_effects[effect.name].turns_left = effect.duration
                 return
             
             self.status_effects[effect.name] = effect
             # Zmiana STR jest już w use_skill/Rage, tutaj tylko komunikat
             if self.interface: self.interface.add_to_log(f"Bohater został dotknięty statusem **{effect.name}**!")
             return
             
        # Specjalne obsługa debuffów na bohaterze
        if effect.name == "Defense Down": 
             if effect.name in self.status_effects: del self.status_effects[effect.name]
             self.status_effects[effect.name] = effect
             self._update_derived_stats()
             if self.interface: self.interface.add_to_log(f"Bohater został dotknięty statusem **{effect.name}**!")
             return

        if effect.name not in self.status_effects or effect.turns_left > self.status_effects[effect.name].turns_left:
             self.status_effects[effect.name] = effect
             if self.interface: self.interface.add_to_log(f"Bohater został dotknięty statusem **{effect.name}**!")
    
    def process_status_effects(self, interface):
        
        # Sprawdzanie i usuwanie Rage (Buff)
        if "Rage" in self.status_effects:
             effect = self.status_effects["Rage"]
             effect.apply_effect(self, interface)
             if effect.turns_left <= 0:
                 self._remove_rage_buff()
                 
        # Sprawdzanie i usuwanie Defense Down
        if "Defense Down" in self.status_effects:
             effect = self.status_effects["Defense Down"]
             effect.turns_left -= 1
             if effect.turns_left <= 0:
                 del self.status_effects["Defense Down"]
                 interface.add_to_log(f"Status **Defense Down** minął.")
                 self._update_derived_stats() 
             else:
                  interface.add_to_log(f"|-- Bohater ma obniżoną obronę. Pozostało: {effect.turns_left} tur.")
                  
        # Sprawdzanie i usuwanie Teleporting
        if "Teleporting" in self.status_effects:
            effect = self.status_effects["Teleporting"]
            effect.turns_left -= 1
            if effect.turns_left <= 0:
                del self.status_effects["Teleporting"]
                interface.add_to_log(f"Status **Teleporting** minął.")


        active_effects = list(self.status_effects.keys())
        for name in active_effects:
            if name in ["Defense Down", "Rage", "Teleporting"]: continue # Już obsłużone
            effect = self.status_effects[name]
            
            # Wpływ na postać gracza (np. Poison)
            if name in ["Poison"]: 
                 effect.apply_effect(self, interface)
            # Wpływ na walkę (np. Stun/Frozen)
            elif name in ["Stun", "Frozen"]:
                 effect.turns_left -= 1
                 interface.add_to_log(f"|-- Bohater jest {name}!")

            if effect.turns_left <= 0:
                del self.status_effects[name]
                interface.add_to_log(f"Status **{name}** minął.")


    def to_dict(self):
        return {
            'name': self.name, 'hero_class': self.hero_class, 
            'attributes': self.attributes, 
            'hp': self.hp, 'max_hp': self.max_hp, 
            'mana': self.mana, 'max_mana': self.max_mana, 
            'gold': self.gold, 'exp': self.exp,
            'level': self.level, 'skills': self.skills, 
            'attribute_points': self.attribute_points, 
            'is_shadow_stepping': self.is_shadow_stepping, # Dodanie flagi
            'status_effects': {k: v.to_dict() for k, v in self.status_effects.items()},
            'inventory': [item.to_dict() for item in self.inventory],
            'equipped_weapon': self.equipped_weapon.to_dict() if self.equipped_weapon else None,
            'equipped_armor': self.equipped_armor.to_dict() if self.equipped_armor else None,
            'equipped_ring': self.equipped_ring.to_dict() if self.equipped_ring else None, 
            'equipped_amulet': self.equipped_amulet.to_dict() if self.equipped_amulet else None, 
            'current_quests': [q.to_dict() for q in self.current_quests]
        }
    

class Enemy:
    def __init__(self, name, hp, atk, gold, exp, AC, interface=None, is_boss=False, enemy_type="Goblin"):
        self.name = name; self.hp = hp; self.max_hp = hp; self.atk = atk; self.gold = gold
        self.exp = exp; self.AC = AC; self.status_effects = {}; self.interface = interface
        self.is_boss = is_boss; self.enemy_type = enemy_type
        
    def is_alive(self): return self.hp > 0
    def take_damage(self, dmg): self.hp = max(0, self.hp - dmg)
    def get_mod(self, stat_value): return (stat_value - 10) // 2
    
    def get_current_AC(self):
        ac = self.AC
        if "Defense Down" in self.status_effects:
             ac -= self.status_effects["Defense Down"].value
        return ac

    def attack(self, hero):
        
        # Sprawdzenie i przetwarzanie efektów statusu (np. Stun, Disarm blokuje atak)
        if "Stun" in self.status_effects:
             self.process_status_effects(self.interface); return 0 # Nie może atakować
             
        if "Disarmed" in self.status_effects:
             if random.random() < 0.5: # 50% szansy na zablokowanie ataku
                  self.process_status_effects(self.interface)
                  self.interface.add_to_log(f"[{self.name}] jest Rozbrojony i traci atak!")
                  return 0
        
        # Sprawdzenie i przetwarzanie Blinds
        if "Blinded" in self.status_effects:
             if random.random() < 0.5: # 50% szansy na pudło
                  self.process_status_effects(self.interface)
                  self.interface.add_to_log(f"[{self.name}] jest Oślepiony i **spudłował!**")
                  return 0


            
        hit_modifier = self.get_mod(self.atk)
        roll_result, final_roll, log_message = roll_d20(hit_modifier)
        if self.interface: self.interface.add_to_log(f"[{self.name}] {log_message}")
        
        if final_roll < hero.defense or roll_result == "MISS": return 0
        
        # Obrażenia: 1k8 + modyfikator ataku
        dmg = random.randint(1, 8) + self.get_mod(self.atk)
        if roll_result == "CRIT": dmg *= 2
        
        # Specjalne ataki wrogów (zaktualizowane o zimowe)
        if self.enemy_type == "Shadow Wolf" and random.random() > 0.6:
            dmg *= 1.2
            hero.apply_status(StatusEffect("Stun", duration=1))
            if self.interface: self.interface.add_to_log(f"{self.name} **Ogłuszył** bohatera!")
        elif self.enemy_type == "Snow Wolf": # Uproszczony status dla Snow Wolf
            if random.random() > 0.5:
                # Bohaterowie teraz ignorują 'Frozen' - tylko komunikat
                if self.interface: self.interface.add_to_log(f"{self.name} **Spowalnia** bohatera zimnym atakiem!")
                
        elif self.enemy_type == "Frost Giant" and random.random() > 0.6:
            dmg *= 1.5
            if self.interface: self.interface.add_to_log(f"{self.name} **Mrozi** bohatera!")
        
        elif self.enemy_type == "Yeti" and random.random() > 0.5:
             # Atak wzmacniany zimnem - większe bazowe obrażenia
            dmg += 5
            if self.interface: self.interface.add_to_log(f"{self.name} uderza z furią lodu!")
            
        final_dmg = max(1, int(dmg))
        hero.take_damage(final_dmg)
        
        # Przetwarzanie statusów wroga po ataku
        self.process_status_effects(self)
        
        return final_dmg
        
    def apply_status(self, effect):
        if effect.name not in self.status_effects or effect.turns_left > self.status_effects[effect.name].turns_left:
             self.status_effects[effect.name] = effect
             if self.interface: self.interface.add_to_log(f"{self.name} został dotknięty statusem **{effect.name}**!")
    
    def process_status_effects(self, interface):
        active_effects = list(self.status_effects.keys())
        for name in active_effects:
            effect = self.status_effects[name]
            effect.apply_effect(self, interface)
            if effect.turns_left <= 0:
                del self.status_effects[name]
                interface.add_to_log(f"Status **{name}** minął na {self.name}.")
                
    def to_dict(self):
        return {
            'name': self.name, 'hp': self.hp, 'max_hp': self.max_hp, 'atk': self.atk, 
            'gold': self.gold, 'exp': self.exp, 'AC': self.AC, 'is_boss': self.is_boss,
            'enemy_type': self.enemy_type,
            'status_effects': {k: v.to_dict() for k, v in self.status_effects.items()},
        }
        
    @staticmethod
    def from_dict(data, interface):
        e = Enemy(data['name'], data['max_hp'], data['atk'], data['gold'], data['exp'], data['AC'], 
                  interface=interface, is_boss=data['is_boss'], enemy_type=data['enemy_type'])
        e.hp = data['hp']
        e.status_effects = {k: StatusEffect.from_dict(v) for k, v in data['status_effects'].items()}
        return e


# ====================================================================
# --- 3. KLASA INTERFEJSU GRY I LOGIKI STEROWANIA (PYGAME) ---
# ====================================================================

class GameInterface:
    def __init__(self, hero, world):
        self.hero = hero
        self.world = world
        self.log = []
        self.input_text = ""
        self.game_state = "EXPLORATION" # EXPLORATION, COMBAT, TOWN, STAT_ALLOCATION, START_MENU, WIN
        self.current_enemies = []
        self.selected_skill = None
        
        hero.interface = self # Ustawienie referencji zwrotnej
        
        # --- FIX: Inicjalizacja QuestBoard ---
        self.quest_board = QuestBoard() 
        # --- END FIX ---
        
        self.add_to_log(f"Witaj, {hero.name} ({hero.hero_class})! Wpisz 'help' aby zobaczyć komendy.")
        self.add_to_log(f"Jesteś na pozycji: {world.hero_position}. Czekają Cię przygody w świecie **{world.theme_name.upper()}**!")

    def add_to_log(self, message):
        # Rozbicie długich wiadomości na krótsze linie dla lepszego wyświetlania
        MAX_LINE_LENGTH = 80
        parts = message.split()
        current_line = ""
        
        for part in parts:
            if len(current_line) + len(part) + 1 > MAX_LINE_LENGTH:
                self.log.append(current_line)
                current_line = part
            else:
                current_line = (current_line + " " + part).strip()
        
        if current_line: self.log.append(current_line)
        if len(self.log) > LOG_LINES: self.log = self.log[-LOG_LINES:]
        
    def set_game_state(self, new_state):
        self.game_state = new_state
        if new_state == "COMBAT":
            self.add_to_log("\n*** ROZPOCZĘTO WALKĘ! ***")
            # Logika wyświetlania opcji jest teraz w 'draw_combat_info'
        elif new_state == "TOWN":
            self.add_to_log("\n*** WEJŚCIE DO MIASTA ***")
            self.add_to_log("Dostępne komendy: 'shop', 'board', 'rest', 'exit' (lub klawisz P dla sklepu).")
        elif new_state == "STAT_ALLOCATION":
            self.add_to_log(f"\nMasz {self.hero.attribute_points} punktów do przydzielenia. Komenda: 'allocate STR/DEX/etc.'")
        # --- Usprawnienie: Wyświetl listę od razu po wejściu do trybu ---
        elif new_state == "TOWN_SHOP":
            self.add_to_log("\n*** SKLEP ***")
            self.quest_board.shop_instance.display_items(self.hero, self)
        elif new_state == "TOWN_BOARD":
             self.add_to_log("\n*** TABLICA OGŁOSZEŃ ***")
             self.quest_board.display_board(self.hero, self)
        # --- Koniec Usprawnienia ---
            
    def start_combat(self, enemies):
        if self.game_state != "COMBAT":
            self.current_enemies = enemies
            self.set_game_state("COMBAT")
            
    def end_combat(self):
        self.add_to_log("\n*** KONIEC WALK! ***")
        
        quests_to_remove = [] 
        for enemy in self.current_enemies:
            if not enemy.is_alive():
                self.hero.gain(enemy.gold, enemy.exp)
                self.add_to_log(f"Zwycięstwo! Zdobyto {enemy.gold} złota i {enemy.exp} EXP.")
                
                # Aktualizacja zadań
                for q in self.hero.current_quests:
                    if q.type == "defeat_enemies":
                        q.update_progress(interface=self)
                    elif q.type == "defeat_enemies_type" and q.target == enemy.enemy_type:
                         q.update_progress(interface=self)
                    elif q.type == "defeat_boss" and enemy.is_boss:
                        q.update_progress(interface=self)
                        
        # Sprawdzenie warunku głównego zadania (po wszystkich walkach)
        for q in list(self.hero.current_quests):
            if q.completed:
                result = q.give_reward(self.hero, self)
                if result == "WIN": 
                    self.set_game_state("WIN") 
                    return
                if result: 
                    # Zadanie odebrane w end_combat (nie powinno się tak dziać, ale zabezpieczamy)
                    if q in self.hero.current_quests:
                         self.hero.current_quests.remove(q)
                        
        self.current_enemies = []
        self.set_game_state("EXPLORATION")
        
    def is_valid_command(self, command):
        if self.game_state == "EXPLORATION":
            return command in ["north", "south", "east", "west", "help", "stats", "inventory", "save", "load", "map", "exit"]
        elif self.game_state == "COMBAT":
            return command in ["attack", "skill", "flee", "skills", "stats"]
        elif self.game_state == "TOWN":
            return command in ["shop", "board", "rest", "exit"]
        elif self.game_state == "STAT_ALLOCATION":
            return command in ["allocate", "stats", "done"]
        return False

    # --- Metody rysowania Pygame ---

    def draw_text(self, surface, text, pos, color=WHITE, align_right=False):
        lines = text.split('\n')
        for i, line in enumerate(lines):
            # Uproszczenie: Usuwanie tagów formatowania przed renderowaniem
            line_cleaned = line.replace("**", "").replace("`", "")
            
            text_surface = FONT.render(line_cleaned, True, color)
            rect = text_surface.get_rect()
            
            x = pos[0]
            if align_right:
                x = pos[0] - rect.width
                
            rect.topleft = (x, pos[1] + i * (FONT_SIZE + 4))
            surface.blit(text_surface, rect)

    def draw_bar(self, surface, pos, current_val, max_val, color, width=200, height=20, text_color=BLACK):
        ratio = current_val / max_val if max_val > 0 else 0
        fill_width = int(width * ratio)
        
        # Tło
        pygame.draw.rect(surface, DARK_GREY, (*pos, width, height))
        # Wypełnienie
        pygame.draw.rect(surface, color, (*pos, fill_width, height))
        # Ramka
        pygame.draw.rect(surface, WHITE, (*pos, width, height), 1)
        
        # Tekst na pasku
        text = f"{int(current_val)}/{int(max_val)}"
        text_surface = FONT.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=(pos[0] + width // 2, pos[1] + height // 2))
        surface.blit(text_surface, text_rect)
        
    def draw_combat_info(self, start_y): # ZMIANA: Przyjmuje start_y
        offset_x = 20
        offset_y = start_y # Użycie start_y
        
        COMBAT_HERO_SIZE = 96 
        COMBAT_ENEMY_SIZE = 64
        
        # Rysowanie bohatera
        hero_x = SCREEN_WIDTH // 2 - 100
        # Pozycja Y bohatera jest teraz względna do start_y i dołu ekranu
        hero_y = start_y + (SCREEN_HEIGHT - 45 - start_y) * 0.6 - COMBAT_HERO_SIZE
        
        if GRAPHICS_LOADED and HERO_SPRITE_ORIGINAL:
            scaled_hero_sprite = pygame.transform.scale(HERO_SPRITE_ORIGINAL, (COMBAT_HERO_SIZE, COMBAT_HERO_SIZE))
            SCREEN.blit(scaled_hero_sprite, (hero_x, hero_y))
        else:
            pygame.draw.rect(SCREEN, HERO_COLOR, (hero_x, hero_y, COMBAT_HERO_SIZE, COMBAT_HERO_SIZE))
        
        self.draw_text(SCREEN, f"{self.hero.name}", (hero_x + COMBAT_HERO_SIZE // 2, hero_y - 30), WHITE, align_right=True)
        self.draw_text(SCREEN, f"AC: {self.hero.defense}", (hero_x - 40, hero_y), WHITE)
        
        # Pasek HP i MP
        self.draw_bar(SCREEN, (hero_x - 100, hero_y + COMBAT_HERO_SIZE + 10), self.hero.hp, self.hero.max_hp, GREEN, width=200, height=20)
        self.draw_text(SCREEN, "HP", (hero_x - 120, hero_y + COMBAT_HERO_SIZE + 10), WHITE)
        self.draw_bar(SCREEN, (hero_x - 100, hero_y + COMBAT_HERO_SIZE + 35), self.hero.mana, self.hero.max_mana, BLUE, width=200, height=20)
        self.draw_text(SCREEN, "MP", (hero_x - 120, hero_y + COMBAT_HERO_SIZE + 35), WHITE)
        
        # Aktywne statusy bohatera
        hero_status_text = ""
        for name, effect in self.hero.status_effects.items():
            if name not in ["Defense Down", "Rage", "Teleporting"]: 
                 hero_status_text += f"**{name}** ({effect.turns_left}) "
        if hero_status_text:
             self.draw_text(SCREEN, f"Statusy: {hero_status_text}", (hero_x - 100, hero_y + COMBAT_HERO_SIZE + 60), LIGHT_GREY)


        # Rysowanie wrogów
        alive_enemies = [e for e in self.current_enemies if e.is_alive()]
        
        for i, enemy in enumerate(alive_enemies):
            enemy_x = offset_x + i * 200
            enemy_y = offset_y + 20 # Przesunięcie w dół od start_y
            
            if GRAPHICS_LOADED and ENEMY_SPRITE_ORIGINAL:
                scaled_enemy_sprite = pygame.transform.scale(ENEMY_SPRITE_ORIGINAL, (COMBAT_ENEMY_SIZE, COMBAT_ENEMY_SIZE))
                SCREEN.blit(scaled_enemy_sprite, (enemy_x, enemy_y))
            else:
                pygame.draw.rect(SCREEN, ENEMY_COLOR, (enemy_x, enemy_y, COMBAT_ENEMY_SIZE, COMBAT_ENEMY_SIZE))
            
            # HP BAR
            self.draw_bar(SCREEN, (enemy_x, enemy_y + COMBAT_ENEMY_SIZE + 10), enemy.hp, enemy.max_hp, RED, width=100, height=15)
            
            # Info
            info = f"[{i+1}] {enemy.name}\n"
            info += f"HP: {enemy.hp}/{enemy.max_hp}\n"
            info += f"AC: {enemy.get_current_AC()}\n"
            
            # Statusy
            enemy_status_text = ""
            for name, effect in enemy.status_effects.items():
                enemy_status_text += f"**{name}** ({effect.turns_left}) "
                
            info += enemy_status_text
                
            self.draw_text(SCREEN, info, (enemy_x + COMBAT_ENEMY_SIZE + 10, enemy_y), WHITE)
            
        # --- LISTA DOSTĘPNYCH AKCJI W WALCE (zaktualizowana) ---
        cost_map = {"Heavy Blow": 15, "Block": 10, "Shatter Defense": 20, "Taunt": 10, "Vampiric Strike": 25, "Shield Bash": 20, "Rage": 30, 
                    "Fireball": 20, "Heal": 25, "Arcane Missile": 15, "Ice Shard": 15, "Mana Shield": 20, "Magic Storm": 40, "Teleport": 30, 
                    "Sneak Attack": 20, "Poison Edge": 15, "Disarm": 15, "Vanish": 20, "Blind": 25, "Shadow Step": 35, "Execute": 40}
        
        actions_text = "*** TWOJE AKCJE ***\n"
        actions_text += f"**Atak Podstawowy**\n  Komenda: `attack [nr]`\n"
        actions_text += "------------------------\n"
        actions_text += f"**Umiejętności** (MP: {self.hero.mana}/{self.hero.max_mana}):\n"
        
        for skill in self.hero.skills:
             cost = cost_map.get(skill, 0)
             if skill in ["Heal", "Block", "Mana Shield", "Vanish", "Rage", "Shadow Step", "Teleport"]:
                 target_info = ""
             elif skill == "Magic Storm":
                 target_info = " [nr1,nr2,...]"
             else:
                 target_info = " [nr]"
             
             actions_text += f"- **{skill}** ({cost} MP)\n  Komenda: `skill {skill.lower().replace(' ', '_')} {target_info}`\n" 
             
        actions_text += "------------------------\n"
        actions_text += "Użyj **flee** aby spróbować uciec."
        
        # Pozycja rysowania akcji
        actions_x = SCREEN_WIDTH // 2 + 120
        actions_y = start_y + 20 # Przesunięcie w dół od start_y
        self.draw_text(SCREEN, actions_text, (actions_x, actions_y), WHITE)
            

    def draw_map(self, start_y): # ZMIANA: Przyjmuje start_y
        # Obliczenie rozmiaru mapy, aby zmieściła się w pozostałym miejscu
        MAP_HEIGHT = (SCREEN_HEIGHT - 45) - start_y - 10 # Wysokość od start_y do paska input
        MAP_WIDTH = SCREEN_WIDTH - 20
        
        CELL_SIZE_H = MAP_HEIGHT // self.world.size
        CELL_SIZE_W = MAP_WIDTH // self.world.size
        CELL_SIZE = min(CELL_SIZE_H, CELL_SIZE_W, 40) # Ograniczenie max rozmiaru
        
        MAP_DRAW_SIZE_X = CELL_SIZE * self.world.size
        MAP_DRAW_SIZE_Y = CELL_SIZE * self.world.size
        
        MAP_START_X = (SCREEN_WIDTH - MAP_DRAW_SIZE_X) // 2
        MAP_START_Y = start_y + (MAP_HEIGHT - MAP_DRAW_SIZE_Y) // 2 # Centrowanie pionowe
        
        
        for x in range(self.world.size):
            for y in range(self.world.size):
                rect = pygame.Rect(MAP_START_X + y * CELL_SIZE, MAP_START_Y + x * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                
                cell_type = self.world.map[x][y]
                # Użyj koloru z aktualnego tematu
                cell_color = self.world.theme_data.get(cell_type, DEFAULT_THEME.get("empty"))["color"]
                
                pygame.draw.rect(SCREEN, cell_color, rect)
                pygame.draw.rect(SCREEN, WHITE, rect, 1) # Ramka
                
                # Rysowanie bohatera
                if (x, y) == self.world.hero_position:
                    if GRAPHICS_LOADED and HERO_SPRITE_ORIGINAL:
                        # Skalowanie oryginału do rozmiaru komórki mapy
                        hero_sprite_scaled = pygame.transform.scale(HERO_SPRITE_ORIGINAL, (CELL_SIZE - 5, CELL_SIZE - 5))
                        SCREEN.blit(hero_sprite_scaled, (rect.x + (CELL_SIZE - hero_sprite_scaled.get_width()) // 2, rect.y + (CELL_SIZE - hero_sprite_scaled.get_height()) // 2))
                    else:
                        hero_rect = pygame.Rect(rect.centerx - CELL_SIZE // 4, rect.centery - CELL_SIZE // 4, CELL_SIZE // 2, CELL_SIZE // 2)
                        pygame.draw.rect(SCREEN, HERO_COLOR, hero_rect)


        # Rysowanie legendy
        legend_start_y = MAP_START_Y + MAP_DRAW_SIZE_Y + 10
        self.draw_text(SCREEN, f"Legenda (Motyw: {self.world.theme_name.upper()}):", (MAP_START_X, legend_start_y))
        
        for i, (key, data) in enumerate(self.world.theme_data.items()):
            if key in ["probabilities", "enemies"]: continue
            color = data["color"]
            name = data["name"]
            
            legend_x = MAP_START_X + (i % 3) * (MAP_DRAW_SIZE_X // 3)
            legend_y = legend_start_y + 30 + (i // 3) * 20
            
            if legend_y < (SCREEN_HEIGHT - 50): # Upewnij się, że legenda nie nachodzi na input
                pygame.draw.circle(SCREEN, color, (legend_x + 5, legend_y + 8), 6)
                self.draw_text(SCREEN, f"- {name}", (legend_x + 15, legend_y))


    def draw_stats(self, start_y): # ZMIANA: Przyjmuje start_y
        stats_text = f"*** STATYSTYKI BOHATERA ({self.hero.name}, Lvl {self.hero.level}) ***\n"
        stats_text += f"Klasa: {self.hero.hero_class}\n"
        stats_text += f"HP: {self.hero.hp}/{self.hero.max_hp} | Mana: {self.hero.mana}/{self.hero.max_mana}\n"
        stats_text += f"Złoto: {self.hero.gold} | EXP: {self.hero.exp}/{100 * self.hero.level}\n"
        stats_text += f"ATK (Modyfikator): {self.hero.atk} | AC (Obrona): {self.hero.defense}\n"
        stats_text += f"Punkty atrybutów: {self.hero.attribute_points}\n"
        stats_text += "---------------------------------------\n"
        
        # Wyświetlanie atrybutów
        for attr, value in self.hero.attributes.items():
            mod = self.hero.get_mod(attr)
            stats_text += f"**{attr}** (Mod: {mod:+}): {value}\n"
        
        stats_text += "---------------------------------------\n"
        
        # Wyświetlanie aktywnego buffa Rage
        if "Rage" in self.hero.status_effects:
             stats_text += f"**Aktywny Buff**: Furia (+2 STR, {self.hero.status_effects['Rage'].turns_left} tury)\n"
        
        # Wyświetlanie ekwipunku
        stats_text += "\n*** EKWIPUNEK ***\n"
        stats_text += f"Broń (Weapon): {self.hero.equipped_weapon.name if self.hero.equipped_weapon else 'Brak'}\n"
        stats_text += f"Zbroja (Armor): {self.hero.equipped_armor.name if self.hero.equipped_armor else 'Brak'}\n"
        stats_text += f"Pierścień (Ring): {self.hero.equipped_ring.name if self.hero.equipped_ring else 'Brak'}\n"
        stats_text += f"Amulet (Amulet): {self.hero.equipped_amulet.name if self.hero.equipped_amulet else 'Brak'}\n"
        
        # Wyświetlanie aktywnego zadania (jeśli jest)
        if self.hero.current_quests:
             stats_text += "\n*** AKTYWNE ZADANIA ***\n"
             for q in self.hero.current_quests:
                 status = "✅ Ukończone!" if q.completed else f"W toku: {q.progress}/{q.target}"
                 stats_text += f"- **{q.name}**: {status}\n"
        
        self.draw_text(SCREEN, stats_text, (20, start_y), WHITE)


    def draw_inventory(self, start_y): # ZMIANA: Przyjmuje start_y
        inventory_text = f"*** INWENTARZ (Złoto: {self.hero.gold}) ***\n"
        inventory_text += "Wpisz 'use [numer]' (mikstury) lub 'equip [numer]' (sprzęt).\n"
        
        for i, item in enumerate(self.hero.inventory):
            equip_info = f" [Wyposażalny, Slot: {item.slot}]" if item.equipable else ""
            inventory_text += f"[{i+1}] **{item.name}** ({item.type}, {item.value} złota): {item.description} {equip_info}\n"
            
        self.draw_text(SCREEN, inventory_text, (20, start_y), WHITE)

    
    def draw(self):
        SCREEN.fill(DARK_GREY)

        # 1. Rysowanie Paska Statystyk (GÓRA)
        stats_text = f"HP: {self.hero.hp}/{self.hero.max_hp} | MANA: {self.hero.mana}/{self.hero.max_mana} | ATK: {int(self.hero.atk)} | AC: {self.hero.defense} | GOLD: {self.hero.gold} | LVL: {self.hero.level} | MAPA: {self.world.theme_name.upper()}"
        stats_surface = FONT.render(stats_text, True, WHITE)
        SCREEN.blit(stats_surface, (10, 10))

        # 2. Rysowanie Loga (NOWA POZYCJA: POD PASKIEM STATYSTYK)
        log_start_y = 40 
        log_height = (LOG_LINES * (FONT_SIZE + 2)) + 10 # 10 linii * 18px + 10 padding = 190px
        pygame.draw.rect(SCREEN, (10, 10, 10), (10, log_start_y, SCREEN_WIDTH - 20, log_height))
        
        for i, line in enumerate(self.log[-LOG_LINES:]):
             color = LIGHT_GREY
             if "ZWYCIĘSTWO" in line: color = GREEN
             elif "PORAŻKA" in line or "BŁĄD" in line: color = RED
             elif "BOSS" in line: color = RED
             elif "Poison" in line: color = POISON_COLOR
             elif "Stun" in line: color = STUN_COLOR
             elif "Frozen" in line: color = SNOW_COLOR 
             elif "Zapisana" in line or "Wczytana" in line or "Motyw" in line or "UWAGA" in line: color = HERO_COLOR
             
             display_line = line.replace('**', '').replace('`', '')
             
             text_surface = FONT.render(display_line, True, color)
             SCREEN.blit(text_surface, (15, log_start_y + 5 + (i * (FONT_SIZE + 2))))
            
        # 3. Rysowanie Głównej Sekcji (NOWA POZYCJA: POD LOGIEM)
        MAIN_SECTION_Y_START = log_start_y + log_height + 10 # Np. 40 + 190 + 10 = 240
        
        # Wyświetlanie stanu gry
        if self.game_state == "START_MENU":
            self.draw_start_menu() # Ten jest pełnoekranowy
        elif self.game_state == "WIN":
            self.draw_win_screen() # Ten jest pełnoekranowy
        elif self.game_state == "COMBAT":
            self.draw_combat_info(MAIN_SECTION_Y_START) 
        elif self.game_state == "EXPLORATION" or self.game_state == "TOWN" or self.game_state == "TOWN_SHOP" or self.game_state == "TOWN_BOARD":
            self.draw_map(MAIN_SECTION_Y_START) 
        elif self.game_state in ["STATS", "STAT_ALLOCATION"]:
            self.draw_stats(MAIN_SECTION_Y_START) 
        elif self.game_state == "INVENTORY":
            self.draw_inventory(MAIN_SECTION_Y_START) 
            
        # UWAGA: Wyświetlanie listy sklepu/zadań odbywa się poprzez logi w set_game_state/handle_command, 
        # a nie w pętli draw, aby uniknąć spamowania logu.

        # 4. Rysowanie Paska Wprowadzania (DÓŁ)
        input_rect = pygame.Rect(10, SCREEN_HEIGHT - 45, SCREEN_WIDTH - 20, 35)
        pygame.draw.rect(SCREEN, WHITE, input_rect)
        
        input_surface = INPUT_FONT.render("> " + self.input_text, True, BLACK)
        SCREEN.blit(input_surface, (input_rect.x + 5, input_rect.y + 5))
        
        
        # 5. Overlays (STAT_ALLOCATION, GAME_OVER)
        if self.game_state == "STAT_ALLOCATION":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            SCREEN.blit(overlay, (0, 0))
            
            self.draw_stat_allocation_overlay(SCREEN, FONT, WHITE, self.hero)

        if self.game_state == "GAME_OVER":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200)) 
            SCREEN.blit(overlay, (0, 0))
            
            go_text = FONT.render("KONIEC GRY", True, RED)
            go_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            SCREEN.blit(go_text, go_rect)
            
            exit_text = FONT.render("Wpisz 'exit' w konsoli i zatwierdź [Enter]", True, WHITE)
            exit_rect = exit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
            SCREEN.blit(exit_text, exit_rect)
            
        pygame.display.flip()

    # Rysowanie nakładki alokacji statystyk
    def draw_stat_allocation_overlay(self, surface, font, color, hero):
        title = font.render("PRZYDZIEL PUNKTY ATRYBUTÓW", True, HERO_COLOR)
        surface.blit(title, (50, 50))
        
        points_left = font.render(f"PUNKTY DO PRZYDZIELENIA: {hero.attribute_points}", True, color)
        surface.blit(points_left, (50, 80))
        
        y_pos = 120
        for stat, value in hero.attributes.items():
            mod = hero.get_mod(stat)
            text = font.render(f"{stat}: {value} (Mod: {mod})", True, color)
            surface.blit(text, (50, y_pos))
            y_pos += FONT_SIZE + 5
            
        help_text = font.render("Użyj komendy: allocate [nazwa_atrybutu]", True, color)
        surface.blit(help_text, (50, y_pos + 10))
        
        if hero.attribute_points == 0:
            exit_text = font.render("Wpisz 'exit' aby kontynuować grę.", True, GREEN)
            surface.blit(exit_text, (50, y_pos + 40))
            

    def handle_command(self, full_command):
        full_command = full_command.strip().lower()
        if not full_command: return
        
        self.add_to_log(f"-> {full_command}")

        parts = full_command.split()
        command = parts[0]
        args = parts[1:]
        
        if command == "help":
            self._display_help()
            return
            
        if command == "stats":
            self.set_game_state("STATS")
            return
            
        if command == "inventory":
            self.display_inventory()
            self.set_game_state("INVENTORY")
            return
            
        if command == "map":
             self.set_game_state("EXPLORATION")
             return

        if command == "save":
            save_game(self.hero, self.world, self)
            return

        if command == "load":
            loaded_hero, loaded_world, loaded_log = load_game(self)
            if loaded_hero:
                 # UWAGA: QuestBoard jest inicjalizowany w __init__ GameInterface, 
                 # więc nie musi być ładowany z pliku, o ile jego stan dynamiczny jest w hero.current_quests.
                 self.hero = loaded_hero
                 self.world = loaded_world
                 self.log = loaded_log
                 self.hero.interface = self
                 self.set_game_state("EXPLORATION")
            return

        # Akcje wspólne: "exit"
        if command == "exit":
            if self.game_state == "TOWN_SHOP" or self.game_state == "TOWN_BOARD":
                self.set_game_state("TOWN")
                return
            elif self.game_state == "TOWN":
                 self.set_game_state("EXPLORATION")
                 return
            elif self.game_state in ["STATS", "INVENTORY", "STAT_ALLOCATION"]:
                 # Specjalna obsługa w STAT_ALLOCATION
                 if self.game_state == "STAT_ALLOCATION" and self.hero.attribute_points > 0:
                      self.add_to_log("Musisz zakończyć przydzielanie punktów (komenda 'done') lub przydzielić pozostałe punkty.")
                      return
                 self.set_game_state("EXPLORATION")
                 return
            
        # Akcje w zależności od stanu gry
        
        if self.game_state == "EXPLORATION":
            if command in ["north", "south", "east", "west"]:
                self.world.move_hero(command, self.hero, self)
            elif self.world.get_current_location() == "town":
                 self.set_game_state("TOWN")
        
        elif self.game_state == "TOWN":
            if command == "shop":
                self.set_game_state("TOWN_SHOP")
            elif command == "board":
                self.set_game_state("TOWN_BOARD")
            elif command == "rest":
                self.hero.rest()

        elif self.game_state == "TOWN_SHOP":
            shop = self.quest_board.shop_instance
            if command == "buy" and args:
                try:
                    index = int(args[0]) - 1
                    if shop.buy_item(self.hero, index, self):
                         shop.display_items(self.hero, self) # Odświeżenie listy po zakupie
                except (ValueError, IndexError): self.add_to_log("Nieprawidłowy numer przedmiotu.")
                
        elif self.game_state == "TOWN_BOARD":
            board = self.quest_board
            if command == "accept" and args:
                try:
                    index = int(args[0]) - 1
                    if board.accept_quest(self.hero, index, self):
                        board.display_board(self.hero, self) # Odświeżenie listy po zaakceptowaniu
                except (ValueError, IndexError): self.add_to_log("Nieprawidłowy numer zadania.")
            elif command == "claim" and args:
                quest_name = " ".join(args).replace("'", "").strip()
                self._claim_quest(quest_name)
                board.display_board(self.hero, self) # Odświeżenie listy po odebraniu nagrody
                
        elif self.game_state == "INVENTORY":
             self._handle_inventory_command(command, args)
             
        elif self.game_state == "STAT_ALLOCATION":
             if command == "allocate" and args:
                 self.hero.assign_attribute_point(args[0])
             elif command == "done":
                 if self.hero.attribute_points == 0:
                     self.set_game_state("EXPLORATION")
                     self.add_to_log("Przydzielanie atrybutów zakończone.")
                 else:
                     self.add_to_log(f"Musisz przydzielić pozostałe {self.hero.attribute_points} punkty. Użyj 'allocate' lub kontynuuj przy następnym awansie.")
             
        elif self.game_state == "COMBAT":
            self._handle_combat_command(command, args)
            

    # --- Metody pomocnicze ---
    
    def _display_help(self):
        if self.game_state == "START_MENU":
             self.add_to_log("Komendy: **new [imie] [klasa] [motyw]**, **load**.")
        elif self.game_state == "EXPLORATION":
            self.add_to_log("Komendy: **WASD** (ruch), **P** (sklep w mieście), **stats**, **inventory**, **map**, **save**, **load**, **exit**.")
        elif self.game_state == "TOWN":
            self.add_to_log("Komendy: **shop**, **board**, **rest**, **exit**.")
        elif self.game_state == "TOWN_SHOP":
             self.add_to_log("Komendy: **buy [numer]**, **exit**.")
        elif self.game_state == "TOWN_BOARD":
             self.add_to_log("Komendy: **accept [numer]**, **claim [nazwa zadania]**, **exit**.")
        elif self.game_state == "COMBAT":
             self.add_to_log("Komendy: **attack [nr_wroga]**, **skill [nazwa] [nr_wroga/lista]**, **flee**, **stats**, **skills**.")
        elif self.game_state == "STAT_ALLOCATION":
             self.add_to_log("Komendy: **allocate STR/DEX/etc.**, **stats**, **done**.")
             
    def _handle_inventory_command(self, command, args):
        if command in ["use", "equip"] and args:
            try:
                index = int(args[0]) - 1
                if 0 <= index < len(self.hero.inventory):
                    item = self.hero.inventory[index]
                    if command == "use" and item.type == "potion":
                        self._use_potion(item)
                    elif command == "equip" and item.equipable:
                        self.hero.equip_item(item)
                        # self.display_inventory() # Odświeżenie (już w logu)
                    else:
                        self.add_to_log(f"Nie możesz użyć/wyposażyć {item.name}.")
                else: self.add_to_log("Błędny numer przedmiotu.")
            except (ValueError, IndexError): self.add_to_log("Nieprawidłowy numer.")
        elif command == "exit":
             self.set_game_state("EXPLORATION")

    def _use_potion(self, item):
        self.hero.inventory.remove(item)
        
        if 'heal' in item.stats:
            heal = item.stats['heal']
            self.hero.hp = min(self.hero.hp + heal, self.hero.max_hp)
            self.add_to_log(f"Użyto {item.name}: przywrócono {heal} HP.")
        
        if 'mana' in item.stats:
            mana_regen = item.stats['mana']
            self.hero.mana = min(self.hero.mana + mana_regen, self.hero.max_mana)
            self.add_to_log(f"Użyto {item.name}: przywrócono {mana_regen} Many.")
        self.draw_inventory(MAIN_SECTION_Y_START) # Odświeżenie

    def _claim_quest(self, quest_name):
         for q in list(self.hero.current_quests): # Używamy kopii do iteracji
             if q.name.lower() == quest_name.lower():
                 if q.completed:
                     result = q.give_reward(self.hero, self)
                     if result == "WIN":
                         self.set_game_state("WIN")
                     else:
                         if q in self.hero.current_quests:
                            self.hero.current_quests.remove(q)
                     return
                 else:
                     self.add_to_log(f"Zadanie '{q.name}' nie jest jeszcze ukończone: {q.progress}/{q.target}.")
                     return
         self.add_to_log(f"Nie znaleziono aktywnego zadania o nazwie '{quest_name}'.")

    
    def _handle_combat_command(self, command, args):
        
        if command == "skills":
            self.add_to_log(f"Dostępne umiejętności ({self.hero.mana}/{self.hero.max_mana} MP): {', '.join(self.hero.skills)}")
            return
            
        if command == "flee":
            self.add_to_log("Próbujesz uciec!")
            flee_chance = 0.5
            if "VANISH" in self.hero.status_effects:
                 flee_chance += 0.3
                 del self.hero.status_effects["VANISH"]
                 
            if random.random() < flee_chance:
                self.add_to_log("Udało się uciec!")
                self.end_combat()
                return
            else:
                self.add_to_log("Ucieczka nie powiodła się. Czas na turę wroga!")
                self._enemy_turn()
                return
        
        # --- Przygotowanie celu i umiejętności ---
        
        alive_enemies = [e for e in self.current_enemies if e.is_alive()]
        if not alive_enemies and command not in ["skills", "flee", "stats"]: self.end_combat(); return
        
        # Weryfikacja i parsowanie celu
        target_index = None
        target_indices = []
        skill_name = None
        
        if command == "attack" and args and args[-1].isdigit():
             try: target_index = int(args[-1]) - 1
             except ValueError: pass
        elif command == "skill":
            if not args:
                 self.add_to_log("Użycie: skill [nazwa_umiejętności] [numer_wroga] lub skill [nazwa_umiejętności] (dla umiejętności własnych)")
                 return
                 
            skill_parts = []
            target_parts = []
            
            # Oddzielanie nazwy umiejętności od celów (np. "magic storm 1,2,3" lub "magic_storm 1 2 3")
            target_start_index = len(args)
            for i, arg in enumerate(args):
                 if any(c.isdigit() for c in arg):
                      target_start_index = i
                      break
            
            skill_parts = args[:target_start_index]
            target_parts = args[target_start_index:]
            
            # Parsowanie celów (obsługuje 1,2,3 lub 1 2 3)
            for part in target_parts:
                 for num in part.split(','):
                     if num.isdigit():
                         target_indices.append(int(num) - 1)
            
            # Konwersja komendy na nazwę umiejętności (np. "shatter defense" -> "Shatter Defense")
            skill_name = "_".join(skill_parts).title().replace('_', ' ')
            
            # --- Weryfikacja celów ---
            
            # Umiejętności wspierające (bez celu)
            if skill_name in ["Heal", "Block", "Mana Shield", "Vanish", "Rage", "Teleport", "Shadow Step"]:
                 if target_indices:
                     self.add_to_log(f"Umiejętność {skill_name} nie wymaga celu.")
                     return
                 target_enemy = None
                 
            # Umiejętności obszarowe (Magic Storm)
            elif skill_name == "Magic Storm":
                 if not target_indices:
                     self.add_to_log(f"Umiejętność {skill_name} wymaga listy celów: skill magic_storm 1 2.")
                     return
                 # Weryfikacja, czy wszystkie cele są poprawne
                 for index in target_indices:
                     if not (0 <= index < len(alive_enemies) and alive_enemies[index].is_alive()):
                          self.add_to_log(f"Nieprawidłowy lub nieżywy cel: {index + 1}.")
                          return
                 target_enemy = None # Atak na listę
                 
            # Umiejętności celujące (reszta)
            else:
                 if not target_indices or len(target_indices) != 1:
                      self.add_to_log(f"Umiejętność {skill_name} wymaga dokładnie jednego celu: skill {skill_name.lower().replace(' ', '_')} [nr].")
                      return
                 target_index = target_indices[0]
                 if not (0 <= target_index < len(alive_enemies) and alive_enemies[target_index].is_alive()):
                     self.add_to_log("Nieprawidłowy lub nieżywy cel.")
                     return
                 target_enemy = alive_enemies[target_index]
                 
            # Sprawdzenie czy umiejętność jest w ogóle znana
            if skill_name not in self.hero.skills:
                 self.add_to_log(f"Nieznana umiejętność: {skill_name}. Sprawdź pisownię w komendzie 'skills'.")
                 return
        
        # --- Tura bohatera ---
        damage_dealt = 0
        status_applied = None
        additional_effect = None

        if command == "attack":
            if target_index is None: 
                 self.add_to_log("Wybierz cel ataku: attack [numer wroga].")
                 return
            
            target_enemy = alive_enemies[target_index]
            self.selected_skill = ("attack", target_index + 1)
            damage_dealt = self.hero.attack_basic(target_enemy.get_current_AC())
            self.add_to_log(f"Atak podstawowy na {target_enemy.name}: Zadano {damage_dealt} obrażeń.")
            
        elif command == "skill":
            self.selected_skill = (skill_name, target_index + 1 if target_index is not None else 0)
            
            # Obsługa Magic Storm (lista celów)
            if skill_name == "Magic Storm":
                 # Przekazujemy listę obiektów wroga
                 targets = [alive_enemies[i] for i in target_indices]
                 damage_dealt, status_applied, additional_effect = self.hero.use_skill(skill_name, target_list=targets)
            else:
                 damage_dealt, status_applied, additional_effect = self.hero.use_skill(skill_name, target_enemy)
            
            if damage_dealt == -1: # Zdolność wspierająca (Heal, Block, Mana Shield, Taunt, Vanish, Rage, Teleport, Shadow Step)
                pass
            elif damage_dealt == -2: # Atak obszarowy
                 pass
            elif damage_dealt == 0:
                self.add_to_log(f"Umiejętność {skill_name}: **Pudło!**")
            else:
                self.add_to_log(f"Umiejętność **{skill_name}** na {target_enemy.name}: Zadano **{damage_dealt}** obrażeń.")
        else:
             self.add_to_log("Nieznana komenda w walce.")
             return
             
        # Obsługa obrażeń i statusów (tylko dla pojedynczego celu)
        if target_enemy and damage_dealt > 0:
            target_enemy.take_damage(damage_dealt)
            
            if additional_effect == "HEAL_DMG_PERCENT_50":
                 heal_amount = int(damage_dealt * 0.5)
                 self.hero.hp = min(self.hero.hp + heal_amount, self.hero.max_hp)
                 self.add_to_log(f"**Vampiric Strike**: Uleczono się za {heal_amount} HP.")
                 
        if target_enemy and status_applied:
            target_enemy.apply_status(status_applied)
            
        if target_enemy and target_enemy.hp <= 0:
            self.add_to_log(f"Pokonałeś {target_enemy.name}!")
        
        # --- Tura wroga ---
        if any(e.is_alive() for e in self.current_enemies):
            self._enemy_turn()
        else:
            self.end_combat()

    def _enemy_turn(self):
        self.hero.process_status_effects(self) # Efekty statusu na bohaterze
        
        if not self.hero.is_alive(): 
             self.add_to_log("\n*** BOHATER ZGINĄŁ! KONIEC GRY! ***")
             self.set_game_state("DEFEAT")
             return # Bohater zginął od statusu
        
        self.add_to_log("\n*** Tura Wroga ***")
        
        
        for i, enemy in enumerate(self.current_enemies):
            if enemy.is_alive():
                 
                 # Wrogowie również przetwarzają swoje efekty statusu PRZED atakiem
                 enemy.process_status_effects(self)
                 
                 if "Stun" in enemy.status_effects: continue # Ogłuszony, traci turę
                 
                 dmg = enemy.attack(self.hero)
                 if dmg > 0:
                     self.add_to_log(f"{enemy.name} atakuje! Bohater traci {dmg} HP. Pozostało: {self.hero.hp}.")
                     
                 if not self.hero.is_alive():
                     self.add_to_log("\n*** BOHATER ZGINĄŁ! KONIEC GRY! ***")
                     self.set_game_state("DEFEAT")
                     break # Przerwij pętlę wrogów
                     
        # Po turze wroga, jeśli był aktywny Teleport, to efekt mija
        if "Teleporting" in self.hero.status_effects:
             del self.hero.status_effects["Teleporting"]
             self.add_to_log("Status **Teleporting** minął.")


    def draw_start_menu(self):
        menu_text = "*** Advanced D&D Text RPG (Pygame Edition) ***\n"
        menu_text += "Wpisz **'new [imie] [klasa] [motyw]'** lub **'load'**, aby wczytać grę.\n"
        menu_text += "Dostępne klasy: Warrior, Mage, Rogue\n"
        menu_text += "Dostępne motywy: default, winter\n"
        menu_text += "Przykład: **new Arek warrior winter**"
        
        self.draw_text(SCREEN, menu_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 50), WHITE)

    def draw_win_screen(self):
        win_text = "\n\n\n\n*** GRATULACJE! OSIĄGNĄŁEŚ ZWYCIĘSTWO! ***\n"
        win_text += "Ukończyłeś główne zadanie i pokonałeś wroga. Twoja legenda trwa!\n"
        win_text += "Wpisz 'exit' by zakończyć grę."
        self.draw_text(SCREEN, win_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 50), (255, 255, 0))


# ====================================================================
# --- 4. FUNKCJE ZAPISU/ODCZYTU STANU GRY ---
# ====================================================================

SAVE_FILE = "rpg_save.json"

def save_game(hero, world, interface):
    data = {
        'hero': hero.to_dict(),
        'world': world.to_dict(),
        'log': interface.log,
        'game_state': interface.game_state
    }
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        interface.add_to_log(f"Gra zapisana pomyślnie do {SAVE_FILE}.")
    except Exception as e:
        interface.add_to_log(f"Błąd zapisu gry: {e}")

def load_game(interface):
    try:
        if not os.path.exists(SAVE_FILE):
             interface.add_to_log("Błąd ładowania: Plik zapisu nie istnieje.")
             return None, None, None
             
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
            
        
        # 1. Tworzenie Świata
        world_data = data['world']
        # Używamy rozmiaru i tematu z pliku zapisu
        new_world = World(size=world_data['size'], theme=world_data['theme_name'])
        new_world.map = world_data['map']
        new_world.hero_position = tuple(world_data['hero_position'])
        
        # 2. Tworzenie Bohatera
        hero_data = data['hero']
        # Tworzymy nowego bohatera, aby zainicjalizować bazowe statystyki i umiejętności
        # Następnie nadpisujemy stanem z pliku
        new_hero = Hero(hero_data['name'], hero_data['hero_class']) 
        
        # Przywracanie statystyk i ekwipunku
        new_hero.attributes = hero_data['attributes']
        new_hero.hp = hero_data['hp']; new_hero.max_hp = hero_data['max_hp']
        new_hero.mana = hero_data['mana']; new_hero.max_mana = hero_data['max_mana']
        new_hero.gold = hero_data['gold']; new_hero.exp = hero_data['exp']
        new_hero.level = hero_data['level']; new_hero.attribute_points = hero_data['attribute_points']
        new_hero.skills = hero_data['skills'] 
        
        new_hero.inventory = [create_item_from_dict(d) for d in hero_data['inventory']]
        
        # Ponowne wyposażenie 
        new_hero.equipped_weapon = create_item_from_dict(hero_data.get('equipped_weapon'))
        new_hero.equipped_armor = create_item_from_dict(hero_data.get('equipped_armor'))
        new_hero.equipped_ring = create_item_from_dict(hero_data.get('equipped_ring'))
        new_hero.equipped_amulet = create_item_from_dict(hero_data.get('equipped_amulet'))
        
        # Upewnienie się, że statystyki są przeliczone
        new_hero._update_derived_stats()
        
        new_hero.status_effects = {k: StatusEffect.from_dict(v) for k, v in hero_data['status_effects'].items()}
        new_hero.current_quests = [create_quest_from_dict(q) for q in hero_data['current_quests']]
        new_hero.is_shadow_stepping = hero_data.get('is_shadow_stepping', False)
        
        # Ponowne obliczenie statystyk pochodnych
        new_hero._update_derived_stats() 
        
        # 3. Przywracanie Logu
        new_log = data['log']
        
        # 4. Ustawienie Stanu Gry (Stan gry zostanie ustawiony w run_game, po podmianie obiektów)
        
        interface.add_to_log(f"Gra załadowana pomyślnie z {SAVE_FILE}.")
        
        return new_hero, new_world, new_log

    except FileNotFoundError:
        # Ten błąd powinien być już obsłużony przez os.path.exists
        interface.add_to_log("Błąd ładowania: Plik zapisu nie istnieje.")
        return None, None, None
    except Exception as e:
        interface.add_to_log(f"Błąd ładowania gry: {e}")
        return None, None, None
        
        
# ====================================================================
# --- 5. GŁÓWNA PĘTLA GRY ---
# ====================================================================

def run_game():
    
    # --- Inicjalizacja Gry (Start Menu) ---
    current_game = GameInterface(Hero("TEMP", "Warrior"), World(theme="default"))
    current_game.set_game_state("START_MENU")
    
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Obsługa wpisywania
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # Naciśnięto ENTER - przetwarzanie komendy
                    command = current_game.input_text
                    current_game.input_text = ""

                    if current_game.game_state == "START_MENU":
                         parts = command.split()
                         if parts[0].lower() == "new" and len(parts) >= 3:
                             name = parts[1].title()
                             hero_class = parts[2].title()
                             theme = parts[3].lower() if len(parts) >= 4 and parts[3].lower() in MAP_THEMES else "default"
                             
                             if hero_class in HERO_CLASSES:
                                 new_hero = Hero(name, hero_class)
                                 new_world = World(theme=theme)
                                 current_game = GameInterface(new_hero, new_world)
                                 current_game.set_game_state("EXPLORATION")
                                 current_game.add_to_log(f"Utworzono nowego bohatera: **{name}**, Klasa: **{hero_class}**, Motyw: **{theme}**.")
                             else:
                                 current_game.add_to_log(f"Nieznana klasa: {hero_class}. Dostępne: Warrior, Mage, Rogue.")
                                 
                         elif parts[0].lower() == "load":
                             loaded_hero, loaded_world, loaded_log = load_game(current_game)
                             if loaded_hero:
                                 # Zastąpienie instancji gry załadowanymi danymi
                                 current_game = GameInterface(loaded_hero, loaded_world)
                                 current_game.log = loaded_log
                                 # Ustawienie stanu gry na podstawie zapisu
                                 current_game.set_game_state(data.get('game_state', 'EXPLORATION')) # Używamy stanu z pliku (jeśli jest)
                                 current_game.add_to_log("Wczytano zapis gry. Witaj z powrotem!")
                             else:
                                  current_game.add_to_log("Nie udało się wczytać gry.")
                                  
                         else:
                             current_game.add_to_log("Nieprawidłowa komenda. Użyj 'new [imie] [klasa] [motyw]' lub 'load'.")
                    
                    # W pozostałych stanach
                    elif current_game.game_state not in ["DEFEAT", "WIN"]:
                        current_game.handle_command(command)

                elif event.key == pygame.K_BACKSPACE:
                    current_game.input_text = current_game.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    # Zapobieganie wstawianiu zbyt długiego tekstu
                    if len(current_game.input_text) < 50:
                        current_game.input_text += event.unicode
                        
                # Obsługa skrótów klawiszowych dla ruchu (tylko w eksploracji)
                if current_game.game_state == "EXPLORATION":
                     if event.key == pygame.K_w: current_game.handle_command("north")
                     elif event.key == pygame.K_s: current_game.handle_command("south")
                     elif event.key == pygame.K_a: current_game.handle_command("west")
                     elif event.key == pygame.K_d: current_game.handle_command("east")
                     elif event.key == pygame.K_p: # Skrót do sklepu
                         if current_game.world.get_current_location() == "town":
                             current_game.handle_command("shop")


        # --- Rysowanie ---
        current_game.draw()
        
        # Ograniczenie klatek na sekundę
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    run_game()

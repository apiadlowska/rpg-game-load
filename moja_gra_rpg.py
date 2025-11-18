from random import randint, choice
import os
import time

# --- UŻYTECZNE FUNKCJE ---

def clear_screen():
    """Czyści konsolę. Używa 'cls' dla Windows i 'clear' dla systemów UNIX/Linux/Mac."""
    os.system('cls' if os.name == 'nt' else 'clear')

def pause(seconds=3):
    """Pauzuje wykonanie na określoną liczbę sekund i czyści ekran."""
    time.sleep(seconds)
    clear_screen()

# --- DEFINICJE STATYSTYK I KLAS ---

# hero: [0-HP, 1-ATK, 2-MANA, 3-GOLD, 4-POTIONS_HP, 5-POTIONS_MANA]
BASE_STATS = {
    "Wojownik": [250, 25, 50, 150, 1, 0],
    "Mag":      [180, 15, 150, 100, 0, 1],
    "Łowca":    [200, 20, 100, 125, 1, 1]
}

# Definicje Potworów (HP, ATK, MANA, GOLD_MIN, GOLD_MAX)
MONSTERS = {
    "Goblin":   (30, 8, 0, 10, 20),
    "Wilk":     (50, 12, 0, 15, 30),
    "Szkielet": (70, 15, 10, 20, 40),
    "Ogr":      (100, 20, 0, 30, 60),
    "Harpia":   (85, 18, 20, 25, 50),
    "Wampir":   (120, 25, 50, 40, 70)
}

# Definicje Zaklęć (Koszt Many, Obrażenia/Leczenie)
SPELLS = {
    "Ognista Kula": (25, 35, "atak"),
    "Leczenie":     (40, 50, "leczenie"),
    "Błyskawica":   (15, 20, "atak"),
    "Tarcza Many":  (30, 0, "obrona") # Absorbuje nastepny atak
}

# Koszty w mieście
TAVERN_COST_PER_HP = 1
TAVERN_COST_PER_MANA = 1
FORGE_ATK_INCREMENT = 5
FORGE_COST_MULTIPLIER = 50
POTION_HP_COST = 30
POTION_MANA_COST = 40
POTION_HP_HEAL = 100
POTION_MANA_RESTORE = 100

# Globalne zmienne stanu
hero = []
max_hp = 0
max_mana = 0
hero_class = ""
shield_active = False # Nowy stan dla Tarczy Many

# --- INICJALIZACJA GRY ---
def setup_game():
    """Inicjuje wybór klasy i statystyki bohatera."""
    global hero, max_hp, max_mana, hero_class
    clear_screen()
    print("========================================")
    print("WITAJ W ŚWIECIE ISEKAI RPG")
    print("========================================")
    print("\nWybierz swoją klasę:")
    
    classes = list(BASE_STATS.keys())
    for i, name in enumerate(classes):
        stats = BASE_STATS[name]
        print(f"\t{i+1}. **{name}** (HP: {stats[0]}, ATK: {stats[1]}, MANA: {stats[2]}, GOLD: {stats[3]})")
    
    while True:
        try:
            choice_num = int(input("\nPodaj numer klasy: "))
            if 1 <= choice_num <= len(classes):
                hero_class = classes[choice_num - 1]
                hero = list(BASE_STATS[hero_class])
                max_hp = hero[0]
                max_mana = hero[2]
                print(f"\nWybrano klasę: **{hero_class}**! Rozpoczynasz przygodę.")
                pause(2)
                break
            else:
                print("Nieprawidłowy numer, spróbuj ponownie.")
        except ValueError:
            print("Wprowadź liczbę.")

# --- FUNKCJE WALKII ---
def create_enemy():
    """Losuje potwora, skalując jego statystyki na podstawie siły bohatera."""
    name, (base_hp, base_atk, base_mana, gold_min, gold_max) = choice(list(MONSTERS.items()))
    
    # Skalowanie wrogów
    scale = 1 + (hero[1] / 35) * 0.6 

    hp = randint(int(base_hp * scale * 0.8), int(base_hp * scale * 1.2))
    atk = randint(int(base_atk * scale * 0.8), int(base_atk * scale * 1.2))
    gold = randint(gold_min, gold_max)
    
    # enemy: [0-HP, 1-ATK, 2-MANA, 3-GOLD, 4-NAME]
    return [max(1, hp), max(1, atk), base_mana, gold, name]

def handle_magic_menu(enemy):
    """Obsługuje menu zaklęć."""
    global hero, shield_active
    
    print("\nDostępne Zaklęcia:")
    
    spell_names = list(SPELLS.keys())
    for i, name in enumerate(spell_names):
        cost, value, type = SPELLS[name]
        print(f"\t{i+1}. **{name}** (Koszt: {cost} Many, Wartość: {value}, Typ: {type.upper()})")

    print(f"\nTwoja Mana: {int(hero[2])}/{max_mana}")
    print("\tw - Wróć (bez rzucania)")
    
    while True:
        choice_input = input("Wybierz zaklęcie (numer lub 'w'): ").lower()
        if choice_input == 'w':
            print("Anulowano rzucanie zaklęcia.")
            time.sleep(1)
            return False
        
        try:
            spell_index = int(choice_input) - 1
            if 0 <= spell_index < len(spell_names):
                spell_name = spell_names[spell_index]
                cost, value, type = SPELLS[spell_name]
                
                if hero[2] >= cost:
                    hero[2] -= cost
                    print(f"\nRzucasz zaklęcie **{spell_name}**!")
                    
                    if type == "atak":
                        enemy[0] -= value
                        print(f"Zadajesz {value} obrażeń magicznych!")
                    elif type == "leczenie":
                        heal_amount = min(value, max_hp - hero[0])
                        hero[0] += heal_amount
                        print(f"Leczysz się za {heal_amount} HP!")
                    elif type == "obrona":
                        shield_active = True
                        print("Tarcza Many aktywowana! Następny atak wroga zostanie wchłonięty.")
                    
                    pause(2)
                    return True
                else:
                    print(f"Brak Many! Potrzebujesz {cost}, masz {int(hero[2])}.")
                    time.sleep(1)
                    return False
            else:
                print("Nieprawidłowy wybór zaklęcia.")
        except ValueError:
            print("Nieprawidłowe wejście. Wpisz numer lub 'w'.")

def handle_potion_menu(enemy):
    """Obsługuje menu mikstur."""
    global hero
    
    print("\nDostępne Mikstury:")
    print(f"\t1. Mikstura HP: Masz {hero[4]} (leczy {POTION_HP_HEAL} HP)")
    print(f"\t2. Mikstura Many: Masz {hero[5]} (odnawia {POTION_MANA_RESTORE} Many)")
    print("\tw - Wróć (bez użycia)")

    while True:
        choice_input = input("Wybierz miksturę (1/2/w): ").lower()
        if choice_input == 'w':
            print("Anulowano użycie mikstury.")
            time.sleep(1)
            return False

        if choice_input == '1':
            if hero[4] > 0:
                heal_amount = min(POTION_HP_HEAL, max_hp - hero[0])
                hero[0] += heal_amount
                hero[4] -= 1
                print(f"Używasz Mikstury HP, leczysz się za {heal_amount} HP! Pozostało: {hero[4]}.")
                pause(2)
                return True
            else:
                print("Brak Mikstur HP!")
        elif choice_input == '2':
            if hero[5] > 0:
                mana_restore = min(POTION_MANA_RESTORE, max_mana - hero[2])
                hero[2] += mana_restore
                hero[5] -= 1
                print(f"Używasz Mikstury Many, odnawiasz {mana_restore} Many! Pozostało: {hero[5]}.")
                pause(2)
                return True
            else:
                print("Brak Mikstur Many!")
        else:
            print("Nieprawidłowy wybór.")

def battle_loop():
    """Główna pętla walki w lesie."""
    global hero, shield_active
    enemy = create_enemy()
    enemy_name = enemy[4]
    shield_active = False

    clear_screen()
    print("WALKA! Wkroczyłeś do lasu i natknąłeś się na **{}**!".format(enemy_name))
    pause(1)

    while hero[0] > 0 and enemy[0] > 0:
        clear_screen()
        
        # 1. WYŚWIETLANIE STATYSTYK
        print("--- Twoja Tura ---")
        print(f"KLASA: **{hero_class}**")
        print(f"HERO: HP: {int(hero[0])}/{max_hp} | ATK: {hero[1]} | MANA: {int(hero[2])}/{max_mana} | GOLD: {hero[3]}")
        if shield_active:
             print("**Tarcza Many jest aktywna!**")
        print(f"PRZECIWNIK ({enemy_name}): HP: {int(enemy[0])} | ATK: {enemy[1]}")
        print("===============================")
        
        # 2. MENU AKCJI
        print("\ta - ATAK (fizyczny)")
        print("\tz - ZAKLĘCIA (magia)")
        print("\tl - LEKI/MIKSTURY (ekwipunek)")
        print("\tw - UCIECZKA (50% szans, kosztuje 10 gold)")
        print("===============================")
        
        inp = input("Co robisz: ").lower()
        
        player_action_taken = False
        
        # 3. AKCJA GRACZA
        if inp == "a":
            print(f"Atakujesz **{enemy_name}** za {hero[1]} obrażeń!")
            enemy[0] -= hero[1]
            player_action_taken = True
        
        elif inp == "z":
            player_action_taken = handle_magic_menu(enemy)
            
        elif inp == "l":
            player_action_taken = handle_potion_menu(enemy)
            
        elif inp == "w":
            if hero[3] >= 10:
                hero[3] -= 10
                if randint(1, 100) <= 50:
                    print("Udało Ci się uciec! Tracisz 10 złota.")
                    pause(2)
                    return
                else:
                    print("Ucieczka nie powiodła się! Tracisz 10 złota.")
                    player_action_taken = True
            else:
                print("Brak złota na próbę ucieczki (koszt: 10).")
                time.sleep(1)

        else:
            print("Stoisz w szoku i nic nie robisz... Tracisz turę.")
            player_action_taken = True

        # 4. TURA PRZECIWNIKA
        if player_action_taken:
            # Sprawdzenie, czy potwór padł PO akcji gracza
            if enemy[0] <= 0:
                break

            print("\n-- Tura Przeciwnika --")
            damage = enemy[1]
            
            if shield_active:
                print("Tarcza Many pochłania atak wroga! Nie tracisz HP.")
                shield_active = False
                time.sleep(1.5)
            else:
                hero[0] -= damage
                print(f"**{enemy_name}** atakuje Cię za {damage} obrażeń!")
                time.sleep(1.5)

    # 5. ZAKOŃCZENIE WALKI
    clear_screen()
    if hero[0] <= 0:
        print("KONIEC GRY! Bohater poległ w walce. Jesteś martwy.")
    elif enemy[0] <= 0:
        gold_gained = enemy[3]
        hero[3] += gold_gained
        print("ZWYCIĘSTWO! Pokonałeś {}!".format(enemy_name))
        print(f"Otrzymujesz {gold_gained} złota! Aktualne złoto: {hero[3]}")
    
    pause(4)

# --- FUNKCJE MIASTA ---
def enter_city():
    """Główne menu miasta."""
    global hero
    while True:
        clear_screen()
        print("WITAJ W MIEŚCIE")
        print("===============================")
        print(f"HERO: HP: {int(hero[0])}/{max_hp} | ATK: {hero[1]} | MANA: {int(hero[2])}/{max_mana} | GOLD: {hero[3]}")
        print(f"INWENTARZ: Mikstury HP: {hero[4]} | Mikstury Many: {hero[5]}")
        print("--- Opcje ---")
        print("\ta - Tawerna (Leczenie)")
        print("\tb - Kuźnia (Ulepszenia ATK)")
        print("\tc - Sklep z Miksturami (Zakupy)")
        print("\tw - Wróć do mapy świata")
        print("===============================")
        
        inp = input("Dokąd idziesz: ").lower()
        
        if inp == "a":
            tavern_menu()
        elif inp == "b":
            forge_menu()
        elif inp == "c":
            potion_shop_menu()
        elif inp == "w":
            print("Wracasz do mapy świata.")
            pause(1)
            break
        else:
            print("Nieprawidłowy wybór.")
            time.sleep(1)

def tavern_menu():
    """Menu leczenia w tawernie."""
    global hero
    clear_screen()
    
    hp_needed = max_hp - hero[0]
    mana_needed = max_mana - hero[2]
    cost_hp = int(hp_needed * TAVERN_COST_PER_HP)
    cost_mana = int(mana_needed * TAVERN_COST_PER_MANA)
    total_cost = cost_hp + cost_mana

    print("TAWERNA")
    print("Odpocznij i wylecz się.")
    print(f"Aktualnie masz: HP: {int(hero[0])}/{max_hp} | MANA: {int(hero[2])}/{max_mana}")
    print(f"Do pełnego zdrowia/many potrzeba: HP: {int(hp_needed)} ({cost_hp} złota) | MANA: {int(mana_needed)} ({cost_mana} złota)")
    print(f"Całkowity koszt: **{total_cost}** złota. Twoje złoto: {hero[3]}")
    
    inp = input("Czy chcesz się w pełni uleczyć i odnowić (t/n)?: ").lower()
    
    if inp == 't':
        if hero[3] >= total_cost and total_cost > 0:
            hero[0] = max_hp
            hero[2] = max_mana
            hero[3] -= total_cost
            print(f"Zostałeś w pełni uleczony i odnowiony! Tracisz {total_cost} złota.")
        elif total_cost == 0:
             print("Już jesteś w pełni zdrowia i many! Odpoczynek za darmo!")
        else:
            print("Za mało złota! Wrócisz, gdy będziesz bogatszy.")
    else:
        print("Wychodzisz z Tawerny bez odpoczynku.")

    pause(3)

def forge_menu():
    """Menu ulepszania ataku w kuźni."""
    global hero
    clear_screen()
    
    current_atk = hero[1]
    # Koszt rośnie z każdym ulepszeniem (skalowanie trudności)
    cost = FORGE_COST_MULTIPLIER + (current_atk * 5)
    
    print("KUŹNIA")
    print(f"Aktualny ATK: {current_atk}")
    print(f"Następne ulepszenie (dodaje +{FORGE_ATK_INCREMENT} ATK) kosztuje **{cost}** złota.")
    print(f"Twoje złoto: {hero[3]}")
    
    inp = input("Czy chcesz ulepszyć Atak (t/n)?: ").lower()
    
    if inp == 't':
        if hero[3] >= cost:
            hero[3] -= cost
            hero[1] += FORGE_ATK_INCREMENT
            print(f"Twój Atak został ulepszony! Nowy ATK: {hero[1]}. Tracisz {cost} złota.")
        else:
            print("Za mało złota na ulepszenie!")
    else:
        print("Opuszczasz Kuźnię.")
        
    pause(3)

def potion_shop_menu():
    """Menu zakupu mikstur."""
    global hero
    while True:
        clear_screen()
        print("SKLEP Z MIKSTURAMI")
        print("--- Twoje Mikstury ---")
        print(f"Mikstura HP: {hero[4]} | Mikstura Many: {hero[5]}")
        print(f"Twoje złoto: {hero[3]}")
        print("--- Na Sprzedaż ---")
        print(f"\t1. Mikstura HP (+{POTION_HP_HEAL} HP) - Koszt: **{POTION_HP_COST}** złota")
        print(f"\t2. Mikstura Many (+{POTION_MANA_RESTORE} Mana) - Koszt: **{POTION_MANA_COST}** złota")
        print("\tw - Wróć do Miasta")

        inp = input("Co kupujesz (1/2/w)?: ").lower()

        if inp == 'w':
            break
        
        if inp == '1':
            cost = POTION_HP_COST
            if hero[3] >= cost:
                hero[3] -= cost
                hero[4] += 1
                print(f"Kupiono Miksturę HP! Pozostało złota: {hero[3]}")
            else:
                print("Za mało złota!")
        elif inp == '2':
            cost = POTION_MANA_COST
            if hero[3] >= cost:
                hero[3] -= cost
                hero[5] += 1
                print(f"Kupiono Miksturę Many! Pozostało złota: {hero[3]}")
            else:
                print("Za mało złota!")
        else:
            print("Nieprawidłowy wybór.")
            
        time.sleep(1.5)

# --- PĘTLA GŁÓWNA GRY ---
def main_game_loop():
    """Główna pętla sterująca grą."""
    clear_screen()
    setup_game()
    
    while hero[0] > 0:
        clear_screen()
        print("MAPA ŚWIATA")
        print("===============================")
        print(f"KLASA: **{hero_class}**")
        print(f"HERO: HP: {int(hero[0])}/{max_hp} | ATK: {hero[1]} | MANA: {int(hero[2])}/{max_mana} | GOLD: {hero[3]}")
        print(f"INWENTARZ: Mikstury HP: {hero[4]} | Mikstury Many: {hero[5]}")
        print("--- Akcje ---")
        print("""\ta - idz do lasu (Walka) \n \tb - idz do miasta (Zakupy/Leczenie)""")
        print("===============================")
        
        inp = input("Co robisz: ").lower()
        
        if inp == "a":
            battle_loop()
        elif inp == "b":
            enter_city()
        else:
            print("Siedzi bezczynie. Nic się nie dzieje.")
            pause(2)
            
    # Koniec gry po wyjściu z pętli głównej
    print("\n===============================")
    print("Gra zakończona. Uruchom ponownie, by rozpocząć nową przygodę.")
    print("===============================")
    time.sleep(5)


if __name__ == "__main__":
    main_game_loop()
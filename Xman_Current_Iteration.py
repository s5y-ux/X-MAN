import keyboard
import os
import time
import random

# ========================
# Config
# ========================
BOARD_WIDTH  = 30
BOARD_HEIGHT = 16   # visible rows

# ========================
# Colors
# ========================
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# ========================
# Utils
# ========================
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def create_empty_lines():
    for _ in range(2):
        print("")

# ========================
# Entities
# ========================
class Character:
    def __init__(self, x, y, health, attack):
        self.x = int(x)
        self.y = int(y)
        self.health = int(health)
        self.attack = list(attack)

class Player(Character):
    def __init__(self, x, y, health, attack, weapon, level, xp, gold):
        super().__init__(x, y, health, attack)
        self.weapon = str(weapon)
        self.level = int(level)
        self.xp = int(xp)
        self.gold = int(gold)

class Enemy(Character):
    def __init__(self, x, y, health, attack):
        super().__init__(x, y, health, attack)

class Shop:
    def __init__(self, x, y):
        self.x = int(x)
        self.y = int(y)

# ========================
# Art
# ========================
def print_alien_art():
    print("       _________")
    print("      /___   ___\\")
    print("     //@@@\\ /@@@\\")
    print("     \\@@@/ \\@@@//")
    print("      \\___  ___/")
    print("         | - |")
    print("          \\_/" + Colors.ENDC)

def print_shop_art():
    print(Colors.WARNING + "                ______________")
    print("    __,.,---'''''              '''''---..._")
    print(" ,-'             .....:::''::.:            '`-.")
    print("'           ...:::.....       '")
    print("            ''':::'''''       . ")
    print("            ''':::'''''       .               ,")
    print("|'-.._           ''''':::..::':          __,,-")
    print(" '-.._''`---.....______________.....---''__,,-")
    print("      ''`---.....______________.....---''" + Colors.ENDC)

def title_screen():
    print(Colors.OKCYAN + "__  __    __  __   ____   __  _ " + Colors.ENDC)
    print(Colors.OKCYAN + r"\ \/ /   |  \/  | / () \ |  \| |" + Colors.ENDC)
    print(Colors.OKCYAN + r"/_/\_\   |_|\/|_|/__/\__\|_|\__|" + Colors.ENDC)
    print(Colors.OKCYAN + "             X-Man" + Colors.ENDC)

# ========================
# UI helpers
# ========================
def show_stats():
    print("===============")
    print(Colors.OKGREEN + "Health: " + Colors.ENDC + str(Player_1.health))
    print("Weapon: " + Player_1.weapon)
    print(Colors.OKBLUE + "Level: " + Colors.ENDC + str(Player_1.level))
    print("XP: " + str(Player_1.xp))
    print(Colors.WARNING + "Gold: " + Colors.ENDC + str(Player_1.gold))
    print("===============")

def generate_board():
    width  = BOARD_WIDTH
    height = BOARD_HEIGHT

    for y in range(height):
        # fresh row each iteration
        row = ['-' for _ in range(width)]

        # place shops on this row
        for shop in shop_list:
            if 0 <= shop.x < width and 0 <= shop.y < height and shop.y == y:
                row[shop.x] = Colors.OKGREEN + 'S' + Colors.ENDC

        # place enemies on this row
        for enemy in enemy_list:
            if 0 <= enemy.x < width and 0 <= enemy.y < height and enemy.y == y:
                row[enemy.x] = Colors.FAIL + 'E' + Colors.ENDC

        # place player on this row (draw last to sit "on top")
        if 0 <= Player_1.x < width and 0 <= Player_1.y < height and Player_1.y == y:
            row[Player_1.x] = Colors.OKCYAN + 'X' + Colors.ENDC  # X-Man

        print(''.join(row))

    create_empty_lines()
    show_stats()

def encounter_check():
    for enemy in enemy_list:
        if Player_1.x == enemy.x and Player_1.y == enemy.y:
            clear_screen()
            enemy_encounter(enemy)
    for shop in shop_list:
        if Player_1.x == shop.x and Player_1.y == shop.y:
            clear_screen()
            shop_encounter()

# ========================
# Encounters
# ========================
def enemy_prompt(exact_enemy):
    if exact_enemy.health <= 0:
        death_encounter(exact_enemy)
        return

    answer = input(">: ").lower()
    if answer == "help":
        create_empty_lines()
        print("Attack | Run")
        time.sleep(1.0)
        enemy_encounter(exact_enemy)

    elif answer == "attack" and exact_enemy.health > 0:
        player_attack_value = random.randint(0, len(Player_1.attack) - 1)
        enemy_attack_value = random.randint(0, len(exact_enemy.attack) - 1)
        create_empty_lines()
        print("You attack the Alien...")
        create_empty_lines()
        exact_enemy.health -= Player_1.attack[player_attack_value]
        if player_attack_value == len(Player_1.attack) - 1:
            print(Colors.OKGREEN + "Critical hit on the alien!" + Colors.ENDC)
        print(f"(*) You did {Player_1.attack[player_attack_value]} damage!")
        print("")
        if exact_enemy.health > 0:
            if enemy_attack_value == len(exact_enemy.attack) - 1:
                print(Colors.FAIL + "Critical hit on you!" + Colors.ENDC)
            Player_1.health -= exact_enemy.attack[enemy_attack_value]
            print(f"-[*]- The alien did {exact_enemy.attack[enemy_attack_value]} damage to you!")
        time.sleep(1.0)
        enemy_encounter(exact_enemy)

    elif answer == "run" and exact_enemy.health > 0:
        decision = random.randint(0, 1)
        if decision == 0:
            create_empty_lines()
            print("The Alien has caught you...")
            time.sleep(1.0)
            enemy_encounter(exact_enemy)
        else:
            create_empty_lines()
            print("Got away safe and sound...")
            create_empty_lines()
            print(Colors.OKGREEN + "Press W/A/S/D Keys to Move..." + Colors.ENDC)
    else:
        create_empty_lines()
        print("Unknown Command, type 'help' for help!")
        time.sleep(0.7)
        enemy_encounter(exact_enemy)

def enemy_encounter(exact_enemy):
    clear_screen()
    print_alien_art()
    create_empty_lines()
    if exact_enemy.health > 0:
        print("YOU HAVE ENCOUNTERED AN ENEMY!")
    print("")
    print("===============")
    print(f"Player Health: {Player_1.health}")
    print(f"Enemy  Health: {max(0, exact_enemy.health)}")
    print("===============")
    create_empty_lines()
    print("Type 'help' for a list of actions...")
    create_empty_lines()
    enemy_prompt(exact_enemy)

def death_prompt():
    # NOTE: 'searched' needs to persist per corpse to matter; keeping simple here.
    answer = input(">: ").lower()
    if answer == "exit":
        create_empty_lines()
        print(Colors.OKGREEN + "Press W/A/S/D Keys to Move..." + Colors.ENDC)
    elif answer == "help":
        create_empty_lines()
        print("Exit | Tbag | Search")
        death_prompt()
    elif answer == "tbag":
        create_empty_lines()
        print("You t-bag the alien's dead corpse XD...")
        death_prompt()
    elif answer == "search":
        # single search reward (simple, not per-corpse persistent)
        gold = random.randint(10, 15)
        create_empty_lines()
        print("You found: " + Colors.WARNING + f"{gold}" + Colors.ENDC + " Gold!")
        Player_1.gold += gold
        print(f"You now have {Player_1.gold} Gold!")
        death_prompt()
    else:
        create_empty_lines()
        print("Unknown Command, type 'help' for help!")
        death_prompt()

def death_encounter(exact_enemy):
    # remove enemy from play space
    exact_enemy.x = 99
    exact_enemy.y = 99
    clear_screen()
    print_alien_art()
    create_empty_lines()
    print("YOU HAVE KILLED AN ENEMY!")
    print("")
    print("Type 'help' for a list of actions...")
    create_empty_lines()
    death_prompt()

def shop_prompt():
    create_empty_lines()
    answer = input(">: ").lower()
    if answer == "help":
        create_empty_lines()
        print("Buy Sword | Buy Mace | Buy Axe | Exit")
        time.sleep(0.8)
        shop_encounter()
    elif answer == "exit":
        print("Exiting...")
        create_empty_lines()
        print(Colors.OKGREEN + "Press W/A/S/D Keys to Move..." + Colors.ENDC)
    elif answer.startswith("buy"):
        wanted = answer.replace("buy", "").strip().title()
        # find weapon by name
        for _, (name, dmg_list, price) in weapons.items():
            if name == wanted:
                if Player_1.gold < price:
                    print(f"You cannot afford the {name}...")
                else:
                    Player_1.gold -= price
                    Player_1.attack = dmg_list
                    Player_1.weapon = name
                    print(f"You have successfully purchased the {name}!")
                time.sleep(1.0)
                shop_encounter()
                return
        print("Unknown weapon. Type 'help' for options.")
        time.sleep(0.8)
        shop_encounter()
    else:
        print("Unknown Command, type 'help' for help!")
        time.sleep(0.8)
        shop_encounter()

def shop_encounter():
    clear_screen()
    print_shop_art()
    create_empty_lines()
    print(f"Gold: {Player_1.gold}")
    create_empty_lines()
    print("===============")
    # FIX: iterate dictionary values properly
    for _, (name, dmg_list, price) in weapons.items():
        print(f"{name} | Price: {price}")
    print("===============")
    shop_prompt()

# ========================
# Main
# ========================
if __name__ == "__main__":
    # init world
    Enemy_1 = Enemy(random.randint(3, BOARD_WIDTH - 1), random.randint(3, BOARD_HEIGHT - 1), 60, [25, 22, 21, 30])
    Enemy_2 = Enemy(random.randint(3, BOARD_WIDTH - 1), random.randint(3, BOARD_HEIGHT - 1), 60, [25, 22, 21, 30])
    Enemy_3 = Enemy(random.randint(3, BOARD_WIDTH - 1), random.randint(3, BOARD_HEIGHT - 1), 60, [25, 22, 21, 30])
    Player_1 = Player(4, 4, 700, [25, 22, 21, 30], "None", 1, 0, 0)
    Shop_1 = Shop(1, 1)

    enemy_list = [Enemy_1, Enemy_2, Enemy_3]
    shop_list = [Shop_1]

    weapons = {
        0: ["Sword", [27, 24, 23, 32], 10],
        1: ["Mace",  [28, 25, 24, 33], 20],
        2: ["Axe",   [30, 27, 26, 35], 35]
    }

    clear_screen()
    title_screen()
    time.sleep(1.2)
    clear_screen()
    print(Colors.OKGREEN + "Press W/A/S/D Keys to Start..." + Colors.ENDC)

    # initial draw
    generate_board()

    # Game loop (keyboard polling)
    while True:
        moved = False

        if keyboard.is_pressed('w'):
            # enemies "drift" vertically a bit
            for enemy in enemy_list:
                if 1 < enemy.y < BOARD_HEIGHT - 2:
                    enemy.y += random.randint(-1, 1)
                elif enemy.y <= 1:
                    enemy.y += 1
                elif enemy.y >= BOARD_HEIGHT - 2:
                    enemy.y -= 1
                enemy.y = clamp(enemy.y, 0, BOARD_HEIGHT - 1)

            Player_1.y -= 1
            Player_1.y = clamp(Player_1.y, 0, BOARD_HEIGHT - 1)
            moved = True

        if keyboard.is_pressed('s'):
            for enemy in enemy_list:
                if 1 < enemy.y < BOARD_HEIGHT - 2:
                    enemy.y += random.randint(-1, 1)
                elif enemy.y <= 1:
                    enemy.y += 1
                elif enemy.y >= BOARD_HEIGHT - 2:
                    enemy.y -= 1
                enemy.y = clamp(enemy.y, 0, BOARD_HEIGHT - 1)

            Player_1.y += 1
            Player_1.y = clamp(Player_1.y, 0, BOARD_HEIGHT - 1)
            moved = True

        if keyboard.is_pressed('a'):
            for enemy in enemy_list:
                if 1 < enemy.x < BOARD_WIDTH - 2:
                    enemy.x += random.randint(-1, 1)
                elif enemy.x <= 1:
                    enemy.x += 1
                elif enemy.x >= BOARD_WIDTH - 2:
                    enemy.x -= 1
                enemy.x = clamp(enemy.x, 0, BOARD_WIDTH - 1)

            Player_1.x -= 1
            Player_1.x = clamp(Player_1.x, 0, BOARD_WIDTH - 1)
            moved = True

        if keyboard.is_pressed('d'):
            for enemy in enemy_list:
                if 1 < enemy.x < BOARD_WIDTH - 2:
                    enemy.x += random.randint(-1, 1)
                elif enemy.x <= 1:
                    enemy.x += 1
                elif enemy.x >= BOARD_WIDTH - 2:
                    enemy.x -= 1
                enemy.x = clamp(enemy.x, 0, BOARD_WIDTH - 1)

            Player_1.x += 1
            Player_1.x = clamp(Player_1.x, 0, BOARD_WIDTH - 1)
            moved = True

        if moved:
            clear_screen()
            generate_board()
            encounter_check()
            time.sleep(0.12)  # small debounce

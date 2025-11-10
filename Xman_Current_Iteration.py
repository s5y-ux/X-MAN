import keyboard
import os
import time
import random
import sys

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
    DARK = '\033[90m'

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

def flush_input():
    """Clear any pending keyboard input from buffer"""
    if os.name == 'nt':  # Windows
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getch()
    else:  # Unix/Linux/Mac
        import termios
        termios.tcflush(sys.stdin, termios.TCIOFLUSH)

# ========================
# Entities
# ========================
class Character:
    def __init__(self, x, y, health, attack):
        self.x = int(x)
        self.y = int(y)
        self.max_health = int(health)
        self.health = int(health)
        self.attack = list(attack)

class Player(Character):
    def __init__(self, x, y, health, attack, weapon, level, xp, gold):
        super().__init__(x, y, health, attack)
        self.weapon = str(weapon)
        self.level = int(level)
        self.xp = int(xp)
        self.gold = int(gold)
        self.burn_damage = 0
        self.burn_turns = 0
        self.wither_damage = 0
        self.wither_turns = 0
        self.weakness_turns = 0
        self.armor = 0
        self.health_potions = 0
        self.big_potions = 0
        
        # Weapon inventory
        self.owned_weapons = {"Fists": True}

        self.total_gold = int(gold)      # total gold earned this session
        self.enemies_killed = 0         # total enemies killed this session
    
    def gain_xp(self, amount):
        """Add XP and check for level up"""
        self.xp += amount
        xp_needed = self.level * 100
        if self.xp >= xp_needed:
            self.level += 1
            self.xp -= xp_needed
            self.max_health += 50
            old_health = self.health
            self.health = self.max_health
            self.attack = [dmg + 7 for dmg in self.attack]  # Increased from +5 to +7
            return True
        return False
    
    def apply_burn(self):
        """Apply burn damage if burning"""
        if self.burn_turns > 0:
            self.health -= self.burn_damage
            self.burn_turns -= 1
            return True
        return False
    
    def apply_wither(self):
        """Apply wither damage if withering"""
        if self.wither_turns > 0:
            self.health -= self.wither_damage
            self.wither_turns -= 1
            if self.wither_turns == 0:
                self.weakness_turns = 0  # Remove weakness when wither ends
            return True
        return False

class Enemy(Character):
    def __init__(self, x, y, health, attack, enemy_type="normal"):
        super().__init__(x, y, health, attack)
        self.searched = False
        self.is_dead = False
        self.respawn_timer = 0
        self.enemy_type = enemy_type  # "normal", "agile", "fire", "darkness"
        self.loot_given = False  # Track if base loot was given on death
        self.attack_counter = 0  # For darkness special attack tracking
    
    def reset_health(self):
        """Reset enemy to full health for new encounter"""
        self.health = self.max_health
        self.is_dead = False
        self.searched = False
        self.loot_given = False
        self.attack_counter = 0
    
    def scale_to_level(self, player_level):
        """Scale enemy stats based on player level"""
        if self.enemy_type == "darkness":
            # Darkness enemy has fixed stats
            level_mult = 1 + (player_level - 1) * 0.15
            self.max_health = int(120 * level_mult)
            self.health = self.max_health
            base_attacks = [30, 25, 35, 39]
            self.attack = [int(dmg * level_mult) for dmg in base_attacks]
        else:
            level_mult = 1 + (player_level - 1) * 0.2  # 20% increase per level
            self.max_health = int(50 * level_mult)
            self.health = self.max_health
            base_attacks = [20, 18, 17, 25]
            self.attack = [int(dmg * level_mult) for dmg in base_attacks]

class Shop:
    def __init__(self, x, y):
        self.x = int(x)
        self.y = int(y)

# ========================
# Art
# ========================
def print_alien_art(enemy_type="normal"):
    if enemy_type == "agile":
        print(Colors.OKCYAN + "       _________")
        print("      /___   ___\\")
        print("     //@@@\\ /@@@\\")
        print("     \\@@@/ \\@@@//")
        print("      \\___  ___/")
        print("         |~~~|    (AGILE)")
        print("          \\_/" + Colors.ENDC)
    elif enemy_type == "fire":
        print(Colors.WARNING + "       _________")
        print("      /___   ___\\")
        print("     //@@@\\ /@@@\\")
        print("     \\@@@/ \\@@@//")
        print("      \\___  ___/")
        print("    ~~~~~| - |~~~~~  (FIRE)")
        print("          \\_/" + Colors.ENDC)
    elif enemy_type == "darkness":
        print(Colors.DARK + "                                               ")
        print("             XMENXM    EN              X    MENXM")
        print("          ENXMENXM    EN               XM    ENXMENXM")
        print("        XMENXMENX    XME               NXM    ENXMENXME")
        print("     NXMENXMENXME    NXME             NXME    NXMENXMENXME")
        print("    NEXMENXMENXME    NXMENXMENXMENXMENXMEN     XMENXMENXMENX")
        print("  MENXMENXMENXMEN     XMENXMENXMENXMENXME     NXMENXMENXMENXM")
        print(" ENXMENXMENXMENXME      NXMENXMENXMENX      MENXMENXMENXMENXM")
        print(" ENXMENXMENXMENXMEN      XMENXMENXMEN      XMENXMENXMENXMENXM")
        print("ENXMENXMENXMENXMENXM      ENXMENXMENX     MENXMENXMENXMENXMENX")
        print("                                                  (DARKNESS)" + Colors.ENDC)
    else:
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
    print(Colors.OKGREEN + f"Health: {Player_1.health}/{Player_1.max_health}" + Colors.ENDC)
    if Player_1.burn_turns > 0:
        print(Colors.WARNING + f"🔥 BURNING: {Player_1.burn_damage} dmg/turn for {Player_1.burn_turns} turns" + Colors.ENDC)
    if Player_1.wither_turns > 0:
        print(Colors.DARK + f"💀 WITHERING: {Player_1.wither_damage} dmg/turn for {Player_1.wither_turns} turns" + Colors.ENDC)
    if Player_1.weakness_turns > 0:
        print(Colors.DARK + f"⚠️  WEAKNESS: -50% damage for {Player_1.weakness_turns} turns" + Colors.ENDC)
    print("Weapon: " + Player_1.weapon)
    if Player_1.armor > 0:
        print(Colors.OKBLUE + f"Armor: {Player_1.armor} (reduces damage)" + Colors.ENDC)
    print(Colors.OKBLUE + "Level: " + Colors.ENDC + str(Player_1.level))
    print(f"XP: {Player_1.xp}/{Player_1.level * 100}")
    print(Colors.WARNING + "Gold: " + Colors.ENDC + str(Player_1.gold))
    print(Colors.HEADER + f"Potions: {Player_1.health_potions} | Big Potions: {Player_1.big_potions}" + Colors.ENDC)
    print("===============")

def generate_board():
    width  = BOARD_WIDTH
    height = BOARD_HEIGHT

    for y in range(height):
        row = ['-' for _ in range(width)]

        # place shops on this row
        for shop in shop_list:
            if 0 <= shop.x < width and 0 <= shop.y < height and shop.y == y:
                row[shop.x] = Colors.OKGREEN + 'S' + Colors.ENDC

        # place enemies on this row (only if alive)
        for enemy in enemy_list:
            if not enemy.is_dead and 0 <= enemy.x < width and 0 <= enemy.y < height and enemy.y == y:
                if enemy.enemy_type == "agile":
                    row[enemy.x] = Colors.OKCYAN + '^' + Colors.ENDC
                elif enemy.enemy_type == "fire":
                    row[enemy.x] = Colors.WARNING + 'O' + Colors.ENDC
                elif enemy.enemy_type == "darkness":
                    row[enemy.x] = ' '  # Blank space - invisible!
                else:
                    row[enemy.x] = Colors.FAIL + 'E' + Colors.ENDC

        # place player on this row (draw last to sit "on top")
        if 0 <= Player_1.x < width and 0 <= Player_1.y < height and Player_1.y == y:
            row[Player_1.x] = Colors.OKCYAN + 'X' + Colors.ENDC

        print(''.join(row))

    create_empty_lines()
    show_stats()

def encounter_check():
    for enemy in enemy_list:
        if Player_1.x == enemy.x and Player_1.y == enemy.y and not enemy.is_dead:
            enemy.reset_health()
            enemy.scale_to_level(Player_1.level)  # Scale enemy to player level
            clear_screen()
            flush_input()
            enemy_encounter(enemy)
    for shop in shop_list:
        if Player_1.x == shop.x and Player_1.y == shop.y:
            clear_screen()
            flush_input()
            shop_encounter()

def respawn_enemies():
    """Handle enemy respawning"""
    for enemy in enemy_list:
        if enemy.is_dead:
            enemy.respawn_timer += 1
            respawn_time = 120 if enemy.enemy_type == "darkness" else 50
            if enemy.respawn_timer >= respawn_time:
                enemy.is_dead = False
                enemy.respawn_timer = 0
                enemy.searched = False
                enemy.loot_given = False
                # Respawn at random location
                enemy.x = random.randint(3, BOARD_WIDTH - 1)
                enemy.y = random.randint(3, BOARD_HEIGHT - 1)
                enemy.reset_health()

# ========================
# Encounters
# ========================
def enemy_prompt(exact_enemy):
    if exact_enemy.health <= 0:
        death_encounter(exact_enemy)
        return

    answer = input(">: ").lower().strip()
    if answer == "help":
        create_empty_lines()
        print("Attack | Run | Potion | BigPotion")
        time.sleep(2.5)
        enemy_encounter(exact_enemy)
    
    elif answer == "potion":
        if Player_1.health_potions <= 0:
            create_empty_lines()
            print("You don't have any health potions!")
            time.sleep(1.0)
            enemy_encounter(exact_enemy)
        else:
            Player_1.health_potions -= 1
            heal_amount = random.randint(30, 50)
            Player_1.health = min(Player_1.max_health, Player_1.health + heal_amount)
            create_empty_lines()
            print(Colors.OKGREEN + f"You drank a potion and restored {heal_amount} HP!" + Colors.ENDC)
            print(f"Current Health: {Player_1.health}/{Player_1.max_health}")
            print(Colors.HEADER + f"Potions remaining: {Player_1.health_potions}" + Colors.ENDC)
            time.sleep(1.5)
            # Potion doesn't consume a turn, return to combat
            enemy_encounter(exact_enemy)
    
    elif answer == "bigpotion":
        if Player_1.big_potions <= 0:
            create_empty_lines()
            print("You don't have any big potions!")
            time.sleep(1.0)
            enemy_encounter(exact_enemy)
        else:
            Player_1.big_potions -= 1
            heal_amount = random.randint(50, 100)
            Player_1.health = min(Player_1.max_health, Player_1.health + heal_amount)
            create_empty_lines()
            print(Colors.OKGREEN + f"You drank a BIG POTION and restored {heal_amount} HP!" + Colors.ENDC)
            print(f"Current Health: {Player_1.health}/{Player_1.max_health}")
            print(Colors.HEADER + f"Big Potions remaining: {Player_1.big_potions}" + Colors.ENDC)
            time.sleep(1.5)
            # Potion doesn't consume a turn, return to combat
            enemy_encounter(exact_enemy)

    elif answer == "attack" and exact_enemy.health > 0:
        # Apply status effects to player first
        wither_damage_taken = False
        if Player_1.apply_wither():
            create_empty_lines()
            print(Colors.DARK + f"💀 You take {Player_1.wither_damage} wither damage! ({Player_1.wither_turns} turns left)" + Colors.ENDC)
            wither_damage_taken = True
            time.sleep(1.0)
            if Player_1.health <= 0:
                game_over()
                return
        
        if Player_1.apply_burn():
            if wither_damage_taken:
                print("")
            else:
                create_empty_lines()
            print(Colors.WARNING + f"🔥 You take {Player_1.burn_damage} burn damage! ({Player_1.burn_turns} turns left)" + Colors.ENDC)
            time.sleep(1.0)
            if Player_1.health <= 0:
                game_over()
                return
        
        # Check if attack misses (agile or darkness enemies)
        miss_chance = 0
        if exact_enemy.enemy_type == "agile":
            miss_chance = 0.35
        elif exact_enemy.enemy_type == "darkness":
            miss_chance = 0.05
        
        if miss_chance > 0 and random.random() < miss_chance:
            create_empty_lines()
            if exact_enemy.enemy_type == "darkness":
                print(Colors.DARK + "Your attack passes through the darkness!" + Colors.ENDC)
            else:
                print(Colors.OKCYAN + "The agile alien dodged your attack!" + Colors.ENDC)
            print("")
            # Enemy still attacks back
            enemy_attack_value = random.randint(0, len(exact_enemy.attack) - 1)
            if enemy_attack_value == len(exact_enemy.attack) - 1:
                print(Colors.FAIL + "Critical hit on you!" + Colors.ENDC)
            base_damage = exact_enemy.attack[enemy_attack_value]
            actual_damage = max(1, base_damage - (Player_1.armor * 2))
            Player_1.health -= actual_damage
            
            if Player_1.armor > 0:
                print(f"-[*]- The enemy did {base_damage} damage ({actual_damage} after armor)!")
            else:
                print(f"-[*]- The enemy did {actual_damage} damage to you!")
            
            # Darkness special attack check
            if exact_enemy.enemy_type == "darkness":
                exact_enemy.attack_counter += 1
                if exact_enemy.attack_counter % 4 == 0:
                    Player_1.wither_damage = 8
                    Player_1.wither_turns = 2
                    Player_1.weakness_turns = 2
                    print(Colors.DARK + "💀 The darkness withers you! 8 damage/turn for 2 turns + WEAKNESS!" + Colors.ENDC)
            
            # Fire enemy applies burn
            if exact_enemy.enemy_type == "fire" and random.random() < 0.5:
                burn_dmg = random.randint(3, 7)
                burn_duration = random.randint(2, 4)
                Player_1.burn_damage = burn_dmg
                Player_1.burn_turns = burn_duration
                print(Colors.WARNING + f"🔥 You've been set on fire! {burn_dmg} damage per turn for {burn_duration} turns!" + Colors.ENDC)
            
            if Player_1.health <= 0:
                game_over()
                return
            time.sleep(1.5)
            enemy_encounter(exact_enemy)
            return
        
        # Normal attack
        player_attack_value = random.randint(0, len(Player_1.attack) - 1)
        enemy_attack_value = random.randint(0, len(exact_enemy.attack) - 1)
        create_empty_lines()
        print("You attack the enemy...")
        create_empty_lines()
        
        # Calculate damage (reduced by weakness)
        damage = Player_1.attack[player_attack_value]
        if Player_1.weakness_turns > 0:
            damage = int(damage * 0.5)
            print(Colors.DARK + "(Your damage is halved by WEAKNESS!)" + Colors.ENDC)
        
        exact_enemy.health -= damage
        if player_attack_value == len(Player_1.attack) - 1:
            print(Colors.OKGREEN + "Critical hit on the enemy!" + Colors.ENDC)
        print(f"(*) You did {damage} damage!")
        print("")
        
        # Check if player killed enemy
        if exact_enemy.health <= 0:
            enemy_encounter(exact_enemy)
            return
        
        # Enemy attacks back
        if enemy_attack_value == len(exact_enemy.attack) - 1:
            print(Colors.FAIL + "Critical hit on you!" + Colors.ENDC)
        
        base_damage = exact_enemy.attack[enemy_attack_value]
        # Apply armor reduction
        actual_damage = max(1, base_damage - (Player_1.armor * 2))
        Player_1.health -= actual_damage
        
        if Player_1.armor > 0:
            print(f"-[*]- The enemy did {base_damage} damage ({actual_damage} after armor)!")
        else:
            print(f"-[*]- The enemy did {actual_damage} damage to you!")
        
        # Darkness special attack (every 4th attack)
        if exact_enemy.enemy_type == "darkness":
            exact_enemy.attack_counter += 1
            if exact_enemy.attack_counter % 4 == 0:
                Player_1.wither_damage = 8
                Player_1.wither_turns = 2
                Player_1.weakness_turns = 2
                print(Colors.DARK + "💀 The darkness withers you! 8 damage/turn for 2 turns + WEAKNESS!" + Colors.ENDC)
        
        # Fire enemy applies burn
        if exact_enemy.enemy_type == "fire" and random.random() < 0.5:
            burn_dmg = random.randint(3, 7)
            burn_duration = random.randint(2, 4)
            Player_1.burn_damage = burn_dmg
            Player_1.burn_turns = burn_duration
            print(Colors.WARNING + f"🔥 You've been set on fire! {burn_dmg} damage per turn for {burn_duration} turns!" + Colors.ENDC)
        
        # Check if player died
        if Player_1.health <= 0:
            game_over()
            return
            
        time.sleep(1.5)
        enemy_encounter(exact_enemy)

    elif answer == "run" and exact_enemy.health > 0:
        decision = random.randint(0, 1)
        if decision == 0:
            create_empty_lines()
            print("The enemy has caught you...")
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
    print_alien_art(exact_enemy.enemy_type)
    create_empty_lines()
    if exact_enemy.health > 0:
        type_name = "ENEMY"
        if exact_enemy.enemy_type == "agile":
            type_name = Colors.OKCYAN + "AGILE ENEMY" + Colors.ENDC + " (Can dodge attacks!)"
        elif exact_enemy.enemy_type == "fire":
            type_name = Colors.WARNING + "FIRE ENEMY" + Colors.ENDC + " (Can burn you!)"
        elif exact_enemy.enemy_type == "darkness":
            type_name = Colors.DARK + "DARKNESS ENTITY" + Colors.ENDC + " (Withers and weakens!)"
        print(f"YOU HAVE ENCOUNTERED {type_name}!")
    print("")
    print("===============")
    print(f"Player Health: {Player_1.health}/{Player_1.max_health}")
    if Player_1.burn_turns > 0:
        print(Colors.WARNING + f"🔥 Burning: {Player_1.burn_damage} dmg/turn ({Player_1.burn_turns} turns)" + Colors.ENDC)
    if Player_1.wither_turns > 0:
        print(Colors.DARK + f"💀 Withering: {Player_1.wither_damage} dmg/turn ({Player_1.wither_turns} turns)" + Colors.ENDC)
    if Player_1.weakness_turns > 0:
        print(Colors.DARK + f"⚠️  Weakness: -50% damage ({Player_1.weakness_turns} turns)" + Colors.ENDC)
    print(f"Enemy  Health: {max(0, exact_enemy.health)}")
    if exact_enemy.enemy_type == "darkness" and exact_enemy.attack_counter > 0:
        turns_until_special = 4 - (exact_enemy.attack_counter % 4)
        if turns_until_special == 4:
            turns_until_special = 0
        if turns_until_special > 0:
            print(Colors.DARK + f"Next wither attack in: {turns_until_special} turns" + Colors.ENDC)
    print("===============")
    create_empty_lines()
    print("Type 'help' for a list of actions...")
    create_empty_lines()
    enemy_prompt(exact_enemy)

def death_prompt(exact_enemy):
    answer = input(">: ").lower().strip()
    if answer == "exit":
        create_empty_lines()
        print(Colors.OKGREEN + "Press W/A/S/D Keys to Move..." + Colors.ENDC)
    elif answer == "help":
        create_empty_lines()
        print("Exit | Tbag | Search")
        death_prompt(exact_enemy)
    elif answer == "tbag":
        create_empty_lines()
        if exact_enemy.enemy_type == "darkness":
            print("You attempt to t-bag the darkness... but there's nothing there...")
        else:
            print("You t-bag the alien's dead corpse XD...")
        death_prompt(exact_enemy)
    elif answer == "search":
        if exact_enemy.searched:
            create_empty_lines()
            print("You've already searched this corpse!")
            death_prompt(exact_enemy)
        else:
            exact_enemy.searched = True
            # Give small bonus for searching (since main loot was given on kill)
            bonus_gold = random.randint(3, 8)
            
            # Bonus rewards for special enemies
            if exact_enemy.enemy_type == "agile":
                bonus_gold += 2
            elif exact_enemy.enemy_type == "fire":
                bonus_gold += 3
            elif exact_enemy.enemy_type == "darkness":
                bonus_gold += 5
            
            create_empty_lines()
            print("You search the remains...")
            print("You found: " + Colors.WARNING + f"{bonus_gold}" + Colors.ENDC + " extra Gold!")
            Player_1.gold += bonus_gold
            Player_1.total_gold += bonus_gold
            
            print(f"You now have {Player_1.gold} Gold total!")
            death_prompt(exact_enemy)
    else:
        create_empty_lines()
        print("Unknown Command, type 'help' for help!")
        death_prompt(exact_enemy)

def death_encounter(exact_enemy):
    exact_enemy.is_dead = True

    # XP reward
    xp_reward = random.randint(30, 50)
    if exact_enemy.enemy_type == "agile":
        xp_reward += 20
    elif exact_enemy.enemy_type == "fire":
        xp_reward += 30
    elif exact_enemy.enemy_type == "darkness":
        xp_reward += 50

    # Gold reward on kill
    gold_reward = random.randint(10, 15)
    if exact_enemy.enemy_type == "agile":
        gold_reward += 5
    elif exact_enemy.enemy_type == "fire":
        gold_reward += 10
    elif exact_enemy.enemy_type == "darkness":
        gold_reward += 15

    # Mark that base loot was given on death
    exact_enemy.loot_given = True

    # Apply rewards to player
    Player_1.gold += gold_reward
    Player_1.total_gold += gold_reward
    Player_1.enemies_killed += 1

    leveled_up = Player_1.gain_xp(xp_reward)

    clear_screen()
    print_alien_art(exact_enemy.enemy_type)
    create_empty_lines()
    print("YOU HAVE KILLED AN ENEMY!")
    print(Colors.OKBLUE + f"You gained {xp_reward} XP!" + Colors.ENDC)
    print(Colors.WARNING + f"You found {gold_reward} Gold!" + Colors.ENDC)

    if leveled_up:
        create_empty_lines()
        print(Colors.OKGREEN + "★★★ LEVEL UP! ★★★" + Colors.ENDC)
        print(f"You are now level {Player_1.level}!")
        print(f"Max Health increased to {Player_1.max_health}!")
        print("Attack damage increased!")
        print(Colors.OKGREEN + "Fully healed!" + Colors.ENDC)
        if Player_1.burn_turns > 0:
            Player_1.burn_turns = 0
            print(Colors.OKGREEN + "Burn cured!" + Colors.ENDC)
        if Player_1.wither_turns > 0:
            Player_1.wither_turns = 0
            Player_1.weakness_turns = 0
            print(Colors.OKGREEN + "Wither and weakness cured!" + Colors.ENDC)
        time.sleep(2.0)

    print("")
    print("Type 'help' for a list of actions...")
    create_empty_lines()
    death_prompt(exact_enemy)

def shop_prompt():
    create_empty_lines()
    answer = input(">: ").lower().strip()
    if answer == "help":
        create_empty_lines()
        print("Buy Sword | Buy Mace | Buy Axe | Buy Potion | Buy BigPotion | Buy Armor")
        print("Equip Sword | Equip Mace | Equip Axe | Equip Fists | Exit")
        time.sleep(2.5)
        shop_encounter()
    elif answer == "exit":
        print("Exiting...")
        create_empty_lines()
        print(Colors.OKGREEN + "Press W/A/S/D Keys to Move..." + Colors.ENDC)
    
    elif answer.startswith("equip"):
        weapon_name = answer.replace("equip", "").strip().title()
        
        if weapon_name in Player_1.owned_weapons:
            # Find the weapon stats
            weapon_found = False
            if weapon_name == "Fists":
                Player_1.weapon = "Fists"
                Player_1.attack = [25, 22, 21, 30]
                # Apply level scaling
                for _ in range(Player_1.level - 1):
                    Player_1.attack = [dmg + 7 for dmg in Player_1.attack]
                weapon_found = True
            else:
                for _, (name, dmg_list, price) in weapons.items():
                    if name == weapon_name:
                        Player_1.weapon = name
                        Player_1.attack = dmg_list.copy()
                        # Apply level scaling
                        for _ in range(Player_1.level - 1):
                            Player_1.attack = [dmg + 7 for dmg in Player_1.attack]
                        weapon_found = True
                        break
            
            if weapon_found:
                print(Colors.OKGREEN + f"Equipped {weapon_name}!" + Colors.ENDC)
            else:
                print(f"You don't own {weapon_name}!")
        else:
            print(f"You don't own {weapon_name}!")
        time.sleep(1.0)
        shop_encounter()
    
    elif answer.startswith("buy"):
        wanted = answer.replace("buy", "").strip().title()
        
        # Check for potion
        if wanted == "Potion":
            potion_price = 10
            if Player_1.gold < potion_price:
                print("You cannot afford a Potion...")
            else:
                Player_1.gold -= potion_price
                Player_1.health_potions += 1
                print(Colors.OKGREEN + "You have purchased a Potion!" + Colors.ENDC)
                print(f"You now have {Player_1.health_potions} potion(s)")
            time.sleep(1.0)
            shop_encounter()
            return
        
        # Check for big potion
        if wanted == "Bigpotion":
            bigpotion_price = 25
            if Player_1.gold < bigpotion_price:
                print("You cannot afford a Big Potion...")
            else:
                Player_1.gold -= bigpotion_price
                Player_1.big_potions += 1
                print(Colors.OKGREEN + "You have purchased a Big Potion!" + Colors.ENDC)
                print(f"You now have {Player_1.big_potions} big potion(s)")
            time.sleep(1.0)
            shop_encounter()
            return
        
        # Check for armor
        if wanted == "Armor":
            armor_price = 50
            if Player_1.gold < armor_price:
                print("You cannot afford Armor...")
            elif Player_1.armor >= 10:
                print("You already have maximum armor!")
            else:
                Player_1.gold -= armor_price
                Player_1.armor += 5
                print(Colors.OKBLUE + "You have purchased Armor! +5 damage reduction" + Colors.ENDC)
                print(f"Current armor: {Player_1.armor} (blocks {Player_1.armor * 2} damage)")
            time.sleep(1.0)
            shop_encounter()
            return
        
        # Check weapons
        for _, (name, dmg_list, price) in weapons.items():
            if name == wanted:
                if wanted in Player_1.owned_weapons:
                    print(f"You already own the {name}! Use 'Equip {name}' to equip it.")
                elif Player_1.gold < price:
                    print(f"You cannot afford the {name}...")
                else:
                    Player_1.gold -= price
                    Player_1.owned_weapons[name] = True
                    Player_1.attack = dmg_list.copy()
                    # Apply level scaling
                    for _ in range(Player_1.level - 1):
                        Player_1.attack = [dmg + 7 for dmg in Player_1.attack]
                    Player_1.weapon = name
                    print(Colors.OKGREEN + f"You have purchased and equipped the {name}!" + Colors.ENDC)
                time.sleep(1.0)
                shop_encounter()
                return
        print("Unknown item. Type 'help' for options.")
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
    print("WEAPONS:")
    for _, (name, dmg_list, price) in weapons.items():
        owned_marker = Colors.OKGREEN + " [OWNED]" + Colors.ENDC if name in Player_1.owned_weapons else ""
        equipped_marker = Colors.OKCYAN + " [EQUIPPED]" + Colors.ENDC if name == Player_1.weapon else ""
        print(f"  {name} | Price: {price}{owned_marker}{equipped_marker}")
    
    # Show Fists option
    equipped_fists = Colors.OKCYAN + " [EQUIPPED]" + Colors.ENDC if Player_1.weapon == "Fists" else ""
    print(f"  Fists | Always owned{equipped_fists}")
    
    print("")
    print("ITEMS:")
    print(f"  Potion | Price: 10 (heals 30-50 HP)")
    print(f"  BigPotion | Price: 25 (heals 50-100 HP)")
    print(f"  Armor | Price: 50 (+5 armor, blocks 10 dmg per piece, max 10)")
    print("===============")
    shop_prompt()

def game_over():
    clear_screen()
    print(Colors.FAIL + "=" * 40)
    print("           GAME OVER")
    print("      You have been defeated!")
    print("=" * 40 + Colors.ENDC)
    print("")
    print(f"Final Level: {Player_1.level}")
    print(f"Total Gold Collected: {Player_1.total_gold}")
    print(f"Enemies Defeated: {Player_1.enemies_killed}")
    print("")
    print("Thanks for playing X-Man!")
    sys.exit()

def spawn_enemy_by_level(player_level):
    """Determine enemy type based on player level"""
    if player_level >= 5:
        rand = random.random()
        if rand < 0.15:  # 15% darkness (rare)
            return "darkness"
        elif rand < 0.40:  # 25% agile
            return "agile"
        elif rand < 0.55:  # 15% fire
            return "fire"
    elif player_level >= 4:
        rand = random.random()
        if rand < 0.3:  # 30% agile
            return "agile"
        elif rand < 0.5:  # 20% fire
            return "fire"
    return "normal"

# ========================
# Main
# ========================
if __name__ == "__main__":
    # init world
    Player_1 = Player(4, 4, 100, [25, 22, 21, 30], "Fists", 1, 0, 0)
    
    # Create initial enemies (5 enemies - all start as normal)
    Enemy_1 = Enemy(random.randint(3, BOARD_WIDTH - 1), random.randint(3, BOARD_HEIGHT - 1), 50, [20, 18, 17, 25], "normal")
    Enemy_2 = Enemy(random.randint(3, BOARD_WIDTH - 1), random.randint(3, BOARD_HEIGHT - 1), 50, [20, 18, 17, 25], "normal")
    Enemy_3 = Enemy(random.randint(3, BOARD_WIDTH - 1), random.randint(3, BOARD_HEIGHT - 1), 50, [20, 18, 17, 25], "normal")
    Enemy_4 = Enemy(random.randint(3, BOARD_WIDTH - 1), random.randint(3, BOARD_HEIGHT - 1), 50, [20, 18, 17, 25], "normal")
    Enemy_5 = Enemy(random.randint(3, BOARD_WIDTH - 1), random.randint(3, BOARD_HEIGHT - 1), 50, [20, 18, 17, 25], "normal")
    
    Shop_1 = Shop(1, 1)

    enemy_list = [Enemy_1, Enemy_2, Enemy_3, Enemy_4, Enemy_5]
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

    turn_counter = 0

    # Game loop (keyboard polling)
    while True:
        moved = False

        if keyboard.is_pressed('w'):
            for enemy in enemy_list:
                if not enemy.is_dead:
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
                if not enemy.is_dead:
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
                if not enemy.is_dead:
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
                if not enemy.is_dead:
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
            turn_counter += 1
            respawn_enemies()
            
            # When enemies respawn at higher levels, they can become special types
            for enemy in enemy_list:
                if not enemy.is_dead and enemy.respawn_timer == 0:
                    # Check if this is a fresh respawn
                    if turn_counter % 50 == 0:  # Just respawned
                        new_type = spawn_enemy_by_level(Player_1.level)
                        if enemy.enemy_type != "darkness" or new_type == "darkness":
                            enemy.enemy_type = new_type
            
            clear_screen()
            generate_board()
            encounter_check()
            time.sleep(0.12)

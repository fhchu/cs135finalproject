# Tile Strategy by Felix Chu
# Tile Strategy is a roguelike game where the player attempts to survive as long as possible within an 8 by 8 matrix.
# Game controls are Up, Down, Left, and Right, which move the player, and Space, which skips your turn.
import sys
import os
import random
import pickle
import pygame
import numpy as np
from pygame.locals import *

# Define things for readability. Never changed in-game.
fps = 60
window_width  = 800
window_height = 600
board_width = 8
board_height = 8

# Define colors
black = (  0,   0,   0)
white = (255, 255, 255)
grey  = (128, 128, 128)
red   = (255,   0,   0)

# Define directions
up    = 'up'
down  = 'down'
left  = 'left'
right = 'right'

# Define tile types for use in the array
grass  = 0
player = 1
slime  = 2
wolf   = 3
potion = 4
stairs = 5

# Define tile stat locations for use in the array
tile   = 0
hp     = 1
atk    = 2
exp    = 3
moved  = 4
ground = 5


class Tile_strategy:
    # The main function loads necessary game elements such as the fps clock, window, fonts, sprites, etc. 
    # It then runs each of the game functions in order: the title screen, the game itself, the game over screen, then finally the score board.
    def main(self):
        pygame.init() 
        self.clock = pygame.time.Clock() 
        self.screen = pygame.display.set_mode((window_width, window_height)) 
        self.font = pygame.font.Font('freesansbold.ttf', 24)
        self.big_font = pygame.font.Font('freesansbold.ttf', 48) 
        self.images = {grass  : pygame.image.load('grass.png'), 
                       player : pygame.image.load('player.png'),
                       slime  : pygame.image.load('slime.png'),
                       wolf   : pygame.image.load('wolf.png'),
                       potion : pygame.image.load('potion.png'),
                       stairs : pygame.image.load('stairs.png')}
        self.enemies = [slime, wolf] 
        self.species_list = [None, None, 'slime', 'wolf']
        pygame.display.set_caption('Tile Strategy') 
        pygame.display.set_icon(pygame.image.load('player.png'))
        self.start() 
        self.run()
        self.game_over()
        self.score_board()

    # Runs the start screen. The player can start a new game or continue from a saved game here.
    # Any save data will be deleted when the game starts.
    def start(self):
        # The following code makes the screen black, then displays the title screen text.
        self.screen.fill(black)
        title_text = self.big_font.render('Tile Strategy', True, white)
        title_text_rect = title_text.get_rect()
        title_text_rect.center = (window_width / 2, window_height / 2 - 36)
        self.screen.blit(title_text, title_text_rect)
        start_text = self.font.render('Press Space to start a new game', True, white)
        start_text_rect = start_text.get_rect()
        start_text_rect.center = (window_width / 2, window_height / 2)
        self.screen.blit(start_text, start_text_rect)
        # If there is a save data, show the option to resume from save. Otherwise don't show this.
        if os.path.exists('save.dat'):
            continue_text = self.font.render('Press Enter/Return to resume from save', True, white)
            continue_text_rect = continue_text.get_rect()
            continue_text_rect.center = (window_height / 2 + 100, window_height / 2 + 32)
            self.screen.blit(continue_text, continue_text_rect)
        # Infinite loop keeps the title screen running.
        # Pressing Space or Return ends the title screen, starting the game.
        # self.load tells the game whether or not it's loading a save state.
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.quit()
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.quit()
                    elif event.key == K_RETURN:
                        if os.path.exists('save.dat'):
                            self.load = True
                        else:
                            self.load = False
                        return
                    elif event.key == K_SPACE:
                        if os.path.exists('save.dat'):
                            os.remove('save.dat')
                        self.load = False
                        return
            pygame.display.update()
            self.clock.tick(fps)

    #Quits the game. It's only called when pressing ESC or clicking the X button.
    def quit(self): 
        pygame.quit()
        sys.exit()                 

    # Runs the game itself. Keeps running until the player dies or quits.
    def run(self):
        # If the game isn't loading from save, it starts the game with a blank slate.
        if self.load == True:
            self.load_game()
        else:
            self.array = np.zeros((8,8,6), dtype=np.int)
            self.player_x = 0
            self.player_y = 0
            self.player_max_hp = 20
            self.player_hp = self.player_max_hp
            self.player_atk = 10
            self.player_exp = 1
            self.level = 1
            self.level_ups = 1
            self.potion_count = 0
            self.floor = 1
            self.total_turn = 0
            self.build_board()
            self.enemy_count = 0
            self.floor_turn = 0
        # combat_message contains a string displayed on the bottom of the screen.
        # It begins as None and changes when combat happens.
        self.combat_message = None
        # Once this bool is True, it's game over. 
        self.is_dead = False
        # arange creates an array of integers from 1-100.
        self.levels = np.arange(1, 101)
        # The for loop determines the player's EXP curve.
        for x in range(len(self.levels)):
            self.levels[x] += x * x * 2
        # self.draw() draws the game onto the game window.
        self.draw()
        # direction starts out as None. It changes depending on which key is pressed.
        direction = None
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.save_game()
                    quit()
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.save_game()
                        quit()
                    elif event.key == K_UP:
                        direction = up
                    elif event.key == K_DOWN:
                        direction = down
                    elif event.key == K_LEFT:
                        direction = left
                    elif event.key == K_RIGHT:
                        direction = right
                    elif event.key == K_SPACE:
                        self.play_turn()
                    # Upon a successful player action, the rest of the turn is played out.
                    if direction != None and self.check_move(direction) == True:
                        self.draw()
                        self.play_turn()
                        direction = None
                    # Ends the function when the player dies
                    if self.is_dead == True: 
                        return
            pygame.display.update()
            self.clock.tick(fps)

    # This function saves the game state as an array, then saves that array as a binary file.
    def save_game(self):
        game_state = [self.array, self.player_x, self.player_y, self.player_max_hp, self.player_hp, 
                      self.player_atk, self.player_exp, self.level, self.level_ups, self.potion_count,
                      self.floor, self.total_turn, self.enemy_count, self.floor_turn]
        with open('save.dat', 'wb') as f:
            pickle.dump(game_state, f)

    # This function loads the save data file as an array, then deletes the save data.
    # It then sets the game state values based on the array contents.
    def load_game(self):
        with open('save.dat', 'rb') as f:
            game_state = pickle.load(f)
        os.remove('save.dat')
        self.array         = game_state[0]
        self.player_x      = game_state[1]
        self.player_y      = game_state[2]
        self.player_max_hp = game_state[3]
        self.player_hp     = game_state[4]
        self.player_atk    = game_state[5]
        self.player_exp    = game_state[6]
        self.level         = game_state[7]
        self.level_ups     = game_state[8]
        self.potion_count  = game_state[9]
        self.floor         = game_state[10]
        self.total_turn    = game_state[11]
        self.enemy_count   = game_state[12]
        self.floor_turn    = game_state[13]

    # Creates a blank board.
    # Called in new games and whenever the player steps on stairs.
    def build_board(self):
        self.enemy_count = 0
        self.floor_turn = 0
        self.array.fill(grass)
        self.array[self.player_x][self.player_y][tile] = player
        stairs_x, stairs_y = self.check_tile()
        self.array[stairs_x][stairs_y][ground] = stairs
        # Randomly spawns potions on the ground. Higher floors are likely to have more potions.
        num_potions = random.randint(0, (self.floor //2))
        for i in range(num_potions):
            potion_x, potion_y = self.check_tile()
            self.array[potion_x][potion_y][ground] = potion

    # Checks if potential spawn tile is unoccupied.
    def check_tile(self): 
        while True:
            x = random.randint(0, board_width - 1)
            y = random.randint(0, board_height - 1)
            if self.array[x][y][tile] == grass and self.array[x][y][ground] == grass:
                return x, y

    # Draws the screen onto the game window.
    # Called whenever something on the screen changes, like movement.
    def draw(self):
        #Defines variables to draw the board onto the screen.
        top_border = 8
        left_border = 8
        board_size = 556
        board_top = 16
        board_left = 16
        line_width = 4
        box_size = 64
        box_spread = line_width + box_size
        self.screen.fill(black)
        # Draws the grey borders onto the screen.
        pygame.draw.rect(self.screen, grey, (left_border, top_border, board_size, board_size))
        # Fills the entire board with grass tiles.
        for x in range(board_width):
            for y in range(board_height):
                current_box = (board_left + box_spread * x, board_top + box_spread * y)
                self.screen.blit(self.images[grass], current_box)
        # Draws each game object onto the screen, from the player to items to enemies.
        for x in range(board_width):
            for y in range(board_height):
                board_tile = self.array[x][y][tile]
                current_box = (board_left + box_spread * x, board_top + box_spread * y)
                if self.array[x][y][ground] == potion:
                    self.screen.blit(self.images[potion], current_box)
                elif self.array[x][y][ground] == stairs:
                    self.screen.blit(self.images[stairs], current_box)
                if board_tile == player:
                    self.screen.blit(self.images[player], current_box)
                elif board_tile == slime:
                    self.screen.blit(self.images[slime], current_box)
                elif board_tile == wolf:
                    self.screen.blit(self.images[wolf], current_box)
        # Draw the UI. I'm sure I could lower the amount of lines but hey, it works
        text_space = 32
        floor_text = self.font.render('Floor %d' % self.floor, True, white)
        floor_text_rect = floor_text.get_rect()
        floor_text_rect.topleft = (board_size + board_left, top_border + text_space * 0)
        self.screen.blit(floor_text, floor_text_rect)
        level_text = self.font.render('Level %d' % self.level, True, white)
        level_text_rect = level_text.get_rect()
        level_text_rect.topleft = (board_size + board_left, top_border + text_space * 1)
        self.screen.blit(level_text, level_text_rect)
        hp_text = self.font.render('Health: %d/%d' % (self.player_hp, self.player_max_hp), True, white)
        hp_text_rect = hp_text.get_rect()
        hp_text_rect.topleft = (board_size + board_left, top_border + text_space * 2)
        self.screen.blit(hp_text, hp_text_rect)
        atk_text = self.font.render('Attack: %d' % self.player_atk, True, white)
        atk_text_rect = atk_text.get_rect()
        atk_text_rect.topleft = (board_size + board_left, top_border + text_space * 3)
        self.screen.blit(atk_text, atk_text_rect)
        exp_text = self.font.render('EXP: %d' % self.player_exp, True, white)
        exp_text_rect = exp_text.get_rect()
        exp_text_rect.topleft = (board_size + board_left, top_border + text_space * 4)
        self.screen.blit(exp_text, exp_text_rect)
        potion_text = self.font.render('Potions: %d' % self.potion_count, True, white)
        potion_text_rect = potion_text.get_rect()
        potion_text_rect.topleft = (board_size + board_left, top_border + text_space * 5)
        # If the player doesn't have any potions, the potion count is not displayed.
        if self.potion_count > 0:
            self.screen.blit(potion_text, potion_text_rect)
        bottom_text = self.font.render(self.combat_message, True, white)
        bottom_text_rect = bottom_text.get_rect()
        bottom_text_rect.topleft = (left_border, board_size + line_width + top_border)
        self.screen.blit(bottom_text, bottom_text_rect)

    # Checks if the player able to move to the input direction, then moves if possible.
    # If the input direction is occupied with an enemy, the player attacks the enemy.
    def check_move(self, direction): 
        if direction == up:
            if self.player_y > 0:
                if self.array[self.player_x][self.player_y - 1][tile] in self.enemies:
                    return self.player_attack(direction)
                else:
                    return self.move_player(direction)
        elif direction == down:
            if self.player_y < board_height - 1:
                if self.array[self.player_x][self.player_y + 1][tile] in self.enemies:
                    return self.player_attack(direction)
                else:
                    return self.move_player(direction)
        elif direction == right:
            if self.player_x < board_width - 1:
                if self.array[self.player_x + 1][self.player_y][tile] in self.enemies:
                    return self.player_attack(direction)
                else:
                    return self.move_player(direction)
        elif direction == left:
            if self.player_x > 0:
                if self.array[self.player_x - 1][self.player_y][tile] in self.enemies:
                    return self.player_attack(direction)
                else:
                    return self.move_player(direction)
        else:
            return False

    # Moves the player by editing the array.
    def move_player(self, direction):
        if direction == up:
            self.array[self.player_x][self.player_y][tile] = grass
            self.player_y -= 1
        elif direction == down:
            self.array[self.player_x][self.player_y][tile] = grass
            self.player_y +=1
        elif direction == left:
            self.array[self.player_x][self.player_y][tile] = grass
            self.player_x -= 1
        elif direction == right:
            self.array[self.player_x][self.player_y][tile] = grass
            self.player_x += 1
        self.array[self.player_x][self.player_y][tile] = player
        # If the tile the player moved to has a potion, pick up the potion.
        if self.array[self.player_x][self.player_y][ground] == potion:
            self.potion_count += 1
            self.array[self.player_x][self.player_y][ground] = grass
        # If the tile the player moved to is stairs, go up the stairs.
        if self.array[self.player_x][self.player_y][ground] == stairs:
            self.build_board()
            self.floor += 1
        return True
    
    # Attacks the enemy in the input direction.
    def player_attack(self, direction):
        x = self.player_x
        y = self.player_y
        if direction == up:
            # Reduced HP of enemy by the player's attack stat
            self.array[x][y - 1][hp] -= self.player_atk
            # Updates combat message, because combat is happening.
            self.combat_message = ('The %s took %d damage. ' % (self.species_list[int(self.array[x][y - 1][tile])], self.player_atk))
            # Checks to see if the enemy died. If it did, the player receives EXP.
            if self.array[x][y - 1][hp] <= 0:
                self.combat_message += ('The %s died. You gained %d exp.' % (self.species_list[int(self.array[x][y - 1][tile])], self.array[x][y - 1][exp]))
                self.player_exp += self.array[x][y - 1][exp]
                self.array[x][y - 1][tile] = grass
                self.enemy_count -= 1
        elif direction == down:
            self.combat_message = ('The %s took %d damage. ' % (self.species_list[int(self.array[x][y + 1][tile])], self.player_atk))
            self.array[x][y + 1][hp] -= self.player_atk
            if self.array[x][y + 1][hp] <= 0:
                self.combat_message += ('The %s died. You gained %d exp.' % (self.species_list[int(self.array[x][y + 1][tile])], self.array[x][y + 1][exp]))
                self.player_exp += self.array[x][y + 1][exp]
                self.array[x][y + 1][tile] = grass
                self.enemy_count -= 1
        elif direction == left:
            self.array[x - 1][y][hp] -= self.player_atk
            self.combat_message = ('The %s took %d damage. ' % (self.species_list[int(self.array[x - 1][y][tile])], self.player_atk))
            if self.array[x - 1][y][hp] <= 0:
                self.combat_message += ('The %s died. You gained %d exp.' % (self.species_list[int(self.array[x - 1][y][tile])], self.array[x - 1][y][exp]))
                self.player_exp += self.array[x - 1][y][exp]
                self.array[x - 1][y][tile] = grass
                self.enemy_count -= 1
        elif direction == right:
            self.array[x + 1][y][hp] -= self.player_atk
            self.combat_message = ('The %s took %d damage. ' % (self.species_list[int(self.array[x + 1][y][tile])], self.player_atk))
            if self.array[x + 1][y][hp] <= 0:
                self.combat_message += ('The %s died. You gained %d exp.' % (self.species_list[int(self.array[x + 1][y][tile])], self.array[x + 1][y][exp]))
                self.player_exp += self.array[x + 1][y][exp]
                self.array[x + 1][y][tile] = grass
                self.enemy_count -= 1
        # Checks to see if the player leveled up.
        self.level_update()
        print(self.combat_message)
        return True

    # Checks to see if the player leveled up.
    # If they did, the player is fully healed and their stats increase.
    def level_update(self):
        base_atk = 10
        base_hp = 20
        level_up = 0
        # Goes through entire level list created in self.run.
        for x in range(len(self.levels)):
            # Sets the player level to where they are on the EXP list.
            if self.player_exp >= self.levels[x]:
                self.level = x + 1
            # Checks to see if the player has leveled up.
            if self.level_ups < self.level:
                self.level_ups += 1
                level_up = 1
        # Set player stats to the player's level
        self.player_atk = base_atk + self.level - 1
        self.player_max_hp = base_hp + self.level - 1
        # If the player has leveled up, fully heal them.
        if level_up == 1:
            self.player_hp = self.player_max_hp

    # Each turn is as follows: Enemies move, enemies are spawned, and the board is drawn.
    def play_turn(self):
        self.move_enemies()
        self.spawn_enemy()
        self.floor_turn += 1
        self.total_turn += 1
        self.draw()

    # AI for the enemies. They will follow the player and attack if the player is adjacent.
    def move_enemies(self):
        # Sets the "moved" flag for all enemies to 0.
        for i in range(board_width):
            for j in range(board_height):
                self.array[i][j][moved] = 0
        # Goes through entire board looking for enemies
        for x in range(board_width):
            for y in range(board_height):
                # If the current tile is an enemy and it hasn't moved:
                if self.array[x][y][tile] in self.enemies and self.array[x][y][moved] == 0:
                    self.array[x][y][moved] = 1
                    player_is_adjacent = (y > 0 and self.array[x][y - 1][tile] == player) or \
                                         (y < board_height - 1 and self.array[x][y + 1][tile]  == player) or \
                                         (x > 0 and self.array[x - 1][y][tile] == player) or \
                                         (x < board_width - 1 and self.array[x + 1][y][tile] == player)
                    if  player_is_adjacent: # Attack
                        self.player_hp -= self.array[x][y][atk]
                        self.combat_message = ('You took %d damage. ' % self.array[x][y][atk])
                        print(self.combat_message)
                        # Checks to see if the player died from the enemy's attack
                        self.is_dead = self.death_check()
                    # If the player isn't adjacent, the enemy moves towards the player.
                    elif self.player_y < y and self.array[x][y - 1][tile] == grass: # Move up
                        self.array[x][y - 1][0:5] = self.array[x][y][0:5]
                        self.array[x][y][tile] = grass
                    elif self.player_y > y and self.array[x][y + 1][tile] == grass: # Move down
                        self.array[x][y + 1][0:5] = self.array[x][y][0:5]
                        self.array[x][y][tile] = grass
                    elif self.player_x < x and self.array[x - 1][y][tile] == grass: # Move left
                        self.array[x - 1][y][0:5] = self.array[x][y][0:5]
                        self.array[x][y][tile] = grass
                    elif self.player_x > x and self.array[x + 1][y][tile] == grass: # Move right
                        self.array[x + 1][y][0:5] = self.array[x][y][0:5]
                        self.array[x][y][tile] = grass

    # Checks to see if the player died. 
    def death_check(self):
        if self.player_hp <= 0:
            # If the player has a potion, use a potion and live another day.
            if self.potion_count > 0:
                self.player_hp = self.player_max_hp
                self.potion_count -= 1
                self.combat_message = ('You used a potion. Potions left: %d' % self.potion_count)
                print(self.combat_message)
                return False
            # If the player's out of potions, set the death bool to True.
            else:
                self.combat_message = ('You died.')
                print(self.combat_message)
                return True

    # Every 8 turns, an enemy is spawned in a random location.
    def spawn_enemy(self):
        spawn_cooldown = 8
        max_enemies = 8
        if self.floor_turn % spawn_cooldown == 0 and self.enemy_count < max_enemies:
            enemy_type = self.enemies[random.randint(0, len(self.enemies) - 1)]
            enemy = self.get_stats(enemy_type)
            x = enemy[6]
            y = enemy[7]
            # Places the enemy onto the game board array.
            self.array[x][y] = enemy[0:6]
            self.enemy_count += 1

    # Sets the newly spawned enemy's stats based on the game length and the floor the player has reached.
    def get_stats(self, enemy_type):
        if enemy_type == slime:
            enemy_hp = 15 + self.total_turn // 5 + self.floor
            enemy_atk = 4 + self.total_turn // 5 + self.floor
        elif enemy_type == wolf:
            enemy_hp = 8 + self.total_turn // 5 + self.floor
            enemy_atk = 8 + self.total_turn // 5 + self.floor
        enemy_exp = (enemy_hp + enemy_atk) // 2
        x, y = self.check_tile()
        return enemy_type, enemy_hp, enemy_atk, enemy_exp, 0, 0, x, y

    # Game Over screen. Shows the player's score and prompts them to enter their name for the Score Board.
    def game_over(self):
        print('Game over.')
        game_over_text = self.big_font.render('GAME OVER', True, red)
        game_over_text_rect = game_over_text.get_rect()
        game_over_text_rect.center = (window_width/2, window_height/2 - 48)
        self.score = self.total_turn * 5 + self.player_exp + self.floor * 10
        score_text = self.font.render('Score: %d' % self.score, True, white)
        score_text_rect = score_text.get_rect()
        score_text_rect.center = (window_width/2, window_height/2)
        name_prompt_text = self.font.render('Enter your name:', True, white)
        name_prompt_text_rect = score_text.get_rect()
        name_prompt_text_rect.center = (window_width/2 - 50, window_height/2 + 32)
        self.name = ''
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.quit()
                elif event.type == KEYDOWN:
                    if event.unicode.isalpha():
                        self.name += event.unicode
                    elif event.key == K_BACKSPACE:
                        self.name = self.name[:-1]
                    elif event.key == K_RETURN:
                        return
                    elif event.key == K_ESCAPE:
                        self.quit()
            self.screen.fill(black)
            self.screen.blit(game_over_text, game_over_text_rect)
            self.screen.blit(score_text, score_text_rect)
            self.screen.blit(name_prompt_text, name_prompt_text_rect)
            name_text = self.font.render(self.name, True, white)
            name_text_rect = name_text.get_rect()
            name_text_rect.center = (window_width/2, window_height/2 + 64)
            self.screen.blit(name_text, name_text_rect)
            pygame.display.update()
            self.clock.tick(fps)

    # Loads up the list of scores, then saves the new score to it and shows the top 10
    def score_board(self):
        if os.path.exists('high scores.dat'):
            with open('high scores.dat', 'rb') as f:
                score_board = pickle.load(f)
        else:
            score_board = [('99', 'default')]
        score_board.append((str(self.score), self.name))
        score_board.sort(key = lambda score: int(score[0]), reverse = True)
        print (score_board)
        while len(score_board) > 10:
           del score_board[-1]
        with open('high scores.dat', 'wb') as f:
            pickle.dump(score_board, f)
        font_spacing = 8
        top_border = 24
        font_size = 36
        score_font = pygame.font.Font('freesansbold.ttf', font_size) 
        self.screen.fill(black)
        high_scores_text = self.big_font.render('High Scores', True, white)
        high_scores_text_rect = high_scores_text.get_rect()
        high_scores_text_rect.midtop = (window_width / 2, top_border)
        self.screen.blit(high_scores_text, high_scores_text_rect)
        for x in range(len(score_board)):
            score = score_font.render('%s %s' % (score_board[x][0], score_board[x][1]), True, white)
            score_rect = score.get_rect()
            score_rect.center = (window_width / 2, top_border + font_size * (3 + x))
            self.screen.blit(score, score_rect)
        restart_text = self.font.render('Press Space to restart', True, white)
        restart_text_rect = restart_text.get_rect()
        restart_text_rect.center = (window_width / 2, window_height - 32)
        self.screen.blit(restart_text, restart_text_rect)
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.quit()
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.quit()
                    elif event.key == K_SPACE:
                        self.main()
            pygame.display.update()
            self.clock.tick(fps)


if __name__ == '__main__':
    Tile_strategy().main()
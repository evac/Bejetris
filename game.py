import core
import pyglet
from pyglet.window import key
from core import GameElement
import sys
import random


GAME_BOARD = None
GAME_WIDTH = 8
GAME_HEIGHT = 8
DEBUG = False
KEYBOARD = None
PLAYER = None
TICK = 0
MATCHES = []
POINTS = 0
LEVEL = 1

#### Class Definitions ####
class Character(GameElement):
    IMAGE = "Cat"
    ALIVE = True
    LIVES = 1

    def __init__(self):
        GameElement.__init__(self)

    def next_pos(self,direction):
        if direction == "up":
            return (self.x, self.y-1)
        elif direction == "down":
            return (self.x, self.y+1)
        elif direction == "left":
            return (self.x-1, self.y)
        elif direction == "right":
            return (self.x+1, self.y)
        return None

    def nearby_coordinates(self):
        x = self.x
        y = self.y
        coordinates = [
            [x-1, y],
            [x+1, y],
            [x, y-1],
            [x, y+1]
        ]
        return coordinates

    def nearby_blocks(self):
        coordinates = self.nearby_coordinates()
        blocks = []
        for coord in coordinates:
            if coord[0] < GAME_WIDTH and coord[0] >= 1 and coord[1] < GAME_HEIGHT and coord[1] >= 0:
                existing_el = GAME_BOARD.get_el(coord[0], coord[1])
                if existing_el:
                    blocks.append(coord)

        return blocks

    def die(self):
        x = self.x
        y = self.y
        #GAME_BOARD.del_el(x, y)

        # set gravestone
        gravestone = GraveStone()
        GAME_BOARD.register(gravestone)
        GAME_BOARD.set_el(x, y, gravestone)

        display_player_info()
        PLAYER.ALIVE = False

class Resource(GameElement):
    SOLID = True
    TICK = 0
    REMOVED = False

    def next_pos(self,direction):
        if direction == "up":
            return (self.x, self.y-1)
        elif direction == "down":
            return (self.x, self.y+1)
        elif direction == "left":
            return (self.x-1, self.y)
        elif direction == "right":
            return (self.x+1, self.y)
        return None

    def move(self, direction):
        next_location = self.next_pos(direction)
        next_x = next_location[0]
        next_y = next_location[1]

        # check if next position is outside of board
        if next_x < GAME_WIDTH and next_x >= 1 and next_y < GAME_HEIGHT and next_y >= 0:
            existing_el = GAME_BOARD.get_el(next_x, next_y)
            self.SOLID = False # 

            if existing_el.__class__.__name__ != 'Character':
                # check if adjacent element is block and move with it if it is
                if existing_el and existing_el.__class__.__name__ != "GraveStone":
                    existing_el.move(direction)

                if existing_el is None:
                    # If there's nothing there or the existing element isn't solid, walk through
                    GAME_BOARD.del_el(self.x, self.y)
                    GAME_BOARD.set_el(next_x, next_y, self)
                else:
                    self.SOLID = True
        else:
            self.SOLID = True

    def remove(self):
        self.REMOVED = True
        GAME_BOARD.del_el(self.x, self.y)

    def update(self, dt):
        if PLAYER.ALIVE:
            if LEVEL == 1:
                speed = 10
            elif LEVEL == 2:
                speed = 7
            elif LEVEL == 3:
                speed = 5
            elif LEVEL >= 4:
                speed = 1

            if self.TICK%speed == 0 and not self.REMOVED:
                self.move('down')

            self.TICK += 1

class Drop(Resource):
    SOLID = False

    def move(self, direction):
        next_location = self.next_pos('down')
        next_x = next_location[0]
        next_y = next_location[1]

        # check if next position is outside of board
        if next_x < GAME_WIDTH and next_x >= 1 and next_y < GAME_HEIGHT and next_y >= 0:
            existing_el = GAME_BOARD.get_el(next_x, next_y)
            self.interact(existing_el)
        else:
            self.remove()

    def interact():
        pass

    def update(self, dt):
        if PLAYER.ALIVE:
            if LEVEL == 1:
                speed = 5
            elif LEVEL == 2:
                speed = 3
            elif LEVEL >=3:
                speed = 1

            if self.TICK%speed == 0 and not self.REMOVED:
                self.move('down')

            self.TICK += 1

class Rock(Drop):
    IMAGE = "Rock"

    def interact(self, element):
        next_location = self.next_pos('down')
        next_x = next_location[0]
        next_y = next_location[1]

        if element.__class__.__name__ == 'Character':
            self.remove()
            PLAYER.LIVES -= 1
            if PLAYER.LIVES == 0:
                PLAYER.die()
                msg = "You lasted %d seconds and collected %d gems before dying from a heavy rock." %(TICK/10, POINTS)
                GAME_BOARD.draw_msg(msg)
        elif element is None:
            # move forward
            GAME_BOARD.del_el(self.x, self.y)
            GAME_BOARD.set_el(next_x, next_y, self)
        else:
            # remove rock
            self.remove()


class Heart(Drop):
    IMAGE = "Heart"

    def interact(self, element):
        next_location = self.next_pos('down')
        next_x = next_location[0]
        next_y = next_location[1]

        if element.__class__.__name__ == 'Character':
            self.remove()
            PLAYER.LIVES += 1
            GAME_BOARD.draw_msg("Yay, you gained a life!")
        elif element is None:
            # move forward
            GAME_BOARD.del_el(self.x, self.y)
            GAME_BOARD.set_el(next_x, next_y, self)
        else:
            # remove rock
            self.remove()

class BlueGem(Resource):
    IMAGE = "BlueGem"

class GreenGem(Resource):
    IMAGE = "GreenGem"

class OrangeGem(Resource):
    IMAGE = "OrangeGem"

class GraveStone(GameElement):
    IMAGE = "TallTree"

####   End class definitions    ####


# Check for rows of 3 or more matching gems #
def count_gems(row):
    matched_gems = []
    counted_gems = []
    for el in row:
        if el != None and el.SOLID and el.__class__.__name__ in "BlueGem GreenGem OrangeGem":
            if len(counted_gems) > 0 and counted_gems[0].__class__ != el.__class__:
                if len(counted_gems) >= 3:
                    matched_gems.extend(counted_gems)
                counted_gems = []

            counted_gems.append(el)
        else:
            if len(counted_gems) >= 3:
                matched_gems.extend(counted_gems)
            counted_gems = []

    if len(counted_gems) >= 3:
        matched_gems.extend(counted_gems)

    return matched_gems


# Helper to get matches #
def match_gems():
    all_gems = []
    matched_gems = []

    # make list of all positions of gens
    for x in range(1, GAME_WIDTH):
        column = []
        for y in range(GAME_HEIGHT):
            el = GAME_BOARD.get_el(x, y)
            column.append(el)

        check_overflow(column)
        all_gems.append(column)

    # check columns
    for col in all_gems:
        matches = count_gems(col)
        matched_gems.extend(matches)

    # check rows
    for i in range(GAME_HEIGHT):
        row_line = [row[i] for row in all_gems]
        matches = count_gems(row_line)
        matched_gems.extend(matches)

    return matched_gems

# Add points for cleared gems #
def collect_gems(matches):
    global POINTS

    for match in matches:
        POINTS += 1
        match.REMOVED = True
        match.remove()

# Check for game over if gems overflow to top #
def check_overflow(column):
    spaces = 0
    for el in column:
        if el is None:
            spaces += 1

    if spaces == 0:
        PLAYER.die()
        msg = "You lasted %d seconds and collected %d gems before your gems overflowed." %(TICK/10, POINTS)
        GAME_BOARD.draw_msg(msg)

# randomly generate an item to drop #
def random_drop():
    resource = None
    drop = random.randint(1, 100)

    if drop >= 1 and drop < 25:
        resource = OrangeGem()
    elif drop >= 30 and drop < 50:
        resource = GreenGem()
    elif drop >= 60 and drop < 75:
        resource = BlueGem()
    elif drop >= 75 and drop < 80:
        resource = Heart()
    else:
        resource = Rock()

    return resource

# place drop randomly
def set_random_drop():
    drop = random_drop()
    pos = random.randint(1, GAME_WIDTH - 1)
    GAME_BOARD.register(drop)
    GAME_BOARD.set_el(pos, 0, drop)

# player status announcements
def display_player_info():
    for i in range(GAME_HEIGHT - 1, -1, -1):
        if GAME_HEIGHT - PLAYER.LIVES - 1 < i:
            life = Heart()
            GAME_BOARD.register(life)
            GAME_BOARD.set_el(0, i, life)
        else:
            GAME_BOARD.del_el(0, i)

    msg = "You collected %d gems" % POINTS
    GAME_BOARD.draw_msg(msg)

def keyboard_handler():
    direction = None
    move_block = None
    delete_block = None

    if PLAYER.ALIVE:
        if KEYBOARD[key.UP]:
            direction="up"
        elif KEYBOARD[key.DOWN]:
            direction="down"
        elif KEYBOARD[key.LEFT]:
            direction="left"
        elif KEYBOARD[key.RIGHT]:
            direction="right"

        if KEYBOARD[key.P] and direction:
            move_block = True

        if direction:
            next_location = PLAYER.next_pos(direction)
            next_x = next_location[0]
            next_y = next_location[1]

            if next_x < GAME_WIDTH and next_x >= 1 and next_y < GAME_HEIGHT and next_y >= 0:
                existing_el = GAME_BOARD.get_el(next_x, next_y)
                el_class = existing_el.__class__.__name__

                if existing_el and el_class in 'Heart':
                    existing_el.interact(PLAYER)
                elif existing_el and el_class != "GraveStone":
                    existing_el.move(direction)

                if existing_el is None or not existing_el.SOLID:

                    # If there's nothing there or the existing element isn't solid, walk through
                    nearby_blocks = PLAYER.nearby_blocks()
                    GAME_BOARD.del_el(PLAYER.x, PLAYER.y)

                    if move_block and direction != None and nearby_blocks:
                        for coord in nearby_blocks:
                            # move block only in linear direction (so no moving blocks sideway)
                            if ((direction == 'left' or direction == 'right') and (next_y - coord[1] == 0)
                                or (direction == 'up' or direction == 'down') and (next_x - coord[0] == 0)):
                                block = GAME_BOARD.get_el(coord[0], coord[1])
                                block.move(direction)

                    GAME_BOARD.set_el(next_x, next_y, PLAYER)

# set speed of game
def update():
    global MATCHES
    global TICK
    global LEVEL

    if PLAYER.ALIVE:
        # display lives
        display_player_info()

        # check for matches and remove them
        MATCHES.extend(match_gems())
        collect_gems(MATCHES)
        MATCHES = []

        if LEVEL == 1:
            speed = 20
        elif LEVEL == 2:
            speed = 10
        elif LEVEL >= 3:
            speed = 5

        if TICK%speed == 0:
            set_random_drop()

        if TICK%600 == 0 and LEVEL <= 4:
            LEVEL += 1

        TICK += 1


def initialize():
    """Put game initialization code here"""
    GAME_BOARD.draw_msg("Match the gems 3 or more in a row. Avoid rocks!")

    # Player
    global PLAYER
    PLAYER = Character()
    GAME_BOARD.register(PLAYER)
    GAME_BOARD.set_el(1, GAME_HEIGHT - 1, PLAYER)
    print "Match the gems 3 or more in a row. Avoid rocks! Collect hearts to have more lives."

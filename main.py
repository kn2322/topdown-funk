import kivy
kivy.require('1.9.1')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, FadeTransition, Screen
from kivy.graphics import Rectangle, Color
from functools import partial
from utilfuncs import difference, get_direction, circle_collide
import camera
import chardata as char
import userinterface
import mapinfo
from kivy.vector import Vector
from math import hypot # Used in entity container
import random

Builder.load_string("""
#: kivy 1.9.1

<Game>
    game_map: game_map
    e_container: e_container
    user_interface: user_interface
    decal_engine: decal_engine
    Map:
        id: game_map
        size_hint: None, None

    DecalEngine:
        id: decal_engine

    EntityContainer:
        id: e_container

    UI:
        id: user_interface

    Label:
        pos: 300, 200
        text: 'Entity num: {}'.format(len(e_container.children))

<LevelUpScreen>

    Button:
        text: 'You have been visited by the spooky meme man, upvote in 2 seconds or never meme again.'

""")

Window.size = (1136, 640)


class ScreenManagement(ScreenManager):
    
    def __init__(self, **kw):
        super(ScreenManagement, self).__init__(**kw)
        self.transition = FadeTransition(duration=.8)

        self.game = Game(name='game')
        self.lvlup = LevelUpScreen(name='lvlup')

        self.add_widget(self.game)
        self.add_widget(self.lvlup)

        self.current = 'game'

    def game_over(self): # Called from game.
        self.__init__()

# Container widget for all game entites, so they can be referenced by the game.
# Also the collision detector

class Entities: # Data container for entities

    # Lists containing all the entities in any category,
    # Any entity only needs to know its name, and if an ability affects a category of other entities.

    # players includes all hero names.
    players = ['test_hero']
    # name, batch size, creation function.
    enemies = [
                ['Riot Police', 4, char.create_riot_police]
                ]
    projectiles = ['test_projectile']

class EntityContainer(Widget):

    def __init__(self, **kwargs):
        super(EntityContainer, self).__init__(**kwargs)
        en = Entities

        self.players = en.players
        self.enemies = [i[0] for i in en.enemies]
        self.projectiles = en.projectiles
        self.all_entites = set(self.players + self.enemies + self.projectiles)

        self.partition_size = 100
        self.grid = None

    
    # To be used in main loop with 'for i in children: if condition, destroy'
    # Additionally gold, exp, and such can be awarded here
    def update(self, game, *args):

        self.check_collision(game)
        
        for entity in self.children: # Consider changing to update all components of one type.
            entity.update(game)

    # Interface for adding entities, includes sanity checks
    def add_entity(self, entity):
        if entity.name not in self.all_entites:
            raise ValueError('The entity name {} does not exist.'.format(entity.name))

        self.add_widget(entity)

    # Used in check collision to move to nearest location inside of the map.
    def move_to_mapborder(self, entity, game_map): # Should be more static method.
        gm = game_map
        hit = False # If collided with wall.
        #print(gm.size)
        if entity.components['Physics'].can_collide_wall: # For things that can go out of map...
            if entity.x < 0:
                entity.x = 0
                hit = True
            if entity.right > gm.right - 0:
                entity.right = gm.right - 0
                hit = True
            if entity.y < 0:
                entity.y = 0
                hit = True
            if entity.top > gm.top - 0:
                entity.top = gm.top - 0
                hit = True
        if hit:
            entity.components['Physics'].collide_wall(entity, self)

    # Does the collision
    def check_collision(self, game):

        gm = game.game_map

        if self.grid is None:
            x = (gm.width // self.partition_size) + 1
            y = (gm.height // self.partition_size) + 1
            self.grid = [[[]] * y for _ in range(x)]

        for entity in self.children:
            self.move_to_mapborder(entity, gm)

            def get_cell(x, y): # of a point on the map.
                x = int(x)
                y = int(y)
                cell = []
                if x < 0:
                    cell.append(0)
                elif x > gm.width:
                    cell.append(gm.width // self.partition_size)
                else:
                    cell.append(x // self.partition_size)

                if y < 0:
                    cell.append(0)
                elif y > gm.height:
                    cell.append(gm.height // self.partition_size)
                else:
                    cell.append(y // self.partition_size)

                return cell


            min_cell = get_cell(entity.x, entity.y)
            max_cell = get_cell(entity.x + entity.width, entity.y + entity.height)

            cell_range_x = range(min_cell[0], max_cell[0]+1)
            cell_range_y = range(min_cell[1], max_cell[1]+1)

            for x in cell_range_x:
                for y in cell_range_y:
                    self.grid[x][y].append(entity)
            
        def resolve(a, b):

            if not circle_collide(a, b):
                return None

            if all([a.components['Physics'].can_collide(a, b), b.components['Physics'].can_collide(b, a)]):
                
                # Resolves the physics portion of the collision.
                diff = difference(a.pos, b.pos)
                depth = (a.width + b.width) / 2 - hypot(*diff) # Overlapping distance
                if depth <= 0: # Important to prevent moving by negative depth.
                    return None
                min_pv = Vector(*diff).normalize() * depth / 2 # Min penetrating vector from a's pov.
                    
                a.pos = Vector(*a.pos) - min_pv
                b.pos = Vector(*b.pos) + min_pv
                    
            # Collide for both entities MUST be called, since collision pairs shouldn't be repeated.
            a.components['Action'].collide(a, b, self)
            b.components['Action'].collide(b, a, self)

        for idx, a in enumerate(self.children):
            self.move_to_mapborder(a, gm)

            for b in self.children[idx+1:]:
                self.move_to_mapborder(b, gm)
                resolve(a, b)


        checked_pairs = []

        """for x in self.grid:
            for cell in x:
                for idx, a in enumerate(cell):
                    for b in cell[idx+1:]:
                        if set((a, b)) not in checked_pairs:
                            resolve(a, b)
                            checked_pairs.append(set((a, b)))"""


        


        """
        for idx, entity in enumerate(self.children):
            for other in self.children[idx+1:]:
                #print('{} checks against {}'.format(entity, other))
                if circle_collide(entity, other):

                    
                    # Collision direction, 1 is from right/top
                    col_dir_x = entity.x - other.x
                    try:
                        col_dir_x /= abs(col_dir_x)
                    except ZeroDivisionError:
                        col_dir_x = 1

                    col_dir_y = entity.y - other.y
                    try:
                        col_dir_y /= abs(col_dir_y)
                    except ZeroDivisionError:
                        col_dir_y = 1

                    # Vector x
                    vx = Vector(1, 0)
                    # Vector y
                    vy = Vector(0, 1)
                    
                    while abs(entity.x - other.x) < entity.width + other.width:
                        entity.move(Vector(entity.pos) + vx, map_size)
                        other.move(Vector(other.pos) - vx, map_size)

                    while abs(entity.y - other.y) < entity.height + other.height:
                        entity.move(Vector(entity.pos) + vy, map_size)
                        other.move(Vector(other.pos) - vy, map_size)
                    

                    entity.collide(other, self)
                    other.collide(entity, self)
            """

class WaveManager: # Handles generating waves and spawning enemies.

    def __init__(self):
        self.enemies = Entities.enemies
        self.batch_ref = range(21) # Number of batches in each wave, is an iterable. E.g. this one goes up to 20 waves.
        self.wave = 0

    def get_names(self): # A list containing all enemy names only.
        return [i[0] for i in self.enemies]

    def update(self, game):
        ec = game.e_container
        # Inefficient as it checks every update loop, checks for all enemies dead.
        for i in ec.children:
            if i.name in ec.enemies:
                return None
        self.next_wave(game)

    def next_wave(self, game):

        self.wave += 1
        game_map = game.game_map
        ec = game.e_container
        # Types of enemy in wave.
        chosen = [self.enemies[0]] # Provisional as there is only 1 enemy type
        for batch in range(self.batch_ref[self.wave]):
            en = random.choice(chosen)
            spawn_center = (800, 600) # Spawn location.
            for i in range(en[1]):
                pos = (spawn_center[0] + random.randint(-100, 100), spawn_center[1] + random.randint(-100, 100))
                e = en[2](pos)
                ec.add_entity(e)

    # Uses data on likelihood of enemies to appear to generate probs of chosen enemy types to appear.
    # TODO: create data struct for enemy probability modifiers.
    def gen_probability(self, enemies):
        return zip([1/len(enemies) for _ in enemies], enemies)

class DecalEngine(Widget): # Modified from graphics component.

    def __init__(self, **kw):
        super(DecalEngine, self).__init__(**kw)
        self.graphics = None
        self.decals = []
        self.image = 'assets/decals/splatter.png'
        self.decal_size = (50, 50) # Temporary.
        self.duration = 60

    # Not handled by kv lang bc it's not explicit enough for update loop.
    def update(self, game):
        r = random.randint
        offset = game.camera.offset

        # Graphical Loop
        self.canvas.clear()
        for decal in self.decals:

            if decal['lifetime'] > self.duration:
                self.decals.remove(decal)
                continue
            draw_pos = Vector(*decal['center']) + Vector(*offset)

            g = self.get_graphics(draw_pos)
            self.canvas.add(Color(rgba=decal['color']))
            self.canvas.add(g)
            decal['lifetime'] += 1
        self.canvas.add(Color())

    def get_graphics(self, center):
        pos = Vector(*center) - (Vector(*self.decal_size) / 2) # Convert center to pos.
        g = Rectangle(source=self.image, pos=pos, size=self.decal_size)
        return g

    def generate_color(self):
        r = random.random
        return (r(), r(), r(), 1)

    def add_decal(self, center):
        config = {
            'center': center, 
            'color': self.generate_color(), 
            'lifetime': 0
            }
        self.decals.append(config)

class Game(Screen):

    def __init__(self, **kwargs):
        super(Game, self).__init__(**kwargs)

        self.update_loop = Clock.schedule_interval(self.update, 1/60)

        self.game_map.initialize('galaxy')
        self.map_size = self.game_map.size

        self.player = char.create_hero((100, 100))

        self.wave_manager = WaveManager()

        self.e_container.add_entity(self.player)
        self.camera = camera.Camera(camerafunc=camera.center_cam, 
                                    anchor=self.user_interface.right_stick.pos,
                                    center=self.player.center) # This line does not seem to do anything.

        self.debug = Label(pos=(400, 200))
        self.add_widget(self.debug)

    def update(self, dt):
        #print(Clock.get_rfps())
        self.camera.update(self)
        self.game_map.update(self)
        self.e_container.update(self)
        self.wave_manager.update(self)
        self.user_interface.update(self)

        self.decal_engine.update(self)

        self.debug.text = self.player.components['Action'].state

    # TODO: Cancel update loop while in other screens.
    # Calls level up from parent, which knows about the levelup screen.
    def level_up(self):
        self.update_loop.cancel()
        self.parent.current = 'lvlup'

    def game_over(self): # Called from player.
        self.update_loop.cancel()
        self.parent.game_over()

class LevelUpScreen(Screen):

    def on_touch_up(self, touch, **kwargs):
        Clock.schedule_once(self.parent.game.update_loop, self.parent.transition.duration) # Restarts update loop, put this before transition or risk memes.
        self.parent.current = 'game'

# TDS: Top Down Shooter
class TDSApp(App):

    def build(self):
        SM = ScreenManagement()

        #game = Game(name='game')
        #level_up = LevelUpScreen(name='lvlup')

        #update_loop = Clock.schedule_interval(game.update, 1/60)

        #SM.add_widget(game)
        #SM.add_widget(level_up)

        #SM.current = 'game'
        return SM
        
if __name__ == '__main__':
    TDSApp().run()
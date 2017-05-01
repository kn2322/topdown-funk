import kivy
kivy.require('1.9.1')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, FadeTransition, RiseInTransition, SlideTransition, Screen
from kivy.animation import Animation
from kivy.graphics import Rectangle, Color, PushMatrix, PopMatrix, Scale
from kivy.core.image import Image as CoreImage
from kivy.core.text.markup import MarkupLabel
from functools import partial
from utilfuncs import difference, circle_collide, label_markup
import camera
import chardata as char
import userinterface
import mapinfo
from abilitydata import Cooldown, DamageInfo
from constants import UPDATE_RATE
from kivy.vector import Vector
from math import hypot # Used in entity container
import random
from itertools import combinations, product
import copy

Builder.load_string("""
#: kivy 1.9.1

<Label>
    #font_name: 'Times New Roman'

<TitleScreen>
    on_touch_up:
        root.manager.start_signal()
    Label:
        text: 'PP game'
        font_size: '48sp'

<LevelUpScreen>
            
<GameOverScreen>
    background: bg
    txt: txt
    text_y: -400

    Image:
        id: bg
        anim_delay: 0.15
        color: (0.5, 0.5, 0.5, 1)
        source: 'assets/misc/harambe.jpg'

    Label:
        id: txt
        pos: 0, root.text_y
        #text: 'REDACTED has blessed you with the power of [i][b]Growth Mindset[/b][/i], its uncanny its uncanny resemblance with Adolf Hitler fills you with determination.'
        text: 'Something something died for your sins.'
        #'You have been visited by [i]The Spooky Meme Man[/i], thank Harambe in 5 seconds or never get 7 for achievement grades again.'
        markup: True
        text_size: self.width / 1.5, None
        font_size: '24sp'
        halign: 'center'   

""")

#Window.size = (160, 90)


class ScreenManagement(ScreenManager):
    
    def __init__(self, **kw):
        super(ScreenManagement, self).__init__(**kw)
        self.transition = FadeTransition(duration=.8) # SlideTransition has a bug that makes the new screen black, so is not used.
        
        self.title = TitleScreen(name='title')
        self.game = Game(name='game')
        self.lvlup = LevelUpScreen(name='lvlup')
        self.gameover = GameOverScreen(name='gameover')
        self.add_widget(self.title)
        self.add_widget(self.game)
        self.add_widget(self.lvlup)
        self.add_widget(self.gameover)
        self.paused = False

        self.current = 'title'

    def start_signal(self):
        self.current = 'game'

    def to_title(self):
        self.current = ' title'

    def level_up(self, *args):
        self.current = 'lvlup'

    def game_over(self, *args): # Called from game.
        self.current = 'gameover'
        #self.__init__()

    def restart(self, *args):
        self.game.restart()
        self.current = 'game'

    def pause(self, *args):
        # Handles both pausing and unpausing, unpause() removes pause graphic.

        """if not self.paused and self.game.update_loop is None:
            # If game is currently being unpaused.
            pass"""

        if self.paused:
            # Unpauses.  
            self.game_start()
            self.paused = False

        else:
            # Game is paused.
            with self.canvas:
                Color(rgba=(0, 0, 0, 0.5))
                Rectangle(size=self.size, pos=self.pos)
            self.paused = True

            #self.canvas.add()
            #self.canvas.add()

            """txt = Label(size=self.size,
                        pos=self.pos,
                        text='Tooty Frooty Go Get That Booty')

            self.add_widget(txt)"""
            """self.add_widget(self.pause_screen)
            self.pause_screen.activate()"""

    def unpause(self, *args):
        # Removes paused graphic.

        for i in self.canvas.children:
            if type(i) in (Color, Rectangle):
                self.canvas.remove(i)
        """self.paused = False
        self.game_start()"""
        

    """def on_touch_down(self, touch):
        print("DOWN")
        if self.paused:
            self.unpause()
        # Workaround for activating touch for all children.
        for i in list(self.walk())[1:]:
            i.on_touch_down(touch)
        
        if self.paused:
            self.unpause()"""

    def game_start(self, *args): # Part of unpausing.
        if self.pause_screen in self.children:
            # Workaround for the pause screen deactivation.
            self.remove_widget(self.pause_screen)
        d = 0.2 if self.paused else self.transition.duration
        Clock.schedule_once(self.game.game_start, d)
        Clock.schedule_once(self.unpause, d)
        #self.current = 'game'

class TitleScreen(Screen):
    pass

# Container widget for all game entites, so they can be referenced by the game.
# Also the collision detector

class Entities: # Data container for entities

    # Lists containing all the entities in any category,
    # Any entity only needs to know its name, and if an ability affects a category of other entities.

    # players includes all hero names.
    players = ['test_hero']
    # name, batch size, creation function.
    # HAVE MERCY, MOVE THIS TO WAVE ENGINE WHERE IT BELONGS.
    enemies = [
                ['Riot Police', 4, char.create_riot_police],
                ['Siner', 3, char.create_siner],
                ['Lancer', 2, char.create_lancer]
                ]
    projectiles = ['test_projectile']
    terrain = ['Pillar']
    powerups = ['TestPowerup']

class EntityContainer(Widget):

    def __init__(self, game, **kwargs):
        super(EntityContainer, self).__init__(**kwargs)
        en = Entities

        # This is called 'u wot m8 design'
        self.players = en.players
        self.enemies = [i[0] for i in en.enemies]
        self.projectiles = en.projectiles
        self.terrain = en.terrain
        self.powerups = en.powerups
        self.all_entites = set(self.players + self.enemies + self.projectiles + self.terrain + self.powerups)

        self.game = game # Terribad object oriented design with Kevin.
        self.game_map = game.game_map

        """self.partition_size = 50

        gm = self.game_map
        x = (gm.width // self.partition_size) + 1
        y = (gm.height // self.partition_size) + 1
        self.grid = [[[]] * y for _ in range(x)]"""

        #self.clock_count = 0 # arbitrary clock count

    # To be used in main loop with 'for i in children: if condition, destroy'
    # Additionally gold, exp, and such can be awarded here
    def update(self, game, *args):

        #if self.clock_count % 2 == 0:
        #self.children = sorted(self.children, key=lambda entity: entity.y) # Sort by y position for drawing.
        self.check_collision(game)
        #self.clock_count += 1
        #self.clock_count %= 2
        
        for entity in self.children: # Consider changing to update all components of one type.
            entity.update(game)

    # Interface for adding entities, includes sanity checks
    def add_entity(self, entity):
        if entity.name not in self.all_entites:
            raise ValueError('The entity name {} does not exist.'.format(entity.name))

        if entity.name in self.enemies:
            def oc():
                self.add_widget(entity)
            self.game.decal_engine.add_decal(entity.center, 
                'spawn_indicator', 
                on_complete=oc)
        else:
            self.add_widget(entity)

    # Used in check collision to move to nearest location inside of the map.
    def out_of_map_handler(self, entity): # Should be more static method.
        gm = self.game_map

        # Mapborder falls off.
        # can_collide_wall and can_fly are both used to determine behaviour.
        if 0 > entity.right or entity.x > gm.right or \
            0 > entity.top or entity.y > gm.top:

            if not entity.components['Physics'].can_fly: # If entity can fall off, death animations.
                dmg = DamageInfo(self, 1337, 'absolute')
                """if entity.name in self.players:
                    # Temporary solution as there is no proper game over, only regain hp on death, prevents crashing.
                    entity.receive_damage(dmg)
                    entity.center = gm.center
                    entity.velocity = Vector(0, 0) # Remove displacement sliding."""
                if True:
                    def death(entity):
                        entity.receive_damage(dmg)

                    if not entity.falling:#entity.name not in self.players:
                        entity.original_size = entity.size[:] # Disgusting workaround temp.
                        entity.original_v_multiplier = entity.velocity_multiplier
                        fall = Animation(size=(1,1), step=1/60, duration=1)
                            
                        entity.velocity_multiplier = 0
                        
                        if entity.name in self.players:
                            def rebirth(entity): # Temp.
                                entity.size = entity.original_size[:]
                                #entity.size = original_size
                                entity.velocity_multiplier = entity.original_v_multiplier
                                entity.receive_damage(dmg)
                            fall.on_complete = rebirth
                        else:
                            fall.on_complete = death

                        fall.start(entity)
                        entity.falling = True
                    else: # Insta kills player to avoid their attributes permanently changing upon game restart.
                        death(entity)

            # Removes entities that fly too far away.
            elif (not -500 < entity.x < gm.right + 500) or (not -500 < entity.y < gm.top + 500):
                self.remove_widget(entity)

    def move_to_mapborder(self, entity): # Called in out_of_map_handler.
        gm = self.game_map

        # Map border are walls.
        hit = False # If collided with wall.
        #print(gm.size)
        if entity.components['Physics'].can_collide_wall: # For things that can go out of map.
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


    # Collision resolution. USED IN CHECK_COLLISION
    def resolve(self, a, b):

        depth = circle_collide(a, b)

        if not depth:
            return None

        diff = difference(a.center, b.center)
        #depth = (a.width + b.width) / 2 - hypot(*diff) # Overlapping distance, sum of radii - distance.
        #if depth <= 0: # Important to prevent moving by negative depth.
            #return None

        if a.components['Physics'].can_collide(a, b, self) and b.components['Physics'].can_collide(b, a, self):
            
            # Resolves the physics portion of the collision.
            min_pv = Vector(*diff).normalize() * depth / 2 # Min penetrating vector from a's pov.
                    
            a.pos = Vector(*a.pos) - min_pv
            b.pos = Vector(*b.pos) + min_pv
            
        # Collide for both entities MUST be called, since collision pairs shouldn't be repeated.
        a.components['Action'].collide(a, b, self)
        b.components['Action'].collide(b, a, self)

    def get_cell(self, x, y): # of a point on the map, used in CHECK_COLLISION.
        gm = self.game_map
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

    def add_to_grid(self, entity):
        gm = self.game_map
        min_cell = self.get_cell(entity.x, entity.y)
        max_cell = self.get_cell(entity.x + entity.width, entity.y + entity.height)

        cell_range_x = range(min_cell[0], max_cell[0]+1)
        cell_range_y = range(min_cell[1], max_cell[1]+1)

        self.grid[0][0].append(entity)

        """for x in cell_range_x:
            for y in cell_range_y:
                self.grid[x][y].append(entity)"""

    # Does the collision
    def check_collision(self, game):

        gm = self.game_map

        """for idx, a in enumerate(self.children):
            self.move_to_mapborder(a)

            #to_check = (b for b in self.children[idx+1:] if a.components['Action'].can_collide(a, b, self) and a.components['Physics'].can_collide(a, b, self))

            for b in self.children[idx+1:]:
                self.move_to_mapborder(b)
                self.resolve(a, b)"""
        for a, b in combinations(self.children, 2): # Combinations solution.
            self.out_of_map_handler(a)
            self.out_of_map_handler(b)
            self.resolve(a, b)

        """checked_pairs = [] # Attempt at spatial partitioning.
        to_be_removed = []

        for column, _ in enumerate(self.grid): # x is the column number in the 2d list.

            for row, cell in enumerate(_):

                if len(cell) == 0:
                    continue

                size = (self.partition_size, self.partition_size)
                pos = (column * self.partition_size, row * self.partition_size)

                # cell bounding box
                cell_bb = Widget(size=size, pos=pos)

                for idx, a in enumerate(cell):
                    if not cell_bb.collide_widget(a):
                        to_be_removed.append(a)
                        continue
                    self.move_to_mapborder(a)

                    for b in cell[idx+1:]: # Brute forcing with idx+1
                        if not cell_bb.collide_widget(b):
                            to_be_removed.append(b)
                            continue
                        self.move_to_mapborder(b)

                        if set((a, b)) not in checked_pairs:
                            self.resolve(a, b)
                            checked_pairs.append(set((a, b)))"""

        """for column, _ in enumerate(self.grid): # x is the column number in the 2d list.

            for row, cell in enumerate(_):

                if len(cell) == 0:
                    continue

                for i in to_be_removed:
                    if i in cell:
                        cell.remove(i)
                        #print(i.name)
                        self.add_to_grid(i)"""                   
        
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

    def clear(self, *args): # Except players.
        for e in self.children:
            if e.name in self.enemies:
                e.hp -= 1337 # Kills EVERYTHING HAHAHAHAHAHAH.

class WaveManager: # Handles generating waves and spawning enemies.

    def __init__(self):
        # See Entities class.
        self.enemies = Entities.enemies
        self.batch_ref = [3, 3, 3, 4, 4, 4, 5, 5, 5, 5]#[i for _ in range(2) for i in range(2, 10)] # Number of batches in each wave, is an iterable. E.g. this one goes up to 20 waves.
        self.wave = -1 # So first wave is batch_ref[0]

        self.spawn_funcs = []

        # Time in between waves
        self.spawn_delay = Cooldown(2)
        self.spawn_delay.activate()

        # Spawn timer widget
        self.counter = Label(font_size='81sp', markup=True)

        #self.siner_directions = [] # record of already spawned siners. Not used because of random directions.

        # siner_maxcd is the spawn delay between each siner.
        self.siner_maxcd = 0.5 * UPDATE_RATE # Different cd system that's slightly saner. (CD object is terribad)
        self.siner_cds = []

    def get_names(self): # A list containing all enemy names only.
        return [i[0] for i in self.enemies]

    def update(self, game):
        ec = game.e_container
        # Inefficient as it checks every update loop, checks for all enemies dead.
        for i in ec.children:
            if i.name in ec.enemies:
                break
        else:
            # Spawn delay.
            if self.spawn_delay.current <= 0:
                if self.counter in game.children:
                    game.remove_widget(self.counter)
                    def spawn_delay(*args):
                        self.spawn_delay.activate()
                    Clock.schedule_once(spawn_delay, 5) # To workaround spawn indicator triggering next wave.
                    self.next_wave(game)
            else: # Spawn indicator number info
                markup = ['[i]', '[color=#FF0000]'] # List of markup text for the output text.
                # Rounds up.
                display_num = int(self.spawn_delay.current + 1)
                text = str(display_num)
                for m in markup:
                    text = label_markup(text, m)
                self.counter.text = text
                if self.counter not in game.children:
                    game.add_widget(self.counter)

                self.spawn_delay.time_step()

        temp = []
        while self.siner_cds: # Nice while loop.
            cd, num_left, info = self.siner_cds.pop(0) # Spawn siners, info is args for spawning
            if num_left > 0 and cd <= 0:
                ec.add_entity(self.enemies[1][2](*info)) # The accessing is not obvious, refers to siners.
                cd = self.siner_maxcd
                num_left -= 1
            elif cd > 0:
                cd -= 1
            elif num_left == 0:
                continue
            temp.append([cd, num_left, info])
        self.siner_cds = temp

    def next_wave(self, game):
        self.wave += 1
        game_map = game.game_map
        ec = game.e_container
        # Types of enemies in wave, will be a function.
        chosen = self.enemies # Provisional as there is only 1 enemy type

        # Generate enemy lists.
        enemy_list = []
        se = self.enemies
        # TODO: Competent scheduling based on frames for varied time spawning in one wave.
        # Specifically designed waves, temporary before something else comes up.
        if self.wave == 0:
            for _ in range(3):
                enemy_list.append(se[0])
        elif self.wave == 1:
            for i in [se[2], se[2], se[0]]:
                enemy_list.append(i)
        elif self.wave == 2:
            for i in [se[0], se[0], se[1]]:
                enemy_list.append(i)
        elif self.wave == 3:
            for i in [se[1], se[1], se[2], se[2]]:
                enemy_list.append(i)
        elif self.wave == 4:
            for i in [se[0], se[2], se[2], se[2]]:
                enemy_list.append(i)
        elif self.wave == 5:
            for i in [se[1], se[1], se[1], se[0]]:
                enemy_list.append(i)
        else:
            enemy_list = [random.choice(chosen) for _ in range(self.batch_ref[self.wave])]
        
        for en in enemy_list:
            name, batch_size, func = en

            if name == 'Siner':
                spawn_center = [0, game_map.center_y] # Spawn Location.
                y_direction = random.uniform(-1, 1) #random.choice([-1, 1]) # +sin(x) or -sin(x)
                #if y_direction == 0: # multiply by 0.
                    #y_direction = 0.01

                #to_spawn = [func(pos, y_direction=y_direction) for _ in range(batch_size)]
                
                print(y_direction)
                """spawn = lambda *args: ec.add_entity(
                    func(spawn_center, y_direction)
                    )"""
                #def spawn(func, *args):
                    #ec.add_entity(func(*args))

                """def spawn():
                    ec.add_entity(func(spawn_center, y_direction))
                    print('spawned')"""

                #print(deepcopy(spawn) is spawn)

                #s = deepcopy(spawn)

                #j = id(s)

                #self.spawn_funcs[id(s)] = s

                #s = partial(spawn, func, spawn_center, y_direction)

                """for i in range(batch_size): # Replaced with new spawning system.
                    entity = func(spawn_center, y_direction)
                    delay = i * 30 # frames in delay
                    # Preventing delay of 0 being scheduled is PARAMOUNT.
                    if delay == 0:
                        #spawn(func, spawn_center, y_direction)
                        #spawn()
                        ec.add_entity(entity)
                    else:
                        # Problematic.
                        #s = partial(ec.add_entity, spawn)
                        self.sane_clock(entity, 1/UPDATE_RATE * delay, ec)
                        #Clock.schedule_once(self.spawn_funcs[j], 1/UPDATE_RATE * delay)
                """
                cd = 0
                num_left = batch_size
                info = [spawn_center, y_direction]
                self.siner_cds.append([cd, num_left, info])

            else:#if name == 'Riot Police':
                r = random.uniform
                gm = game_map
                # bounds is corner 100 x 100 squares on the map, where enemies can spawn.
                bounds = [
                            [(50, 50), (150, 150)], # bot left 
                            [(50, gm.top-150), (150, gm.top-50)], # top left
                            [(gm.right-150, 50), (gm.right-50, 150)], # bot right
                            [(gm.right-150, gm.top-150), (gm.right-50, gm.top-50)] # top right
                            ]
                spawn_center = random.choice(bounds)
                # NOTE: The list() here is crucial to prevent an immutable valueerror.
                shuffled = list(zip(*spawn_center)) # Inverts the center to make it bounds_x and bounds_y, for ease of looping.
                #spawn_center = [r(0, i) for i in game_map.size]
                
                for i in range(batch_size):
                    p = [random.uniform(a, b) for a, b in shuffled]
                    #pos = [i + random.randint(-100, 100) for i in spawn_center]
                    e = func(p)
                    ec.add_entity(e)
                    #self.sane_clock(e, random.uniform(0.01, 1), ec)

    # Visual Indicator for entity spawning, TODO.œ
    #def pre_spawn(self, entity, delay=1):
    #    Clock.schedule_once()

    def sane_clock(self, obj, time, ec): # Copious amounts of workarounds, not used anymore.
        """#print(func)
        copied = deepcopy(func)
        #print(copied == func)
        def done(dt):
            return copied()
        self.spawn_funcs.append(done)
        a = len(self.spawn_funcs) - 1
        print(a)
        #print(a)
        #self.spawn_funcs[a] = lambda dt: copied()
        Clock.schedule_once(self.spawn_funcs[a], time)"""
        #self.spawn_funcs.append(obj)
        #print(self.spawn_funcs)

        def add(dt): # This function is dark magic, but it works.
            ec.add_entity(obj)

        Clock.schedule_once(add, time)

    # Uses data on likelihood of enemies to appear to generate probs of chosen enemy types to appear.
    # TODO: create data struct for enemy probability modifiers.
    def gen_probability(self, enemies): # Look into static methods is self is not needed.
        return zip([1/len(enemies) for _ in enemies], enemies)

class DecalEngine(Widget): # Modified from graphics component.

    def __init__(self, **kw):
        super(DecalEngine, self).__init__(**kw)
        #self.graphics = None
        self.decals = []
        #self.image = CoreImage('assets/decals/splatter.png')
        #self.duration = UPDATE_RATE * 2
        self.decal_types = {'splash': self.decal_splash, 
                            'spawn_indicator': self.decal_spawn_indicator}

    """def get_method(self, method): # interface for getting the right decal
        #self.decal_types = {'splash': self.decal_splash, 'spawn_indicator': None}
        if method == 'splash':
            return self.decal_splash
        elif method == 'spawn_indicator':
            return None"""

    # Not handled by kv lang bc it's not explicit enough for update loop.
    def update(self, game):
        r = random.randint
        offset = game.camera.offset

        # Graphical Loop
        self.canvas.clear()
        for decal in self.decals:

            if decal['lifetime'] > decal['duration']:
                if decal['on_complete']: # Event based garbage.
                    decal['on_complete']()
                self.decals.remove(decal)
                continue

            color = decal['color']
            size = decal['size']
            if decal['name'] == 'splash':
                # Fade away function if decal should fade.
                color[-1] = -(decal['lifetime'] / decal['duration']) + 1
            elif decal['name'] == 'spawn_indicator':
                ratio = decal['lifetime'] / decal['duration']
                #size = Vector(size) - (Vector(size) * ratio) # Decreasing
                size = Vector(size) * ratio # Increasing

            # TODO: Add mechanism to only draw if decal is on screen.
            # Adjust to camera.
            draw_pos = Vector(*decal['center']) + Vector(*offset)

            # Adjust center position to x1, y1 based on size.
            draw_pos -= Vector(*size) / 2

            self.canvas.add(Color(rgba=color))
            g = Rectangle(
                    texture=decal['image'].texture, 
                    pos=draw_pos, 
                    size=size)
            self.canvas.add(g)
            #decal['color'][-1] -= 0.5 / UPDATE_RATE # Fade out, TODO: Implement these for individuals.
            decal['lifetime'] += 1

    """def get_graphics(self, center):
        size = Vector(*self.image.size).normalize() * 100 # multiplier is width of decal.
        pos = Vector(*center) - Vector(*size) / 2 # Convert center to pos.
        g = Rectangle(texture=self.image.texture, pos=pos, size=size)
        return g"""

    """def generate_color(self):
        r = random.random
        return [r(), r(), r(), 1]"""

    def add_decal(self, center, decal_type, on_complete=None): # decal_type is string.
        # Dynamically gets the decal tm.
        method = self.decal_types[decal_type]
        if method == None:
            raise NameError('decal type "{}" was not found.'.format(decal_type))
        config = method(center, on_complete=on_complete)
        self.decals.append(config)

    # Below here are specific decal infos.

    def decal_splash(self, center, on_complete=None): # Use this one as an example.
        r = random.random
        config = {
            'name': 'splash',
            'center': center, 
            'color': [r(), r(), r(), 1], 
            'duration': 3 * UPDATE_RATE,
            'image': CoreImage('assets/decals/decal1.png'),
            'size': (100, 100),
            'lifetime': 0,
            'on_complete': on_complete
            }
        return config

    def decal_spawn_indicator(self, center, on_complete=None):
        r = random.random
        config = {
            'name': 'spawn_indicator',
            'center': copy.deepcopy(center), # copy to avoid kivy property binding.
            'color': [r(), r(), r(), 1], 
            'duration': 1 * UPDATE_RATE,
            'image': CoreImage('assets/decals/decal3.png'),
            'size': (50, 50),
            'lifetime': 0,
            'on_complete': on_complete
            }
        return config    

class Game(Screen):

    def __init__(self, **kwargs):
        super(Game, self).__init__(**kwargs)



        # The drawing order.
        self.game_map = mapinfo.Map('galaxy', size_hint=(None, None))
        self.decal_engine = DecalEngine()
        self.e_container = EntityContainer(self)
        self.user_interface = userinterface.UI()

        for i in [self.game_map, self.decal_engine, self.e_container, self.user_interface]:
            self.add_widget(i)

        self.paused = False # self explanatory.
        self.pause_text = Label(size=self.size,
                                pos=self.pos,
                                font_size='48sp',
                                text='[i][color=#801dab]Tooty Frooty go get that booty[/i][/color]',
                                markup=True)

        self.map_size = self.game_map.size # Kind of redundant, since game_map is already an instance variable.

        # Pillars.
        x_locations = self.map_size[0] * 0.3, self.map_size[0] * 0.7
        y_locations = self.map_size[1] * 0.3, self.map_size[1] * 0.7
        for pos in product(x_locations, y_locations):
            self.e_container.add_entity(char.create_pillar(pos))
        # Map corner pillars.
        m = self.game_map

        size = Vector(128, 128)
        half = size / 2
        #corners = (m.x-half.x, m.y-half.y), (m.x+half.x, m.y-half.y), (m.x-half.x, m.y+half.y),\
                    #(m.x+m.width+half.x, m.y-half.y), (m.x+m.width+half.x, m.y+half.y), (m.x+m.width-half.x, m.y-half.y),\
                    #(m.x-half.x, m.y+m.height+half.y), (m.x-half.x, m.y+m.height-half.y), (m.x+half.x, m.y+m.height+half.y)
                    #(m.x+m.width, m.y+m.height)

        """[(m.x, m.y), 
                    (m.x+m.width, m.y), 
                    (m.x, m.y+m.height), 
                    (m.x+m.width, m.y+m.height)]:"""

        #for pos in corners:
            #self.e_container.add_entity(char.create_pillar(pos, size=size))

        # Test powerups.
        self.e_container.add_entity(char.create_powerup((300, 300)))

        self.player = char.create_hero(self.game_map.center)

        self.wave_manager = WaveManager()

        self.e_container.add_entity(self.player)
        self.camera = camera.Camera(camerafunc=camera.center_cam, 
                                    anchor=self.user_interface.right_stick.pos,
                                    center=self.player.center) # This line does not seem to do anything.

        # Debug text stuff.
        self.debug = Label(pos=(300, 250))
        self.debug2 = Label(pos=(300, 200))
        self.debug3 = Label(pos=(200, 200), font_size='48sp')
        self.debug4 = Label(pos=(100, 200), font_size='48sp')
        for i in [self.debug, self.debug2, self.debug3, self.debug4]:
            self.add_widget(i)

        # CONSTANTS, more or less
        self.player_spawn_center = self.game_map.center

        self.game_start() # Activate update loop.

    def update(self, dt):
        #print(Clock.get_rfps())
        self.camera.update(self)
        self.game_map.update(self)
        self.e_container.update(self)
        self.wave_manager.update(self)
        self.user_interface.update(self)

        self.decal_engine.update(self)

        self.debug.text = self.player.components['Action'].state
        self.debug2.text = str(len(self.e_container.children)) + ' ' + str(self.player.components['Action'].get_value(self.player, 'velocity_multiplier'))
        fps = Clock.get_rfps()
        self.debug3.text = str(fps)
        self.debug4.text = str(self.player.components['Action'].exp)


    def game_start(self, *args):
        if self.paused:
            # Unpauses, and removes paused graphics.
            self.remove_widget(self.pause_text)

            for i in self.canvas.children:
                if type(i) in (Color, Rectangle):
                    self.canvas.remove(i)

            self.paused = False
        self.update_loop = Clock.schedule_interval(self.update, 1/UPDATE_RATE)

    # TODO: Cancel update loop while in other screens.
    # Calls level up from parent, which knows about the levelup screen.
    def level_up(self, *args):
        self.update_loop.cancel()
        self.parent.level_up()

    def pause(self, *args):
        self.update_loop.cancel()
        # Game is paused.
        with self.canvas:
            Color(rgba=(0, 0, 0, 0.5))
            Rectangle(size=self.size, pos=self.pos)
        self.add_widget(self.pause_text)
        self.paused = True

    def on_touch_down(self, touch, *args):
        if self.paused:
            # Unpauses upon touch anywhere.
            self.game_start()
        else:
            for wid in list(self.walk())[1:]:
                # Hack for letting this widget have on_touch_down, activates all children's touches.
                wid.on_touch_down(touch, *args)


    def game_over(self, player, *args): # Called from player.
        self.update_loop.cancel()
        print('game over')
        self.manager.game_over(player)

    def restart(self, *args): # Resets game.
        self.e_container.clear() # Clears all non player entities.
        self.player.falling = False
        self.player.hp = self.player.max_hp # Restore health.
        self.player.velocity = Vector(0, 0) # Remove velocity.
        self.wave_manager.wave = -1 # Reset wave count.
        self.player.center = self.player_spawn_center # Reset pos.
        self.game_map.reset() # Resets map.
        self.game_start()
        

class LevelUpScreen(Screen):

    def __init__(self, **kwargs):
        super(LevelUpScreen, self).__init__(**kwargs)
        self.rising_text = Animation(y=0, duration=2, t='out_bounce') # t is the transition, bouncy for meme value.

    def on_touch_up(self, touch, **kwargs):

        """#def game_start(dt):
            #self.parent.game.update_loop = Clock.schedule_interval(self.parent.game.update, 1/UPDATE_RATE)

        game_start = self.parent.game.game_start
        
        Clock.schedule_once(game.game_start, self.parent.transition.duration) # Restarts update loop, put this before transition or risk memes.
        self.parent.current = 'game'"""
        self.parent.game_start()

    def on_pre_enter(self):
        self.rising_text.start(self.txt)
    
    def on_leave(self):
        self.rising_text.cancel(self.txt) # Stop the animation before leaving
        self.txt.y = -400

class PauseScreen(Button):
    # Not being used.

    def activate(self):
        self.size = self.parent.size
        self.pos = self.parent.pos
        with self.canvas:
            Color(rgba=(0, 0, 0, 0.5))
            Rectangle(size=self.size, pos=self.pos)

    def on_touch_up(self, touch):
        self.parent.restart()

class GameOverScreen(Screen):

    def __init__(self, **kwargs):
        super(GameOverScreen, self).__init__(**kwargs)
        self.rising_text = Animation(y=0, duration=2, t='out_bounce') # t is the transition, bouncy for meme value.
    
    def on_touch_down(self, touch, *args):
        self.manager.restart()

    def on_pre_enter(self):
        self.rising_text.start(self.txt)
    
    def on_leave(self):
        self.rising_text.cancel(self.txt) # Stop the animation before leaving
        self.txt.y = self.text_y

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
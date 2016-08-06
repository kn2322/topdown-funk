import kivy
kivy.require('1.9.1')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from functools import partial
from utilfuncs import difference, get_direction, circle_collide
import camera
import abilitydata
import chardata as char
import userinterface
import mapinfo
from kivy.vector import Vector

Builder.load_string("""
#: kivy 1.9.1


<Game>
    game_map: game_map
    e_container: container
    user_interface: user_interface

    Map:
        id: game_map

    EntityContainer:
        id: container
        size: 1, 1

    UI:
        size: root.size
        id: user_interface

""")

Window.size = (1136, 640)

# Container widget for all game entites, so they can be referenced by the game.
# Also the collision detector
class EntityContainer(Widget):

    # Lists containing all the entities in any category.
    # So the entity only needs to know its name, and if xxx in category is used.

    # players includes all hero names.
    players = ['test_hero']
    enemies = ['Riot Police']
    projectiles = ['test_projectile']

    # Derived set of all entities.
    all_entites = set(players + enemies + projectiles)

    def __init__(self, **kwargs):
        super(EntityContainer, self).__init__(**kwargs)
    
    # To be used in main loop with 'for i in children: if condition, destroy'
    # Additionally gold, exp, and such can be awarded here
    def update(self, game, *args):

        self.check_collision(game.map_size)
        
        for entity in self.children:
            entity.update(game)

    # Interface for adding entities, includes sanity checks
    def add_entity(self, entity):
        if entity.name not in self.all_entites:
            raise ValueError('The entity name {} does not exist.'.format(entity.name))

        self.add_widget(entity)

    # Does the collision
    def check_collision(self, map_size):
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
                    """
                    while abs(entity.x - other.x) < entity.width + other.width:
                        entity.move(Vector(entity.pos) + vx, map_size)
                        other.move(Vector(other.pos) - vx, map_size)

                    while abs(entity.y - other.y) < entity.height + other.height:
                        entity.move(Vector(entity.pos) + vy, map_size)
                        other.move(Vector(other.pos) - vy, map_size)
                    """

                    entity.collide(other, self)
                    other.collide(entity, self)

class Game(Widget):

    def __init__(self, **kwargs):
        super(Game, self).__init__(**kwargs)

        self.game_map.initialize('galaxy')
        self.map_size = self.game_map.size

        self.player = char.create_hero((100, 100))
        self.player.assign_util_ability(abilitydata.SuperSpeed(0))

        self.e_container.add_entity(self.player)
        self.camera = camera.Camera(Window.size, camera.center_cam)

        # For testing before spawn algorithm is done.
        for e in [char.create_riot_police((800, 600)), char.create_riot_police((100, 600))]:
            self.e_container.add_entity(e)


    def update(self, dt):
        self.camera.update(self)
        self.game_map.update(self)
        self.e_container.update(self)
        self.user_interface.update(self)

# TDS: Top Down Shooter
class TDSApp(App):

    def build(self):
        game = Game()
        Clock.schedule_interval(game.update, 1/60)
        return game
        
if __name__ == '__main__':
    TDSApp().run()
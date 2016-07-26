import kivy
kivy.require('1.9.1')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import NumericProperty, ReferenceListProperty
from collections import OrderedDict
from functools import partial
import camera
from utilfuncs import difference, get_direction
import gamedata
import chardata as char
import userinterface
import mapinfo

Builder.load_string("""
#: kivy 1.9.1


<Game>
    game_map: game_map
    left_stick: left_stick
    e_container: container
    user_interface: user_interface
    a1: a1

    Map:
        id: game_map

    EntityContainer:
        id: container
        size: 1, 1

    UI:
        id: user_interface
        LeftStick:
            id: left_stick
            center: 100, 100
        AbilityButton:
            id: a1
            # Testing
            center: root.width - 100, 100
""")

Window.size = (1136, 640)

# Container widget for all game entites, so they can be referenced by the game.
# Also the collision detector
class EntityContainer(Widget):

    # A tree of app -> game -> this container and UI -> entity -> components

    def __init__(self, **kwargs):
        super(EntityContainer, self).__init__(**kwargs)
    
    # To be used in main loop with 'for i in children: if condition, destroy'
    # Additionally gold, exp, and such can be awarded here
    def update(self, game, *args):
        for entity in self.children:
            entity.update(game)

# Window.center is to be changed to starting position on the game map
def create_hero(size=(50, 50), pos=Window.center):
    e = Entity()
    e.size = size
    e.center = pos
    e.hp = 20
    e.components['Input'] = char.HeroInputComponent()
    e.components['Physics'] = char.HeroPhysicsComponent()
    e.components['Graphics'] = char.HeroGraphicsComponent(e)
    e.components['Action'] = char.HeroActionComponent()
    # The add_widget step is not in the function, so it's decoupled.
    return e

class Entity(Widget):

    velocity_x = NumericProperty()
    velocity_y = NumericProperty()
    velocity = ReferenceListProperty(velocity_x, velocity_y)
    hp = NumericProperty()

    def __init__(self, **kwargs):
        super(Entity, self).__init__(**kwargs)
        # 'components' uses a dict so each component can be referenced and extended.
        # Action component is to handle the inputs for ability casting.
        # OrderedDict allows the components to update at the correct order.
        self.components = OrderedDict(
            {'Input': None, 'Physics': None, 'Action': None, 'Graphics': None}
            )
        self.last_pos = 0, 0

    def update(self, game):
        Clock.schedule_once(self.record_pos, -1)
        for name, item in self.components.items():
            if item is None:
                continue
            item.update(self, game)

    def record_pos(self, *args):
        self.last_pos = self.pos
        return None

# Ellipse collision workaround to default axis-aligned bounding box
# Works by finding the distance collision point is using pythag and diference
# This is now redundant, because hypot(*difference()) <= radius is more flexible for testing different things
"""def in_ellipse_checker(center, touch, radius):
    if hypot(*difference(center, touch)) <= radius:
        return True
    return False
"""

class Game(Widget):

    def __init__(self, **kwargs):
        super(Game, self).__init__(**kwargs)

        self.game_map.initialize('galaxy')
        self.map_size = self.game_map.size

        self.player = create_hero()
        self.a1.assign_function(gamedata.SuperSpeed())

        self.right_stick = userinterface.RightStick()
        self.user_interface.add_widget(self.right_stick)

        self.e_container.add_widget(self.player)
        self.e_container.add_widget(create_hero())
        self.camera = camera.Camera(Window.size, camera.center_cam)

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
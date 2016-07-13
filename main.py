import kivy
kivy.require('1.9.1')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import NumericProperty, BooleanProperty, ObjectProperty, ReferenceListProperty
from math import atan2, degrees, radians, inf, sin, cos, tan, hypot
from functools import partial

Builder.load_string("""
#: kivy 1.9.1

<Game>
    entity_container: entity_container
    left_stick: left_stick

    EntityContainer:
        id: entity_container
        size: root.size
        pos: root.pos
    LeftStick:
        id: left_stick
        center: 100, 100
    AbilityButton:
        # Testing
        cool_down: 6
        center: root.width - 100, 100

<LeftStick>
    moving_stick: moving

    Widget:
        id: station
        size: 100, 100
        center: root.center
        canvas:
            Ellipse:
                size: self.size
                pos: self.pos

    Widget:
        size: moving.size
        center: root.center
        canvas:
            Color:
                rgba: 0, 0, 1, .5
            Ellipse:
                size: self.size
                pos: self.pos

    Widget:
        id: moving
        # args[1] is the touch object, important.
        on_touch_down: root.touch_handler(args[1])
        on_touch_move: root.touch_callback(args[1])
        on_touch_up: root.touch_revert()
        center: root.center
        size: 40, 40
        canvas:
            Color:
                rgba: 0, 0, 1, 1
            Ellipse:
                size: self.size
                pos: self.pos

<AbilityButton>
    cd_indicator: cd_indicator

    Widget:
        on_touch_down: root.touch_handler(args[1])
        size: root.size
        center: root.center
        canvas:
            Color:
                rgba: 0, 0, 1, 1
            Ellipse:
                size: self.size
                pos: self.pos
    Widget:
        id: cd_indicator
        size: 1, 1
        center: root.center
        canvas:
            Color:
                # First comparison is so the observer pattern doesn't go before time_step() in making the size of the circle tiny
                # Instead of seeing the full circle from the end of the previous call
                # size is not done using observer pattern bind
                a: 0 if root.cool_down == root.current_cd or root.current_cd <= 0 else .3
            Ellipse:
                size: self.size
                pos: self.pos
""")

Window.size = (800, 600)

# Container widget for all game entites, so they can be referenced by the game.
class EntityContainer(Widget):
    
    # To be used in main loop with 'for i in children: if condition, destroy'
    # Additionally gold, exp, and such can be awarded here
    def destroy(self, entity):
        self.remove_widget(entity)

# TODO: Rewrite/fix entity system to be more extensible and follow OOP
# Changed to using components
"""class Entity(Widget):
    # hp, size, ai, in order
    game_entities = {
        'Zombie': (100, 50, None)
        }
    TODO: Determine different attributes of each game entity, inc but not
    limited to the source image, status effect modifiers, speed.
    
    def __init__(self, hp, size, **kwargs):
        super(Entity, self).__init__(**kwargs)
        self.hp = hp
        self.size = size

    def destroy(self):
        pass

class BasePlayer(Entity):
    
    def __init__(self, **kwargs):
        super(BasePlayer, self).__init__(**kwargs)

class TestHero(BasePlayer):

    def __init__(self, **kwargs):
        super(TestHero, self).__init__(**kwargs)

    def move(self):
        pass


class BaseEnemy(Entity):

    def __init__(self, **kwargs):
        super(BaseEnemy, self).__init__(**kwargs)

class Zombie(BaseEnemy):

    def __init__(self, **kwargs):
        super(Zombie, self).__init__(**kwargs)
"""
class Entity(Widget):

    Input = ObjectProperty()
    Physics = ObjectProperty()
    Graphics = ObjectProperty()
    components = ReferenceListProperty()
    velocity_x = NumericProperty()
    velocity_y = NumericProperty()
    velocity = ReferenceListProperty(velocity_x, velocity_y)
    movement_angle = ReferenceListProperty()

    def __init__(self, Input, Physics, Graphics, **kwargs):
        super(Entity, self).__init__(**kwargs)
        for i in [Input, Physics, Graphics]:
            self.i = i
        movement_angle = [0, 0]

    def update(self):
        self.Input.update()
        self.Physics.update()
        self.Graphics.update()


def create_hero():
    entity = Entity(Input=HeroInputComponent(entity))
    return entity

class EmptyComponent:

    def update(self):
        pass

class HeroInputComponent:

    def __init__(self, obj, game):
        self.obj = obj
        self.game = game

    def update(self):
        left_stick = self.game.left_stick
        angle = left_stick.angle
        # TODO: variable speed
        # the decimal is the distance between half and full speed
        #if left_stick.touch_distance > 0.4:

        # The 'ratios' of the x and y velocities in a circle with r of 1
        x = cos(angle)
        y = sin(angle)
        obj.movement_angle = [x, y]

class HeroPhysicsComponent:

    speed_multiplier = NumericProperty

    def __init__(self, obj):
        self.obj = obj
        # Full movement speed, pixel/s/60 updates per second
        self.speed_multiplier = 60/60

    def update(self):
        self.obj.velocity = [i * self.speed_multiplier 
                             for i in self.obj.movement_angle]
        self.obj.x += self.obj.velocity_x
        self.obj.y += self.obj.velocity_y

# deltay/deltax distance calculations
def difference(pos1, pos2):
    return (pos2[0] - pos1[0], pos2[1] - pos1[1])

# Ellipse collision workaround to default axis-aligned bounding box
# Works by finding the distance collision point is using pythag and diference
# This is now redundant, because hypot(*difference()) <= radius is more flexible for testing different things
"""def in_ellipse_checker(center, touch, radius):
    if hypot(*difference(center, touch)) <= radius:
        return True
    return False
"""

class LeftStick(Widget):

    moving_edge = NumericProperty()

    def __init__(self, **kwargs):
        super(LeftStick, self).__init__(**kwargs)
        self.moving_edge = self.height / 2
        # touch_distance will be the touch's distance from center in decimal
        # Used for hero movements
        self.touch_distance = None
        self.angle = 0

    def touch_handler(self, touch):
        # kv doesn't init to reference moving_stick in __init__ (?)
        self.moving_edge = self.height / 2 - self.moving_stick.height / 2
        self.touch_callback(touch)
    
    # For on_touch_move
    # TODO: remove gradient/unecessary components
    def touch_callback(self, touch):
        if touch.x < Window.width / 2:
            delta = difference(self.center, touch.pos)
            self.angle = atan2(delta[1], delta[0])
            # checks for touch collision with the control stick
            if hypot(*difference(self.center, touch.pos)) <= self.moving_edge:
                self.touch_distance = hypot(*difference(self.center, touch.pos)) / self.moving_edge
                self.moving_stick.center = touch.pos
            else:
                self.touch_distance = 1
                # Intense right angle trigonometry
                # Have trust in trig functions. :p
                # Operates on 'triangle' where the moving_edge is the hypotnuse
                x = self.center_x + self.moving_edge * cos(angle)
                y = self.center_y + self.moving_edge * sin(angle)
                self.moving_stick.center = (x, y)
        else:
            self.touch_distance = None
            self.touch_revert()

    # For on_touch_up
    def touch_revert(self):
        self.moving_stick.center = self.center

class AbilityButton(Widget):

    cool_down = NumericProperty()
    current_cd = NumericProperty()
    on_cd = BooleanProperty()

    # Functions to be accepted with *args with tuple which has func and its cd.
    # Purpose: So that the button's behavior is able to be swapped out depending on hero.
    def __init__(self, func=partial(print, 'there is no function'), cool_down=0, **kwargs):
        super(AbilityButton, self).__init__(**kwargs)
        self.func = func
        self.cool_down = cool_down
        self.current_cd = 0
        self.on_cd = False
        
    def assign(self, func, cool_down):
        self.func = func
        self.cool_down = cool_down

    def time_step(self, dt):
        if round(self.current_cd, 3) > 0:
            self.current_cd -= 1/60
            # Function to make the size of cd_indicator grow at constant rates until original size depending on cd
            # The indicator is updated here to allow for more explicit logic instead of observer pattern via kv
            self.cd_indicator.size = tuple(
                -i / self.cool_down * self.current_cd + i for i in self.size
                )
            self.cd_indicator.center = self.center
        else:
            self.current_cd = 0
            self.on_cd = False
            self.cd.cancel()

    def touch_handler(self, touch):
        if  hypot(*difference(self.center, touch.pos)) <= self.height / 2 and \
        not self.on_cd:
            self.func()
            self.current_cd = self.cool_down
            # on_cd is to prevent multiple activations of the button while on cd
            self.on_cd = True
            self.cd = Clock.schedule_interval(self.time_step, 1/60)

class Game(Widget):

    def update(self, dt):
        pass

# TDS: Top Down Shooter
class TDSApp(App):

    def build(self):
        game = Game()
        Clock.schedule_interval(game.update, 1/60)
        return game
        
if __name__ == '__main__':
    TDSApp().run()
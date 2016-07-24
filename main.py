import kivy
kivy.require('1.9.1')

# TODO: Split the main file into different parts for maintainability
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Ellipse, Color
from kivy.properties import NumericProperty, BooleanProperty, ObjectProperty, ReferenceListProperty
from math import atan2, degrees, radians, inf, sin, cos, tan, hypot
from functools import partial
from collections import OrderedDict

Builder.load_string("""
#: kivy 1.9.1

<Game>
    left_stick: left_stick
    right_stick: right_stick
    e_container: container
    user_interface: ui

    EntityContainer:
        id: container
        size: 1, 1

    UI:
        id: ui
        LeftStick:
            id: left_stick
            center: 100, 100
        RightStick:
            id: right_stick      
        AbilityButton:
            # Testing
            cooldown: 6
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
                a: 0 if root.cooldown == root.current_cd or root.current_cd <= 0 else .3
            Ellipse:
                size: self.size
                pos: self.pos

<EntityContainer>

<Entity>
    canvas:
        Ellipse:
            size: self.size
            pos: self.pos
""")

Window.size = (800, 600)

# Container widget for all game entites, so they can be referenced by the game.
class EntityContainer(Widget):

    # A tree of app -> game -> this container and UI -> entity -> components

    def __init__(self, **kwargs):
        super(EntityContainer, self).__init__(**kwargs)
    
    # To be used in main loop with 'for i in children: if condition, destroy'
    # Additionally gold, exp, and such can be awarded here
    def update(self, game, *args):
        for entity in self.children:
            entity.update(game)

class UI(Widget): # Considering to change this into a layout for resolution scaling.
    
    layout = {left}

    def __init__(self, **kwargs):
        super(UI, self).__init__(**kwargs)

    # Updates all ui elements needing updates
    def update(self, game, *args):
        for element in self.children:
            # Catches elements that don't have an update method.
            try:
                element.update(game)
            except AttributeError:
                continue

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

    velocity_x = NumericProperty()
    velocity_y = NumericProperty()
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    def __init__(self, **kwargs):
        super(Entity, self).__init__(**kwargs)
        # 'components' uses a dict so each component can be referenced and extended.
        # Action component is to handle the inputs for ability casting.
        # OrderedDict allows the components to update at the correct order.
        self.components = OrderedDict(
            {'Input': None, 'Physics': None, 'Action': None, 'Graphics': None}
            )

    def update(self, game):
        for name, item in self.components.items():
            if item is None:
                continue
            item.update(self, game)
 
def create_hero(size=(50, 50), pos=Window.center):
    e = Entity()
    e.size = size
    e.center = pos
    e.components['Input'] = HeroInputComponent()
    e.components['Physics'] = HeroPhysicsComponent()
    e.components['Graphics'] = HeroGraphicsComponent()
    e.components['Action'] = HeroActionComponent()
    # The add_widget step is not in the function, so it's decoupled.
    return e

class HeroInputComponent:

    def __init__(self):
        # Same one as the one in left stick, used for reference by physics.
        # This is not encapsulated and decoupled, use caution.
        # Decimal distance of moving stick from border
        self.touch_distance = 0

    def update(self, entity, game):
        left_stick = game.left_stick
        angle = left_stick.angle
        self.touch_distance = left_stick.touch_distance
        # TODO: variable speed
        # The 'ratios' of the x and y velocities in a circle with r of 1.
        x = cos(angle)
        y = sin(angle)
        # Merely tells physics the direction, not the full velocity, which is processed more.
        entity.components['Physics'].direction = [x, y]

class HeroPhysicsComponent:

    def __init__(self):
        self.direction = [0, 0]
        # Pixels/s is the intended value,
        self.speed_multiplier = 200

    def update(self, entity, game):
        if entity.components['Input'].touch_distance <= .2:
            # Ensures the hero does not 'slide'
            entity.velocity = 0, 0
            return None
        # Multiply 'direction' with speed and divide by 60 for updates per second.
        entity.velocity = [i * self.speed_multiplier / 60
                             for i in self.direction]

    # Called in action component to allow 'Postprocessing'.
    def move(self, entity):
        entity.x += entity.velocity_x
        entity.y += entity.velocity_y

class HeroGraphicsComponent:
    
    # Mostly handled by .kv lang
    def update(self, entity, game):
        pass

class HeroActionComponent:
    # On hold while ability ui is being made
    
    def __init__(self):
        # Functions/Objects which contain active effects, their duration,
        self.effects = []

    def update(self, entity, game):
        for effect in self.effects:
            # Have faith in the effects not lingering...
            effect(entity)
        entity.components['Physics'].move(entity)
        print('updated')

# For graphics components, returns the sprite facing direction.
def get_direction(angle):
    if -22.5 < angle <= 22.5:
        return 'right'
    elif 22.5 < angle <= 67.5:
        return 'downright'
    elif 67.5 < angle <= 112.5:
        return 'down'
    elif 112.5 < angle <= 157.5:
        return 'downleft'
    elif 157.5 < angle <= 180 or -180 <= angle < -157.5:
        return 'left'
    elif -157.5 <= angle < -112.5:
        return 'upleft'
    elif -112.5 <= angle < -67.5:
        return 'up'
    elif -67.5 <= angle < -22.5:
        return 'upright'
    else:
        raise ValueError('The angle {} is out of bounds.'.format(angle))

# deltay/deltax distance calculations
# TODO: move this to a 'utils.py' or similar, and import
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
        # touch_distance will be the touch's distance from center in decimal
        # Used for hero movements
        self.touch_distance = 0
        self.angle = 0

    def touch_handler(self, touch):
        # Can't reference moving_stick in __init__ (defined in kv lang)
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
                x = self.center_x + self.moving_edge * cos(self.angle)
                y = self.center_y + self.moving_edge * sin(self.angle)
                self.moving_stick.center = (x, y)
        else:
            self.touch_revert()

    # For on_touch_up
    def touch_revert(self):
        self.touch_distance = 0
        self.moving_stick.center = self.center

# Repeating code...
class RightStick(Widget):

    moving_edge = NumericProperty()

    def __init__(self, **kwargs):
        super(RightStick, self).__init__(**kwargs)
        self.angle = 0

    def touch_handler(self, touch):
        # Can't reference moving_stick in __init__ (defined in kv lang)
        self.moving_edge = self.height / 2 - self.moving_stick.height / 2
        self.touch_callback(touch)
    
    # For on_touch_move
    # TODO: remove gradient/unecessary components
    def touch_callback(self, touch):
        if touch.x > Window.width / 2:
            delta = difference(self.center, touch.pos)
            self.angle = atan2(delta[1], delta[0])
            # checks for touch collision with the control stick
            if hypot(*difference(self.center, touch.pos)) <= self.moving_edge:
                self.moving_stick.center = touch.pos
            else:
                # Intense right angle trigonometry
                # Have trust in trig functions. :p
                # Operates on 'triangle' where the moving_edge is the hypotnuse
                x = self.center_x + self.moving_edge * cos(self.angle)
                y = self.center_y + self.moving_edge * sin(self.angle)
                self.moving_stick.center = (x, y)
        else:
            self.touch_revert()

    # For on_touch_up
    def touch_revert(self):
        self.moving_stick.center = self.center

class AbilityButton(Widget):

    cooldown = NumericProperty()
    current_cd = NumericProperty()
    on_cd = BooleanProperty()

    # Functions to be accepted with *args with tuple which has func and its cd.
    # Purpose: So that the button's behavior is able to be swapped out depending on hero.
    def __init__(self, **kwargs):
        super(AbilityButton, self).__init__(**kwargs)
        self.current_cd = 0
        self.on_cd = False
        
    def assign_function(self, ability):
        self.ability = ability
        self.cooldown = self.ability.cooldown

    def update(self, game):
        # Breaks out of the loop if the ability isn't on cooldown.
        if not self.on_cd:
            return None

        if round(self.current_cd, 3) > 0:
            self.current_cd -= 1/60
            # Function to make the size of cd_indicator grow at constant rates until original size depending on cd
            # The indicator is updated here to allow for more explicit logic instead of observer pattern via kv
            self.cd_indicator.size = tuple(
                -i / self.cooldown * self.current_cd + i for i in self.size
                )
            self.cd_indicator.center = self.center
        else:
            self.current_cd = 0
            self.on_cd = False

    def touch_handler(self, touch):
        if hypot(*difference(self.center, touch.pos)) <= self.height / 2 and \
        not self.on_cd:
            self.ability()
            self.current_cd = self.cooldown
            # on_cd is to prevent multiple activations of the button while on cd
            self.on_cd = True

class Game(Widget):

    def __init__(self, **kwargs):
        super(Game, self).__init__(**kwargs)
        self.e_container.add_widget(create_hero())

    def update(self, dt):
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
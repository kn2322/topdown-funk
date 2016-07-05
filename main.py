import kivy
kivy.require('1.9.1')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import NumericProperty, BooleanProperty
from math import atan2, degrees, radians, inf, sin, cos, tan

Builder.load_string("""
#: kivy 1.9.1   

<Game>
    EntityContainer:
        id: entity_container
        size: root.size
        pos: root.pos
    LeftStick:
        center: 100, 100
    AbilityButton:
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
        id: moving
        # args[1] is the touch object, important.
        on_touch_down: root.touch_handler(args[1])
        on_touch_move: root.touch_callback(args[1])
        on_touch_up: root.touch_revert()
        center: root.center
        size: 50, 50
        canvas:
            Color:
                rgba: 0, 0, 1, .5
            Ellipse:
                size: self.size
                pos: self.pos

<AbilityButton>
    Widget:
        canvas:
            Ellipse:
                size: root.size
                pos: root.pos
    Widget:
        id: hitbox
        # balance is the average of the default axis aligned bounding box and
        # a smaller box where the corners touch the edge of the button ellipse.
        balance: ((root.height ** 2 / 2) ** 0.5 + root.height) / 2
        size: balance, balance
        center: root.center
""")

Window.size = (800, 600)

# Container widget for all game entites, so they can be referenced by the game.
class EntityContainer(Widget):
    pass

class Entity(Widget):
    # hp, size, ai, in order
    game_entities = {
        'Zombie': (100, 50, None)
        }
    """TODO: Determine different attributes of each game entity, inc but not
    limited to the source image, status effect modifiers, speed.
    """
    def __init__(self, hp, size, **kwargs):
        super(Entity, self).__init__(**kwargs)
        self.hp = hp
        if isinstance(tuple, size):
            self.size = size
        else:
            self.size = (size, size)

    def destroy(self):
        pass

class Player(Entity):
    
    def __init__(self, hp=100, size=20, **kwargs):
        super(Entity, self).__init__(hp, size, **kwargs)

def difference(pos1, pos2):
    return (pos2[0] - pos1[0], pos2[1] - pos1[1])


class LeftStick(Widget):

    #touching = BooleanProperty()
    moving_edge = NumericProperty()

    def __init__(self, **kwargs):
        super(LeftStick, self).__init__(**kwargs)
        self.moving_edge = self.height / 2

    """For on_touch_down, it detects whether the touch is on the moving_stick,
    before it binds the pos of the moving_stick onto the touch, this is so that
    it doesn't bind to the edge of the leftstick when the touch moves in from
    outside. The touching variable communicates so that touch_callback isn't
    called unless the touch starts from the center (and on the moving_stick).
    """
    def touch_handler(self, touch):
        self.touch_callback(touch)
    
    # For on_touch_move
    def touch_callback(self, touch):
        if touch.x < Window.width / 2:
            delta = difference(self.center, touch.pos)
            angle = atan2(delta[1], delta[0])
            try:
                gradient = delta[1] / delta[0]
            except ZeroDivisionError:
                gradient = inf
            #print(angle, gradient)
            if self.collide_point(*touch.pos):
                self.moving_stick.center = touch.pos
            else:
                # Intense right angle trigonometry
                # Converting between rads and degrees for absolute value of degrees, don't know a better way.
                # EDIT: Don't need abs value, it works without doing it
                # Operates on 'triangle' where the moving_edge is the hypotnuse
                x = self.center_x + self.moving_edge * cos(angle)
                y = self.center_y + self.moving_edge * sin(angle)
                self.moving_stick.center = (x, y)


    # For on_touch_up
    def touch_revert(self):
        self.moving_stick.center = self.center

class AbilityButton(Widget):



    # Functions to be accepted with *args with tuple which has func and its cd.
    # Purpose: So that the button's behavior is able to be swapped out depending on hero.
    def __init__(self, func=None, cool_down=None, **kwargs):
        super(AbilityButton, self).__init__(**kwargs)
        self.func = func
        self.cool_down = cool_down

    def assign(self, func, cool_down):
        self.func = func
        self.cool_down = cool_down

    def touch_handler(self, touch):
        pass




class Zombie(Entity):

    direction = NumericProperty()
    rotation_speed = NumericProperty(6)
    speed = NumericProperty(40)

    def __init__(self, hp=100, size=50, **kwargs):
        super(Zombie, self).__init__(hp, size, **kwargs)

    def update(self, player):
        atan2()
        self.move()

    def move(self):
        pass


class AI():

    def __init__(self):
        pass

class Game(Widget):

    def update(self, dt):
        pass

    """Creates entity in the gamespace with parameter which points to dict of 
    possible entities. The higher level determining the positions and numbers of
    entites to spawn are done with a higher level object(?).
    """
    def create_entity(self, entity):
        objects = Entity.game_entities
        if entity not in objects.keys():
            raise ValueError("'{}' is an invalid entity.".format(entity))
        e = objects[entity]
        self.entity_container.add_widget(Entity(*e))

# TDS: Top Down Shooter
class TDSApp(App):

    def build(self):
        game = Game()
        Clock.schedule_interval(game.update, 1/60)
        return game
        
if __name__ == '__main__':
    TDSApp().run()
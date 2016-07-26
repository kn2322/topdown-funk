from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.graphics import Line, Ellipse, Rectangle, Color
from math import atan2, hypot, cos, sin
from utilfuncs import difference
from kivy.properties import NumericProperty, BooleanProperty
from kivy.vector import Vector
from kivy.core.window import Window

"""Module used to contain all of the ui elements in the game, to avoid cluttering
the main file
"""

Builder.load_string("""
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
""")

class UI(Widget): # Considering to change this into a layout for resolution scaling.
    
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

    def __init__(self, **kwargs):
        super(RightStick, self).__init__(**kwargs)
        self.size = 1, 1
        self.graphics = lambda self: Line(width=1.5, circle=(*self.center, 200))

    def update(self, game):
        self.center = Vector(game.player.center) + Vector(game.camera.offset)
        self.canvas.clear()
        self.canvas.add(Color(1, 0, 0, .5))
        self.canvas.add(self.graphics(self))

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
        self.player = game.player
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
            self.ability(self.player)
            self.current_cd = self.cooldown
            # on_cd is to prevent multiple activations of the button while on cd
            self.on_cd = True
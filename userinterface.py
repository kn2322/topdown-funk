from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.graphics import Line, Ellipse, Rectangle, Color
from math import atan2, hypot, cos, sin
from kivy.properties import NumericProperty, BooleanProperty
from kivy.vector import Vector
from kivy.core.window import Window
from utilfuncs import difference

"""Module used to contain all of the ui elements in the game, to avoid cluttering
the main file
"""

Builder.load_string("""
<UI>
    HealthBar:
        center: root.center_x, root.top - 50


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
        on_touch_move: root.touch_handler(args[1])
        on_touch_up: root.touch_revert()
        center: root.center
        size: 40, 40
        canvas:
            Color:
                rgba: 0, 0, 1, 1
            Ellipse:
                size: self.size
                pos: self.pos

<HealthBar>
    size: 200, 50
    canvas:
        Color:
            rgb: .5, .5, .5
        Rectangle:
            size: self.size
            pos: self.pos
        Color:
            rgb: .5, 0, 0
        Rectangle:
            # unreadable, but basically doesn't let the bar go negative
            size: self.width * self.hp / self.max_hp if self.width * self.hp / self.max_hp > 0 else 0, self.height
            pos: self.pos

    Label:
        size: root.size
        pos: root.pos
        text: '{} / {}'.format(root.hp, root.max_hp)
""")
# For the old circular ability button.
"""
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
"""

class UI(Widget): # Change this into a layout for resolution scaling.
    
    def __init__(self, **kwargs):
        super(UI, self).__init__(**kwargs)
        self.left_stick = LeftStick(center=(self.x+100,self.y+100))
        self.right_stick = RightStick()
        # 'Slots' for utility abilities/buttons.
        self.slots = [
            # Center positions of ability buttons
            AbilityButton(slot=0, center=(Window.width-100, 100)),
            AbilityButton(slot=1, center=(Window.width-100, 100))
        ]
        self.add_widget(self.left_stick)
        self.add_widget(self.right_stick)

    # Updates all ui elements needing updates
    def update(self, game, *args):
        player_a = game.player.components['Action']
        # Adds button when there is an assigned ability, doesn't account for removing buttons.
        for slot, a in enumerate(player_a.abilities):
            if a is None:
                continue
            if self.slots[slot] not in self.children:
                self.add_widget(self.slots[slot])
        # For checking whether or not the ability exists, to bypass looping in self.children, since before the ability exists, the button is NOT added to the UI.
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
        # The stick starts on bottom left of left stick, so this is a workaround.
        self.moving_stick.center = self.center

    # For on_touch_move
    # TODO: remove gradient/unecessary components
    def touch_handler(self, touch):
        # Can't reference moving_stick in __init__ (defined in kv lang)
        self.moving_edge = self.height / 2 - self.moving_stick.height / 2

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
        self.radius = 200
        self.size = 1, 1
        # graphical representation function, as the circle can't be referenced with pos.
        def g(self):
            return Line(width=1.5, circle=(*self.center, self.radius))
        self.graphics = g
        # None so conditions in which direction to face can be done with if rightstick.angle...
        self.angle = None

    def on_touch_down(self, touch):
        self.touch_handler(touch)

    def on_touch_move(self, touch):
        self.touch_handler(touch)

    def on_touch_up(self, touch):
        self.angle = None

    def touch_handler(self, touch):
        d = difference(self.center, touch.pos)
        if hypot(*d) <= self.radius:
            self.angle = atan2(d[1], d[0])
        else:
            self.angle = None

    def update(self, game):
        self.center = game.user_interface.center
        self.canvas.clear()
        self.canvas.add(Color(1, 0, 0, .5))
        self.canvas.add(self.graphics(self))
"""
class AbilityButton(Widget):

    cooldown = NumericProperty()

    # Functions to be accepted with *args with tuple which has func and its cd.
    # Purpose: So that the button's behavior is able to be swapped out depending on hero.
    def __init__(self, slot, **kwargs):
        super(AbilityButton, self).__init__(**kwargs)
        self.slot = slot
        self.ability = None

    def update(self, game):
        self.player = game.player
        self.ability = self.player.components['Action'].slots[self.slot]
        if self.ability is None:
            return None
        current_cd = self.ability.current_cd

        if current_cd > 0:
            # Function to make the size of cd_indicator grow at constant rates until original size depending on cd
            # The indicator is updated here to allow for more explicit logic instead of observer pattern via kv.
            self.cd_indicator.size = tuple(
                -i / self.ability.cooldown * current_cd + i for i in self.size
                )
            self.cd_indicator.center = self.center
            self.cd_indicator.canvas.clear()
            with self.cd_indicator.canvas:
                Color(a=0.3)
                Ellipse(size=self.cd_indicator.size, pos=self.cd_indicator.pos)
        else:
            self.cd_indicator.canvas.clear()

    def touch_handler(self, touch):
        if hypot(*difference(self.center, touch.pos)) <= self.height / 2 and \
        self.ability.current_cd <= 0:
            self.ability.activate(self.player)
"""
class AbilityButton(Widget):

    cooldown = NumericProperty(1)

    # Purpose: So that the button's behavior is able to be swapped out depending on hero.
    def __init__(self, slot, **kwargs):
        super(AbilityButton, self).__init__(**kwargs)
        self.slot = slot
        self.ability = None

    def on_touch_down(self, touch):
        # Button down animation
        pass

    def on_touch_move(self, touch):
        # Change animation if hand slides off to other button
        pass

    def on_touch_up(self, touch):
        # Activate button
        self.touch_handler(touch)

    def update(self, game):
        self.player = game.player
        self.ability = self.player.components['Action'].abilities[self.slot]

        # Handles counting down cd, previously handled in action components...
        self.ability.time_step()

        current_cd = self.ability.cooldown.current
        
        self.canvas.clear()
        # Graphics are updated here to be more explicit than kv lang, and works.
        with self.canvas:
            Color(rgb=(0,0,1))
            Rectangle(pos=self.pos, size=self.size)
        if current_cd > 0:
            # Function for width being proportional to cd.
            cd_width = (self.ability.cooldown.current / self.ability.cooldown.default) * self.width
            cd_indicator_size = (
                cd_width if self.ability.cooldown.current > 0 else 0,
                self.height
                )
            with self.canvas:
                Color(a=0.3)
                Rectangle(size=cd_indicator_size, pos=self.pos)

    def touch_handler(self, touch):
        if self.collide_point(*touch.pos) and self.ability.cooldown.current <= 0:
            self.ability.activate(self.player)

# Temporary health bar before final health bar system is decided.
class HealthBar(Widget):

    max_hp = NumericProperty(1)
    hp = NumericProperty(1)

    def update(self, game):
        player = game.player
        self.max_hp = player.max_hp
        self.hp = player.hp
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, BoundedNumericProperty, ListProperty, StringProperty, BooleanProperty
from collections import OrderedDict
from kivy.clock import Clock

"""Module containing the entity class, which will be imported,
along with components.

Every entity will have some information known to other entities when needed.
These information are the type of entity, the name of the individual entity,
and health.
"""
class Entity(Widget):

    # IMPORTANT: Class level attributes do not seem to show up in __dict__

    # Bounded properties for game balance, all managed here.
    #velocity_multiplier = BoundedNumericProperty(0)
    #knockback_coefficient = NumericProperty()
    # Boolean for taking damage
    #can_be_damaged = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(Entity, self).__init__(**kwargs)
        # 'components' uses a dict so each component can be referenced and extended.
        # Action component is to handle the inputs for ability casting.
        # OrderedDict allows the components to update at the correct order.
        self.components = OrderedDict(
            {'Input': None, 'Physics': None, 'Action': None, 'Graphics': None}
        )

        """There will be a corresponding database where all of these attribute
        values for whatever entity will be stored, and called in to assign
        everything in the entity's creation function.
        """
        # ALL THE ATTRIBUTES, adjacent ones are ones in the same category.
        """IMPORTANT: __str__ does not seem to work with the instance variables
        defined in this method, raises AttributeError. However it DOES work for
        variables present in Widget(), such as pos. Find out why.
        """
        self.name = ''

        # In pixels/s, 
        # velocity multiplier is changed when char move speed is change.
        # velocity is derived in physics component from multiplier.
        self.velocity_multiplier = 0
        self.velocity = 0, 0

        self.can_be_damaged = True
        self.max_hp = 0
        self.hp = 0

        self.last_pos = 0, 0

        # Damage done upon contact
        self.contact_damage = 0

        # Cooldown in between ranged attacks or otherwise.
        # Entities with 1 < derives the individual ones from the attack speed.
        self.attack_speed = 0

    def update(self, game):
        Clock.schedule_once(self.record_pos, -1)
        for name, item in self.components.items():
            if item is None:
                continue
            item.update(self, game)

    def collide(self, other, entity_container):
        self.components['Action'].collide(self, other, entity_container)

    def move(self, next_pos, map_size):
        self.components['Physics'].move(self, next_pos, map_size)

    """Pass DamageInfo object (abilitydata.py) as argument,
    defines behaviour when receiving damage, whether armour or whatever
    effects are applied, before lowering the hp.
    """
    def receive_damage(self, damage_info):
        get_value = self.components['Action'].get_value
        if get_value(self, 'can_be_damaged'):
            print('damaged')
            self.components['Action'].on_receive_damage(self, damage_info)

    def record_pos(self, *args):
        self.last_pos = self.pos
        return None
from kivy.vector import Vector
from kivy.graphics import Ellipse
from kivy.clock import Clock
from math import sin, cos, atan2, hypot
from utilfuncs import circle_collide, difference
from abilitydata import DamageInfo, Cooldown, Invincibility, SuperSpeed
from entity import Entity
from functools import partial

"""Module used to contain all of the character components in the game
"""

class InputComponent:
    pass

class PhysicsComponent:

    def __init__(self):
        # direction is a value received from the input component indicating direction of movement.
        self.direction = [0, 0]
        self.total_velocity = [0, 0] # imperative movement + displacement.
        self.time = False
        """
        # The controlled movement velocity.
        self.c_velocity = [0, 0]
        """

    def update(self, entity, game):
        self.move(entity, game)

    # Called in action component to allow 'Postprocessing'. RESOLVED with get_value()
    # next_pos is a universal moving interface that checks for map boundaries when moving an entity.
    # This could be moved to entity container, and call individual entity behaviour when e.g. hitting the walls.
    def temp_move(self, entity, next_pos, map_size):
        bounds = map_size
        outx, outy = entity.pos
        # Compares x and y borders individually to allow sliding along the border.
        if 0 > next_pos.x:
            outx = 0
        elif next_pos.x + entity.width > bounds[0]:
            outx = bounds[0] - entity.width
        else:
            outx = next_pos.x

        if 0 > next_pos.y:
            outy = 0
        elif next_pos.y + entity.height > bounds[1]:
            outy = bounds[1] - entity.height
        else:
            outy = next_pos.y

        entity.pos = outx, outy

    # For the physics interactions with colliding entity.
    def collide_entity(self, entity, other, entity_container): # Returns next position.
        return self.separate(entity, other)

    """Returns next_pos where objects don't intersect, recommend to call this first
    in collision resolving.
    """
    def separate(self, entity, other):
        v = self.total_velocity # Total, adding displacement and imperative movement.
        """ Theory, find the amount to add to the currrent entity position so that
        it is exactly colliding with the other using circle_collide,
        which is hypot(*difference(a.center, b.center)) == a.width + b.width.
        In an eqn where x is the coefficient (time) for the total velocity so that it
        fulfills the exact collision. NOT WORKING

        New, calculate overlapping distance by subtracting distance of two entities from the sum of
        the radii. Then move back by the current direction * depth.
        """
        diff = difference(entity.pos, other.pos)
        depth = (entity.width + other.width) / 2 - hypot(*diff) # Overlapping distance
        min_pv = Vector(*diff).normalize() * depth # Min penetrating vector using current velocity vector (not actually minimum)
        next_pos = Vector(*entity.pos) + (v - min_pv)
        return next_pos

    # Wall colliding behaviour.
    def collide_wall(self, entity, map_size):
        pass

    def move_to_mapborder(self, entity, map_size): # Handles the edge of the map.
        pass

    def move(self, entity, game):
        get_value = entity.components['Action'].get_value
        multiplier = get_value(entity, 'velocity_multiplier')
        # Multiply 'direction' with speed and divide by 60 for updates per second.
        controlled_movement = Vector(self.direction) * (multiplier / 60)
        self.total_velocity = Vector(*controlled_movement) + Vector(*entity.velocity)
        next_pos = Vector(*entity.pos) + self.total_velocity

        # Checks for collision with all types, keeps recalculating physics until there are no more collisions,
        # makes entity move up to the border of an entity it collides with, while the collision funcs define behaviour afterwards.

        # This block is currently bugged beyond belief.

        e_container = game.e_container
        
        for e in e_container.children:
            
            if circle_collide(entity, e):
                # Resolves the physics portion of the collision.
                next_pos = self.collide_entity(entity, e, e_container)
                
                # Collide for both entities MUST be called, otherwise your own collision will only be called when you move.
                entity.components['Action'].collide(entity, e, e_container)
                e.components['Action'].collide(e, entity, e_container)
        
        entity.pos = next_pos
        
# Convert center pos to actual pos for canvas instructions.
def center_to_pos(size, pos):
    return Vector(*pos) - Vector(*size) / 2

class GraphicsComponent:

    def __init__(self):
        self.graphics = None

    # Not handled by kv lang bc it's not explicit enough for update loop.
    def update(self, entity, game):
        self.graphics = self.update_graphics(entity)

        # Apply camera offset
        offset = game.camera.offset
        draw_pos = Vector(*entity.pos) + Vector(*offset)

        # Not using instruction group because iterating over it is not working.
        # Iterates because container of graphical elements is iterable.

        entity.canvas.clear()
        for i in self.graphics:
            # The position of the instruction of a coordinate space of (0, 0)-(width, height) which is then offsetted by camera.
            # Works because draw_pos accounted for the original position of the entity.
            i.pos = Vector(center_to_pos(i.size, i.pos)) + Vector(*draw_pos)
            entity.canvas.add(i)

    # the graphics can be altered without copying the entire update function.
    # Contains the graphical information of the entity
    def update_graphics(self, entity):
        # The default
        g = []
        g.append(Ellipse(size=entity.size, pos=(entity.width/2,entity.height/2)))
        return g

class ActionComponent:

    def __init__(self):
        # Functions/Objects which contain active effects, their duration,
        self.effects = []

    def update(self, entity, game):
        if entity.hp <= 0:
            # Destroy is provisional here, exp and other systems have not been added.
            self.destroy(entity, game)
        for effect in self.effects:
            effect.time_step()
            if effect.duration <= 0:
                self.effects.remove(effect)

    def destroy(self, entity, game):
        game.player.receive_exp(entity.exp) # Giving player exp.
        game.e_container.remove_widget(entity)
    """The universal value getter used in all components, although the __dict__
    might (probably not) need to be changed, since it doesn't apply to any
    attributes in the widget class.

    The function applies all of the active effects as 'Post processing' onto the
    character attribute, so the attribute itself is not modified, while the used
    value is. The multipliers are applied before the additives.

    It is yet to be decided if multipliers have diminishing returns, or if another
    system is used all together, at that point, simply change this.
    """
    def get_value(self, entity, attribute_id):
        try:
            val = entity.__dict__[attribute_id]
        except AttributeError:
            # Should really be with logging...
            print('Attribute {} is not in {}'.format(attribute_id, entity))
            return val

        for effect in self.effects:
            val = effect.m_apply_modifier(attribute_id, val)
        for effect in self.effects:
            val = effect.a_apply_modifier(attribute_id, val)
        for effect in self.effects:
            val = effect.spec_apply_modifier(attribute_id, val)
        return val

    # Defines behaviour of entity when colliding with another entity.
    def collide(self, entity, other, entity_container):
        pass

    """Pass DamageInfo object (abilitydata.py) as argument,
    defines behaviour when receiving damage, whether armour or whatever
    effects are applied, before lowering the hp.
    """
    def on_receive_damage(self, entity, damage_info):
        #print('damaged, %s' % self.get_value(entity, 'can_be_damaged'))
        if self.get_value(entity, 'can_be_damaged'):
            entity.hp -= damage_info.amount
        #attacker = damage_info.attacker

    """ Changed system to globallly accessible player exp, and adding to that.
        if entity.hp <= 0 and True: # attacker.name in EntityContainer.players -> Not implemented bc entity container needs to be moduled and imported. I think is Singleton.
            # Destruction not handled here to allow for better overriding (?), decorators may be applicable here.
            attacker.receive_exp(entity.exp) # If action component contained exp.

    def on_receive_exp(self, entity, amount):
        pass
    """


"""The character input component only handles the movement stick, and not the
actual ability buttons, because they are as simple as binding an ability with
argument being the player.
"""

class HeroInputComponent(InputComponent):

    def __init__(self):
        # Same one as the one in left stick, used for reference by physics.
        # This is not encapsulated and decoupled, use caution.
        # Decimal distance of moving stick from border
        self.touch_distance = 0

    def update(self, entity, game):
        self.basic_attack_speed = entity.attack_speed
        ui = game.user_interface
        self.activate_left(entity, ui.left_ui.left_stick)

    def activate_left(self, entity, left_stick):
        angle = left_stick.angle
        self.touch_distance = left_stick.touch_distance
        x = cos(angle)
        y = sin(angle)
        # Tells physics the direction, not the full velocity, which is processed more.
        entity.components['Physics'].direction = [x, y]


class HeroPhysicsComponent(PhysicsComponent):

    def update(self, entity, game):
        if entity.components['Input'].touch_distance <= .7:
            return None
        self.move(entity, game)

    # TODO: Add displacement/knockback

# Job is to contain the graphical elements of the entity,
# and handle drawing with the camera.
class HeroGraphicsComponent(GraphicsComponent):

    pass

# The base class for player characters action components.
class HeroActionComponent(ActionComponent):
    
    def __init__(self):
        super(HeroActionComponent, self).__init__()
        self.abilities = [None, None]
        # Using cooldown object to reduce number of variables
        self.basic_attack_cd = Cooldown(0)
        self.exp = 0
        self.levels = (0, 0, 0) # Level increments.

    def assign_util_ability(self, ability):
        for idx, slot in enumerate(self.abilities):
            if slot is None:
                self.abilities[idx] = ability
                return None

    def update(self, entity, game):
        super(HeroActionComponent, self).update(entity, game)
        self.basic_attack_cd.default = entity.attack_speed
        for ability in self.abilities:
            try:
                ability.time_step()
            except AttributeError:
                continue
        self.activate_right(entity, game)

    # Needs to know game for both ui and e_container
    # Used for handling cooldowns and conditions for basic attack.
    def activate_right(self, entity, game):
        angle = game.user_interface.right_stick.angle
        # Angle is None if touch is not pressed.
        if angle and self.basic_attack_cd.current <= 0:
            a = create_hero_projectile(entity.center)
            a.components['Physics'].direction = [cos(angle), sin(angle)]
            game.e_container.add_entity(a)
            self.basic_attack_cd.activate()
        else:
            self.basic_attack_cd.time_step()

    def collide(self, entity, other, entity_container):
        pass
        """ Deprecated because of becoming invincible before receiving damage, functionality moved to on_receive_damage.
        if other.name in entity_container.enemies:
            if Invincibility in (type(i) for i in self.effects):
                return None
            def append(itm, dt): self.effects.append(itm)
            effect = partial(append, Invincibility(self, 1.5))
            Clock.schedule_once(effect, -1)
        """

    def on_receive_damage(self, entity, damage_info):
        #print('damaged, %s' % self.get_value(entity, 'can_be_damaged'))
        if self.get_value(entity, 'can_be_damaged'):
            entity.hp -= damage_info.amount
            self.effects.append(Invincibility(self, 1.5))

    def on_receive_exp(self, entity, amount): # Unique to player action component.
        print('Player has received {} exp'.format(amount))
        self.exp += amount

"""Below this point are enemy components.
"""

"""Provisionally, the AI will work through trees of decision making with methods,
starting with what action to do, which will put the AI into a predetermined state. (Enum, Dict, whateever)
Whenever update is called, the method for the AI's state is called, giving instruction.
"""
class BaseAIComponent(InputComponent):
    
    def __init__(self):

        # Dict for now, can switch to Enum, database.

        # states can include routines, which are a list of state functions that cannot be easily broken out of.
        self.states = {
            'IDLE': lambda *args: None,
            'CHASE': self.chase_state
            }

        self.state = 'IDLE'
        # Seconds times update speed.
        self.cooldown = 2 * 60
        # The amount of time in between each state function call, to give sense of lag.
        self.cycle_count = 20

    def update(self, entity, game):
        if self.cooldown <= 0:
            self.state = self.get_state(entity, game)
        self.cooldown -= 1

        if self.cycle_count <= 0:
            self.states[self.state](entity, game)
            self.cycle_count = 20
        else:
            self.cycle_count -= 1

    """The ai states work in a hierarchy of 2 levels (as of now).
    First is get_state, which makes a broad decision based on the game situation
    as for what the ai should do. Then the determined state function is called
    every update loop, making its own decisions for the ai's tangible behaviour.

    Routines can be part of an AI 'state', where a list of state functions that
    can be unique to the routine are called in order, such as 'move in an arc
    relative to the player, then shoot the player'.
    """

    # The highest level function for determining which state to use.
    def get_state(self, entity, game):
        player = game.player
        return 'CHASE'

    # Mindless chasing, TODO: cooldown of state switching.
    def chase_state(self, entity, game):
        # The number of cycles in between each change, to create a sense of lag.
        # Research closures to figure out method specific variables.
        frequency = 15

        player = game.player

        delta = difference(entity.pos, player.pos)
        angle = atan2(delta[1], delta[0])
        x = cos(angle)
        y = sin(angle)

        entity.components['Physics'].direction = [x, y]

class RiotPoliceInputComponent(BaseAIComponent):
    pass

class RiotPolicePhysicsComponent(PhysicsComponent):
    pass

class RiotPoliceGraphicsComponent(GraphicsComponent):

    def update_graphics(self, entity):
        g = []
        g.append(Ellipse(size=entity.size, pos=(entity.width/2, entity.height/2)))
        g.append(Ellipse(size=(10,10), pos=(0, entity.height/2)))
        g.append(Ellipse(size=(10,10), pos=(entity.width/2, entity.height)))
        g.append(Ellipse(size=(10,10), pos=(entity.width, entity.height/2)))
        g.append(Ellipse(size=(10,10), pos=(entity.width/2, 0)))
        return g

class RiotPoliceActionComponent(ActionComponent):

    def __init__(self):
        super(RiotPoliceActionComponent, self).__init__()
        # Proposition: make the contact_damage 'derive' from a base damage, so all damage from an entity is changed when dmg is changed.
        # self.contact_damage = 1
        # Moved to main entity

    def collide(self, entity, other, entity_container):
        if other.name in entity_container.players: # entity_id is yet to be implemented.
            dmg_inf = DamageInfo(
                entity,
                self.get_value(entity, 'contact_damage'), # damage is gotten through get_value interface.
                'contact' # dmg_type
                )
            other.receive_damage(dmg_inf)

"""Below here are all of the 'sub entities' created by entities (projectiles, etc.)
Each one will have a comment as to what entity(s) it belongs to.
"""

class HeroProjectilePhysicsComponent(PhysicsComponent):

    def collide_entity(self, entity, other, entity_container): # Overridden bc projectile is destroyed on contact with enemy.
        return Vector(*entity.pos) + self.total_velocity

class HeroProjectileGraphicsComponent(GraphicsComponent):

    pass

# Belongs to the 'Hero' or 'test_hero' entity, as a projectile to fire.
class HeroProjectileActionComponent(ActionComponent):

    def __init__(self, dmg=1):
        super(HeroProjectileActionComponent, self).__init__()
        self.damage = dmg

    # No need for active effects on a projectile.
    def update(self, *args):
        pass

    def collide(self, entity, other, entity_container):
        if other.name in entity_container.enemies:
            d = DamageInfo(entity, self.damage, 'projectile')
            other.receive_damage(d)
            entity_container.remove_widget(entity)

    # Can't be destroyed, destructible projectiles can have hp value.
    def on_receive_damage(self, *args):
        pass



"""Below here are entity creation functions, includes:
components, entity, various attributes.
"""

# Window.center is to be changed to starting position on the game map
def create_hero(center, size=(20, 20)):
    # TODO: Add error checking if the name is not in any valid names.
    e = Entity(center=center, size=size)
    chardata = {'name': 'test_hero', 'max_hp': 20, 'hp': 20, 
        'velocity_multiplier': 450, 'attack_speed': 1.5
        }
    for key, val in chardata.items():
        e.__dict__[key] = val
    e.components['Input'] = HeroInputComponent()
    e.components['Physics'] = HeroPhysicsComponent()
    e.components['Graphics'] = HeroGraphicsComponent()
    e.components['Action'] = HeroActionComponent()
    e.components['Action'].assign_util_ability(SuperSpeed())
    # The add_widget step is not in the function, so it's decoupled.
    return e

def create_hero_projectile(center, size=(25, 25)):
    e = Entity(size=size)
    e.center = center
    chardata = {'name': 'test_projectile', 'max_hp': 1, 'hp': 1,
        'velocity_multiplier': 700, 'can_be_damaged': False
        }
    for key, val in chardata.items():
        e.__dict__[key] = val
    e.components['Input'] = None
    e.components['Physics'] = HeroProjectilePhysicsComponent()
    e.components['Graphics'] = HeroProjectileGraphicsComponent()
    e.components['Action'] = HeroProjectileActionComponent()
    return e

def create_riot_police(center, size=(20, 20)):
    e = Entity(center=center, size=size)
    chardata = {'name': 'Riot Police', 'max_hp': 3, 'hp': 3, 'velocity_multiplier': 250,
        'contact_damage': 1, 'exp': 2
                }
    for key, val in chardata.items():
        e.__dict__[key] = val
    e.components['Input'] = RiotPoliceInputComponent()
    e.components['Physics'] = RiotPolicePhysicsComponent()
    e.components['Graphics'] = RiotPoliceGraphicsComponent()
    e.components['Action'] = RiotPoliceActionComponent()
    return e

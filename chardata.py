from kivy.vector import Vector
from kivy.graphics import Ellipse, Color
from kivy.clock import Clock
from math import sin, cos, atan2, hypot
from utilfuncs import circle_collide, difference
from abilitydata import DamageInfo, Cooldown, Invincibility, SuperSpeed, SpeedUp
from entity import Entity
from functools import partial
import random

"""Module used to contain all of the character components in the game
"""

class InputComponent:
    pass

class PhysicsComponent:

    def __init__(self): # Pls call super()... every time it's subclassed
        # direction is a value received from the input component indicating direction of movement.
        self.direction = [0, 0]
        self.total_velocity = [0, 0] # imperative movement + displacement.
        self.can_collide_wall = True
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

    """ Moved to entity container.
    # For the physics interactions with colliding entity.
    def collide_entity(self, entity, other, entity_container): # Returns next position.
        return self.separate(entity, other)
    """

    """Returns next_pos where objects don't intersect, recommend to call this first
    in collision resolving.
    """
    """ Moved to entity container
    def separate(self, entity, other):
        v = self.total_velocity # Total, adding displacement and imperative movement.
        
        Theory, find the amount to add to the currrent entity position so that
        it is exactly colliding with the other using circle_collide,
        which is hypot(*difference(a.center, b.center)) == a.width + b.width.
        In an eqn where x is the coefficient (time) for the total velocity so that it
        fulfills the exact collision. NOT WORKING

        New, calculate overlapping distance by subtracting distance of two entities from the sum of
        the radii. Then move back by the current direction * depth.
        
        diff = difference(entity.pos, other.pos)
        depth = (entity.width + other.width) / 2 - hypot(*diff) # Overlapping distance
        min_pv = Vector(*diff).normalize() * depth # Min penetrating vector using current velocity vector (not actually minimum)
        next_pos = Vector(*entity.pos) + (v - min_pv)
        return next_pos
    """

    # Wall colliding behaviour, default from entity container is to do nothing.
    def collide_wall(self, entity, entity_container):
        pass

    def move(self, entity, game):
        get_value = entity.components['Action'].get_value
        multiplier = get_value(entity, 'velocity_multiplier')
        # Multiply 'direction' with speed and divide by 60 for updates per second.
        if self.direction:
            controlled_movement = Vector(self.direction) * (multiplier / 60)
        else:
            controlled_movement = Vector(0, 0)
        displacement = entity.velocity
        self.total_velocity = Vector(*controlled_movement) + displacement
        next_pos = Vector(*entity.pos) + self.total_velocity

        # Reducing displacment vector based on friction.
        displacement *= 1 - (entity.friction / 60) if displacement.length() > 0.5 else 0 # Prevent infinitely close to 0.

        # Checks for collision with all types, keeps recalculating physics until there are no more collisions,
        # makes entity move up to the border of an entity it collides with, while the collision funcs define behaviour afterwards.

        """ Moved to collision engine (entity container)
        # This block is currently bugged beyond belief.

        e_container = game.e_container
        
        for e in e_container.children:
            
            if circle_collide(entity, e):
                # Resolves the physics portion of the collision.
                next_pos = self.collide_entity(entity, e, e_container)
                
                # Collide for both entities MUST be called, otherwise your own collision will only be called when you move.
                entity.components['Action'].collide(entity, e, e_container)
                e.components['Action'].collide(e, entity, e_container)
        """
        
        entity.pos = next_pos

    # if cant_collide: return False else: return True is the way this should be used, called with an all().
    def can_collide(self, entity, other):
        return True # Can be physically resolved, called in entity container.
        
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
            if type(i) != Color:
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

        self.leftdown = False # Booleans for entity state.
        self.rightdown = False

    def update(self, entity, game):
        ui = game.user_interface
        left_stick = ui.left_ui.left_stick
        if left_stick.touch_distance != None and left_stick.touch_distance >= 0.7:
            self.leftdown = True
            self.activate_left(entity, left_stick)
        else:
            entity.components['Physics'].direction = None
            self.leftdown = False
        self.rightdown = bool(ui.right_stick.angle)

    def activate_left(self, entity, left_stick):
        angle = left_stick.angle
        x = cos(angle)
        y = sin(angle)
        # Tells physics the direction, not the full velocity, which is processed more.
        entity.components['Physics'].direction = [x, y]


class HeroPhysicsComponent(PhysicsComponent):

    def update(self, entity, game):
        """acomp = entity.components['Action']

        if acomp.state in ('moving', 'attacking') and self.direction: # If left_stick is activated.
        """
        self.move(entity, game)

    # TODO: Add displacement/knockback

# Job is to contain the graphical elements of the entity,
# and handle drawing with the camera.
class HeroGraphicsComponent(GraphicsComponent):

    pass

# The base class for player characters action components.
class HeroActionComponent(ActionComponent):

    states = ['idle', 'moving', 'attacking']
    
    def __init__(self):
        super(HeroActionComponent, self).__init__()
        self.abilities = [None, None]
        # Using cooldown object to reduce number of variables
        self.basic_attack_cd = Cooldown(0) # The duration is attack animation duration.
        self.exp = 0
        self.level = 0 # used for checking for level ups.
        self.lvl_boundaries = (0, 500, 7, 20) # Level increments.
        self.state = 'idle'


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

        self.basic_attack_cd.time_step()

        icomp = entity.components['Input']

        if self.state == 'idle':
            if icomp.rightdown:
                self.state = 'attacking'
            elif icomp.leftdown:
                self.state = 'moving'

        elif self.state == 'attacking':
            if self.basic_attack_cd.current > 0: # If attack animation is not finished.
                effect = SpeedUp(None, 1/60, 0.3)
                self.effects.append(effect)
            elif icomp.rightdown:
                self.activate_right(entity, game)
            elif icomp.leftdown:
                self.state = 'moving'
            else:
                self.state = 'idle'

        elif self.state == 'moving':
            if icomp.rightdown:
                self.state = 'attacking'
            elif icomp.leftdown:
                pass
            else:
                self.state = 'idle'
            

        if self.exp >= self.lvl_boundaries[self.level+1]:
            self.level += 1
            game.level_up()


    # Needs to know game for both ui and e_container
    # Used for handling cooldowns and conditions for basic attack.
    def activate_right(self, entity, game):
        angle = game.user_interface.right_stick.angle # Angle of touch.
        # Angle is None if touch is not pressed.
        if angle and self.basic_attack_cd.current <= 0:

            def create_proj(*args):
                a = create_hero_projectile(Vector(*entity.center), velocity_multiplier=100) # target_pos is for curving towards a location.
                direction = Vector(cos(angle), sin(angle)).rotate(random.uniform(-5, 5))
                #a.velocity_multiplier = random.uniform(400, 700) # TODO: Replace with some kwarg instead of direct access.
                a.components['Physics'].direction = direction
                #a.center = Vector(*a.center) + Vector(cos(angle), sin(angle)) * 3 # For spawning the missile off center.
                game.e_container.add_entity(a)

            for idx, _ in enumerate(range(3)): # Chain missile test.
                #Clock.schedule_once(create_proj, idx/10)
                create_proj()

            self.basic_attack_cd.activate()

            entity.velocity += -Vector(cos(angle), sin(angle)).rotate(random.randint(-10, 10)) * 2 # Recoil to give weight, multiplier is magnitude.
        else:
            pass
            #self.basic_attack_cd.time_step()

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
            self.effects.append(Invincibility(self, 0.5))

    def on_receive_exp(self, entity, amount): # Unique to player action component.
        print('Player has received {} exp'.format(amount))
        self.exp += amount

    def destroy(self, entity, game):
        game.game_over()


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
        # Seconds * update speed.
        self.cooldown = 2 * 60

    def update(self, entity, game):
        if self.cooldown <= 0:
            self.state = self.get_state(entity, game)
        self.cooldown -= 1

        self.states[self.state](entity, game)

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
    
    def update(self, entity, game):
        super(RiotPolicePhysicsComponent, self).update(entity, game)
        # TODO: Add stuff here.

class RiotPoliceGraphicsComponent(GraphicsComponent):

    def update_graphics(self, entity):
        g = []
        g.append(Color())
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
            #print(other.name)
            other.receive_damage(dmg_inf)
            # Knockback code on contact.
            # TODO: Add variable for knockback magnitude.
            other.velocity += (Vector(*other.pos) - Vector(*entity.pos)).normalize() * 8
        elif other.name in entity_container.enemies:
            other.velocity += (Vector(*other.pos) - Vector(*entity.pos)).normalize() * 2

    def destroy(self, entity, game):
        game.player.receive_exp(entity.exp)
        game.decal_engine.add_decal(entity.center)
        game.e_container.remove_widget(entity)

"""Below here are all of the 'sub entities' created by entities (projectiles, etc.)
Each one will have a comment as to what entity(s) it belongs to.
"""

class HeroProjectilePhysicsComponent(PhysicsComponent):

    #def collide_entity(self, entity, other, entity_container): # Overridden bc projectile is destroyed on contact with enemy.
        #return Vector(*entity.pos) + self.total_velocity

    def __init__(self, target_pos=None, **kw):
        super(HeroProjectilePhysicsComponent, self).__init__(**kw)
        self.target_pos = target_pos # Aimed position, NOT IN USE.

    def update(self, entity, game):
        super(HeroProjectilePhysicsComponent, self).update(entity, game)
        self.direction = Vector(*self.direction).rotate(random.choice([2, -2, 0])) # 'shakes' the missile. Testing.

    def can_collide(self, entity, other):
        return False # Shouldn't resolve with anything.

    def collide_wall(self, entity, entity_container):
        entity.components['Action'].collide_wall(entity, entity_container) # Calls into exploding upon hitting wall.

class HeroProjectileGraphicsComponent(GraphicsComponent):

    def __init__(self, **kwargs):
        super(HeroProjectileGraphicsComponent, self).__init__(**kwargs)
        self.explosion_config = None # To save the randomly generated explosion color.

    def update_graphics(self, entity):
        r = random.random
        state = entity.components['Action'].state
        g = []
        if state == 'initial':
            g.append(Color())
            g.append(Ellipse(size=entity.size, pos=(entity.width/2, entity.height/2)))
        else:
            colors = self.generate_explosion()
            g.append(colors[0])
            g.append(Ellipse(size=(entity.width * 1.5, entity.height * 1.5), pos=(entity.width/2, entity.height/2)))
            #g.append(colors[1])
            #g.append(Ellipse(size=entity.size, pos=(entity.width/2, entity.height/2)))
            
        return g

    def generate_explosion(self):
        r = random.random
        if self.explosion_config == None:
            self.explosion_config = []
            self.explosion_config.append(Color(rgba=(1,r(),r(),1)))
            self.explosion_config.append(Color(rgba=(r(),r(),r(),0.2)))
            return self.explosion_config
        else:
            return self.explosion_config


# Belongs to the 'Hero' or 'test_hero' entity, as a projectile to fire.
class HeroProjectileActionComponentPROTOTYPE(ActionComponent):

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
            # The access to total velocity is unelegant.
            # Knockback code, knocks enemy back in average(pos_difference, projectile direction) direction.
            difference = (Vector(*other.pos) - Vector(*entity.pos)).normalize()
            entity_velocity = Vector(*entity.components['Physics'].total_velocity).normalize()
            knockback = (difference + entity_velocity) / 2
            other.velocity += knockback * 20 # The magnitude of the knockback.
            entity_container.remove_widget(entity) # Remove projectile after hitting something.

    # Can't be destroyed, destructible projectiles have 1 hp.
    def on_receive_damage(self, *args):
        pass

class HeroProjectileActionComponent(ActionComponent):

    def __init__(self, dmg=1):
        super(HeroProjectileActionComponent, self).__init__()
        self.damage = dmg
        self.states = ['initial', 'exploding', 'exploded']
        self.state = 'initial'
        self.explode_time = 0

    # No need for active effects on a projectile.
    def update(self, entity, game):
        if self.state == 'initial':
            entity.velocity_multiplier += (10 * 30) / 60 # Acceleration, 1st term is 'meter', where 10 pixels is a meter. 2nd is how many m/s acceleration.
        if self.explode_time > 0:
            self.state = 'exploded'
            Clock.schedule_once(lambda dt: game.e_container.remove_widget(entity), 0.2)

        if self.state == 'exploding':
            self.explode_time += 1

    def collide(self, entity, other, entity_container):
        if self.state == 'initial': 

            def death_memes(dt):
                self.explode(entity)
                self.state = 'exploding'

            if other.name in entity_container.enemies:
                death_memes(None)

            elif other.name == entity.name and other.components['Action'].state == 'exploding':
            # Temporary check for missiles exploding eachother, needs to be changed for different missile types.
                Clock.schedule_once(death_memes, 0.1)

            else:
                return None

        elif self.state == 'exploding': 

            if other.name in entity_container.enemies or other.name in entity_container.players:

                difference = Vector(*other.center) - Vector(*entity.center)
                #entity_velocity = Vector(*entity.components['Physics'].total_velocity).normalize()
                #knockback = (difference + entity_velocity) / 2
                # Above comments are pre explosion knockback code.
                percent = (difference.length() - other.width) / entity.width # Distance from center of explosion
                magnitude =  -15 * percent + 12 # The magnitude of the knockback.
                other.velocity += difference.normalize() * magnitude


            if other.name in entity_container.enemies:
                d = DamageInfo(entity, self.damage, 'projectile')
                other.receive_damage(d)


        elif self.state == 'exploded':
            entity.velocity_multiplier = 150 # Causes a 'blast' visual effect on the target.
            

    def explode(self, entity):
        c = [entity.center_x, entity.center_y][:]
        entity.size = (35, 35)
        entity.center = c
        entity.velocity_multiplier = 0
        entity.components['Physics'].can_collide_wall = False # So dirty access, better change, stops explosions from being resolved.

    def collide_wall(self, entity, entity_container): # Called from physics component.
        def death_memes(dt):
            self.explode(entity)
            self.state = 'exploding'
        Clock.schedule_once(death_memes, -1) # To stop explosion overlap from chain explosions, which can cause double explosions.

    # Can't be destroyed, destructible projectiles have 1 hp.
    def on_receive_damage(self, *args):
        pass



"""Below here are entity creation functions, includes:
components, entity, various attributes.
"""

# Window.center is to be changed to starting position on the game map
def create_hero(center, size=(16, 16)):
    # TODO: Add error checking if the name is not in any valid names.
    e = Entity(center=center, size=size)
    chardata = {'name': 'test_hero', 'max_hp': 20, 'hp': 20, 
        'velocity_multiplier': 300, 'attack_speed': 0.15
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

def create_hero_projectile(center, size=(6, 6), velocity_multiplier=100, target_pos=None): # target_pos is for missile curving.
    e = Entity(size=size)
    e.center = center
    chardata = {'name': 'test_projectile', 'max_hp': 1, 'hp': 1,
        'velocity_multiplier': velocity_multiplier, 'can_be_damaged': False
        }
    for key, val in chardata.items():
        e.__dict__[key] = val
    e.components['Input'] = None
    e.components['Physics'] = HeroProjectilePhysicsComponent(target_pos)
    e.components['Graphics'] = HeroProjectileGraphicsComponent()
    e.components['Action'] = HeroProjectileActionComponent()
    return e

def create_riot_police(center, size=(16, 16)):
    e = Entity(center=center, size=size)
    chardata = {'name': 'Riot Police', 'max_hp': 3, 'hp': 3, 'velocity_multiplier': 125,
        'contact_damage': 1, 'exp': 1
                }
    for key, val in chardata.items():
        e.__dict__[key] = val
    e.components['Input'] = RiotPoliceInputComponent()
    e.components['Physics'] = RiotPolicePhysicsComponent()
    e.components['Graphics'] = RiotPoliceGraphicsComponent()
    e.components['Action'] = RiotPoliceActionComponent()
    return e

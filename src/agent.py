#! /usr/bin/python3
"""
### Agent
Contains agent creation, rendering, behaviours.
"""
__all__ = []
__author__ = "aith"
__version__ = "1.0"

import math

from random import choice, random, choices, randint
from enum import Enum
import src.pathfinding
import src.states
import src.manipulation
import src.legal
import src.utils
import src.scheme_utils
import src.chronicle
import http_framework.interfaceUtils
import names
from random import shuffle


class Agent:
    P1_BUILDS = src.utils.STRUCTURES['decor'] + src.utils.STRUCTURES['small']
    P2_BUILDS = src.utils.STRUCTURES['decor'] + src.utils.STRUCTURES['decor'] + src.utils.STRUCTURES['decor'] + \
                src.utils.STRUCTURES['decor'] + src.utils.STRUCTURES['small'] + src.utils.STRUCTURES['med'] + \
                src.utils.STRUCTURES['med']
    P3_BUILDS = src.utils.STRUCTURES['decor'] + src.utils.STRUCTURES['med'] + src.utils.STRUCTURES['large']

    DELTA_TO_DIR_IDX = {
        (1, 0): 0,
        (0, 1): 1,
        (-1, 0): 2,
        (0, -1): 3,
        (1, 1): 4,
        (-1, 1): 5,
        (-1, -1): 6,
        (1, -1): 7,
        (1, -1): 7,
        (0, 0): 0,
    }

    class Motive(Enum):
        """
        Agent Actions
        """
        LOGGING = 0
        REST = 1
        SOCIALIZE_LOVER = 2
        SOCIALIZE_FRIEND = 3
        SOCIALIZE_ENEMY = 4
        BUILD = 5
        IDLE = 6
        WATER = 7
        REPLENISH_TREE = 8
        PROPAGATE = 9

    BASE_SOCIAL_SCORES = {
        Motive.SOCIALIZE_LOVER: 10,
        Motive.SOCIALIZE_FRIEND: 10,
        Motive.SOCIALIZE_ENEMY: 10,
    }

    # going first, doing second. Note: socializing is doubled bc 2 agents
    CHRONICLE_RATES = {
        Motive.LOGGING.name: (0.05, 0.02),
        Motive.BUILD.name: (0.1, 0.1),
        Motive.SOCIALIZE_LOVER.name: (0.0, 0.5),
        Motive.SOCIALIZE_FRIEND.name: (0.0, 0.5),
        Motive.SOCIALIZE_ENEMY.name: (0.0, 0.5),
        Motive.REST.name: (0.2, 0.00),
        Motive.REPLENISH_TREE.name: (0.0, 0.01),
        Motive.PROPAGATE.name: (0.0, 1.0),
        Motive.WATER.name: (0.0, 0.05),
        Motive.IDLE.name: (0.0, 0.00),
    }

    POSE = {
        0: {  # normal walk 1
            "Head": "350f,10f,0f",
            "LeftLeg": "30f,10f,0f",
            "RightLeg": "330f,10f,0f",
            "LeftArm": "50f,0f,0f",
            "RightArm": "310f,0f,0f",
        },
        1: {  # normal walk 2
            "Head": "350f,10f,0f",
            "LeftLeg": "330f,10f,0f",
            "RightLeg": "30f,10f,0f",
            "LeftArm": "310f,0f,0f",
            "RightArm": "50f,0f,0f",
        },
        2: {  # normal rest 3
            "Head": "40f,10f,0f",
            "LeftLeg": "0f,10f,0f",
            "RightLeg": "0f,10f,0f",
            "LeftArm": "0f,0f,0f",
            "RightArm": "0f,0f,0f",
        },
        3: {  # normal rest 4
            "Head": "45f,10f,0f",
            "LeftLeg": "0f,10f,0f",
            "RightLeg": "0f,10f,0f",
            "LeftArm": "0f,0f,0f",
            "RightArm": "0f,0f,0f",
        },
        4: {  # socialize lover 1
            "Head": "353f,10f,0f",
            "LeftLeg": "30f,10f,0f",
            "RightLeg": "0f,10f,0f",
            "LeftArm": "0f,0f,210f",
            "RightArm": "260f,0f,0f",
        },
        5: {  # socialize lover 2
            "Head": "359f,10f,0f",
            "LeftLeg": "40f,10f,0f",
            "RightLeg": "0f,10f,0f",
            "LeftArm": "0f,0f,190f",
            "RightArm": "250f,0f,0f",
        },
        6: {  # socialize friend 1
            "Head": "359f,10f,0f",
            "LeftLeg": "0f,10f,0f",
            "RightLeg": "0f,10f,0f",
            "LeftArm": "0f,0f,210f",
            "RightArm": "300f,0f,0f",
        },
        7: {  # socialize friend 2
            "Head": "354f,10f,0f",
            "LeftLeg": "0f,10f,0f",
            "RightLeg": "0f,10f,0f",
            "LeftArm": "0f,0f,190f",
            "RightArm": "290f,0f,0f",
        },
        8: {  # socialize enemy 1
            "Head": "0f,10f,0f",
            "LeftLeg": "0f,10f,0f",
            "RightLeg": "0f,10f,0f",
            "LeftArm": "200f,0f,0f",
            "RightArm": "260f,0f,0f",
        },
        9: {  # socialize enemy 2
            "Head": "0f,10f,0f",
            "LeftLeg": "0f,10f,0f",
            "RightLeg": "0f,10f,0f",
            "LeftArm": "260f,0f,0f",
            "RightArm": "200f,0f,0f",
        },
    }

    STAY_STILL_MAX_TURNS = 15
    SOCIALIZE_DURATION = 10

    shared_resource_list = [
        "oak_log",
        "dark_oak_log",
        "spruce_log",
        "birch_log",
        "acacia_log",
        "jungle_log",
    ]

    shared_resources = {
        "oak_log": 0,
        "dark_oak_log": 0,
        "spruce_log": 0,
        "birch_log": 0,
        "acacia_log": 0,
        "jungle_log": 0,
    }

    def __init__(self, state, state_x, state_z, walkable_heightmap, name, head, lover=None,
                 parent_1=None, parent_2=None, motive=Motive.LOGGING.name):

        # POSITION
        self.x = self.rendered_x = max(min(state_x, state.last_node_pointer_x), 0)
        self.z = self.rendered_z = max(min(state_z, state.last_node_pointer_z), 0)
        self.y = self.rendered_y = walkable_heightmap[state_x][state_z] + 0
        self.state = state
        self.node = self.state.nodes(*self.state.node_pointers[(self.x, self.z)])
        self.dx = self.dz = 1  # Movement since last step
        # IDENTITY
        self.name = name
        self.parent_1 = parent_1
        self.parent_2 = parent_2
        self.path = []
        self.motive = motive
        self.current_action_item = ""
        self.favorite_item = choice(src.utils.AGENT_ITEMS['FAVORITE'])
        self.head = head
        # RESOURCES
        self.water_max = 100
        self.water_decay = -0.3  # lose this per turn
        self.water_inc_rate = 10
        self.thirst_thresh = 50
        self.rest_decay = -0.4  # sprawl factor
        self.rest_inc_rate = 2
        self.rest_thresh = 30
        self.rest_max = 200  # 100
        self.happiness = 50
        self.happiness_max = 100
        self.happiness_decay = -0.05  # the inevitable creep of loneliness
        self.unshared_resources = {
            "water": self.water_max * 0.8,
            "rest": self.rest_max * random(),
            "happiness": self.happiness_max * 0.8
        }
        # MISC
        self.build_params = None
        self.building_material = ''
        self.build_cost = 0
        self.building_max_y_diff = 3
        self.inc_building_max_y_diff = 0
        self.tree_grow_iteration = 0
        self.tree_grow_iterations_max = randint(3, 5)
        self.tree_leaves_height = randint(5, 7)
        self.last_log_type = 'oak_log'
        self.is_placing_sapling = False
        self.turns_staying_still = 0
        self.walk_stage = 0  # whether moving left or right. do XOR with 1 and this
        self.is_resting = False
        # SOCIAL
        self.socialize_want = 0
        self.socialize_threshold = 20  # TODO change this
        self.socialize_partner = None
        self.found_and_moving_to_socialization = False  # _disables when either of the two found the other
        self.is_mid_socializing = False
        self.socialize_partner_pos = (0, 0)
        self.is_child_bearing = False
        self.courtship_requirement = 1  # number of times needed to interact with lover to propagate
        self.courtship_current = 0
        self.is_busy = False
        # OTHER AGENTS
        self.mutual_friends = set()
        self.mutual_enemies = set()
        self.lover = lover
        self.children = []

    def socialize(self, found_socialization):  #
        """
        Interact with other agents
        :param found_socialization:
        :return:
        """
        self.socialize_want += 1
        if self.socialize_want < self.socialize_threshold: return  # TODO unlock this somewhere
        if self.is_busy: return
        if found_socialization: return  # TODO unlock this somewhere
        for agent in list(self.state.agent_nodes[self.node.center] - {self}):
            if agent.socialize_want < agent.socialize_threshold: continue
            self.socialize_partner = agent
            agent.socialize_partner = self
            if found_socialization:
                return  # TODO unlock this somewhere
            elif agent == self.lover:
                self.set_motive(self.Motive.SOCIALIZE_LOVER)
                agent.set_motive(self.Motive.SOCIALIZE_LOVER)
            elif agent in self.mutual_friends:
                self.set_motive(self.Motive.SOCIALIZE_FRIEND)
                agent.set_motive(self.Motive.SOCIALIZE_FRIEND)
            elif agent in self.mutual_enemies:
                self.set_motive(self.Motive.SOCIALIZE_ENEMY)
                agent.set_motive(self.Motive.SOCIALIZE_ENEMY)
            else:  # form a new relationship
                if self.lover == None and agent.lover == None:
                    self.is_child_bearing = True
                    self.lover = agent
                    agent.lover = self
                    self.set_motive(self.Motive.SOCIALIZE_LOVER)
                    agent.set_motive(self.Motive.SOCIALIZE_LOVER)
                elif random() < 0.7:
                    self.mutual_friends.add(agent)
                    agent.mutual_friends.add(self)
                    self.set_motive(self.Motive.SOCIALIZE_FRIEND)
                    agent.set_motive(self.Motive.SOCIALIZE_FRIEND)
                else:
                    self.mutual_enemies.add(agent)
                    agent.mutual_enemies.add(self)
                    self.set_motive(self.Motive.SOCIALIZE_ENEMY)
                    agent.set_motive(self.Motive.SOCIALIZE_ENEMY)
            self.approach_agent(
                agent)  # go to path, and both agents interact once follow_path is done and friend nearby
            agent.await_agent(self)
            self.socialize_partner_pos = (agent.x, agent.z)
            agent.socialize_partner_pos = (self.x, self.z)
            self.found_and_moving_to_socialization = True  # put in this function
            agent.found_and_moving_to_socialization = True

    def approach_agent(self, agent):
        """
        Move towards socialization partner
        :param agent:
        :return:
        """
        self.set_path_to_nearest_of(agent, 3, 1, 0, search_neighbors_instead=True)
        l = len(self.path)
        if l > 3:  # error
            self.path.clear()
            agent.choose_motive()
            self.choose_motive()
        else:
            if l > 0: self.path.pop(0)
            self.found_and_moving_to_socialization = True
            agent.found_and_moving_to_socialization = True

    def socialize_with_lover(self):
        self.courtship_current += 1

    def complete_socialization(self):
        self.socialize_want = 0
        self.is_mid_socializing = False
        self.found_and_moving_to_socialization = False
        self.is_busy = False
        self.socialize_threshold += self.state.num_agents * 2

    def await_agent(self, agent):
        """
        Wait for other for 3 turns
        :param agent:
        :return:
        """
        self.path.clear()
        self.path.append((self.x, self.z))
        self.path.append((self.x, self.z))
        self.path.append((self.x, self.z))

    def set_lover(self, agent):
        self.lover = agent

    def do_socialize_task(self, agent, motive_str):
        """
        Perform socialization
        :param agent:
        :param motive_str:
        :return:
        """
        if motive_str == self.Motive.SOCIALIZE_LOVER.name:
            self.courtship_current += 1
            self.happiness += self.happiness_max * 0.3
        elif motive_str == self.Motive.SOCIALIZE_FRIEND.name:
            self.happiness += self.happiness_max * 0.3
        elif motive_str == self.Motive.SOCIALIZE_ENEMY.name:
            self.happiness -= self.happiness_max * 0.3
        self.path = [(self.x, self.z)] * Agent.SOCIALIZE_DURATION
        self.is_mid_socializing = True
        self.socialize_want = -Agent.SOCIALIZE_DURATION

    def do_build_task(self, found_road, ctrn_node, found_nodes, ctrn_dir, bld, rot, min_nodes_in_x, min_nodes_in_z,
                      built_arr, wood_type):
        """
        Perform Build task. Takes result of find_build_spot
        :return:
        """
        status, build_y = self.state.place_building(found_road, ctrn_node, found_nodes, ctrn_dir, bld, rot,
                                                    min_nodes_in_x, min_nodes_in_z, built_arr, wood_type)

    def choose_motive(self):
        """
        Find and set MOTIVE
        :return:
        """
        new_motive = self.calc_motive()
        self.set_motive(new_motive)

    def calc_motive(self):
        """
        Find motive by priority
        :return:
        """
        if self.unshared_resources['rest'] < self.rest_thresh:
            return self.Motive.REST
        elif self.unshared_resources['water'] < self.thirst_thresh:
            return self.Motive.WATER
        elif self.is_child_bearing and self.courtship_current >= self.courtship_requirement and self.state.num_agents < self.state.max_agents:
            return self.Motive.PROPAGATE
        elif self.state.generated_a_road and self.check_can_build(self.state.phase):
            return self.Motive.BUILD
        else:
            actions = (self.Motive.LOGGING, self.Motive.REPLENISH_TREE)
            weights = (10, 1)
            choice = choices(actions, weights, k=1)
            return choice[0]

    def check_can_build(self, phase):
        shuffle(Agent.shared_resource_list)  # decide random resource choice
        for key in Agent.shared_resource_list:
            amt = Agent.shared_resources[key]
            if amt <= self.state.build_minimum_phase_1:
                continue
            elif phase == 1:
                if amt > self.state.build_minimum_phase_1:
                    self.building_material = key
                    return True
            elif phase == 2:
                if amt > self.state.build_minimum_phase_2:
                    self.building_material = key
                    return True
            elif phase == 3:
                if amt > self.state.build_minimum_phase_3:
                    self.building_material = key
                    return True
            else:
                return False

    def get_appropriate_build(self, phase):
        """
        Pick a building based on Phase
        :param phase:
        :return:
        """
        rp = './schemes/'
        build = ''
        cost = 0  # TODO
        if phase == 1:
            pool = Agent.P1_BUILDS
            build, cost = choice(pool)
        elif phase == 2:
            pool = Agent.P2_BUILDS
            build, cost = choice(pool)
        elif phase == 3:
            pool = Agent.P3_BUILDS
            build, cost = choice(pool)
        else:
            print('error: incorrect phase')
            # exit(1)
        return rp + build, cost

    def move_self(self, new_x, new_z, state, walkable_heightmap):
        """
        Move agent
        :param new_x:
        :param new_z:
        :param state:
        :param walkable_heightmap:
        :return:
        """
        if self.state.out_of_bounds_Node(new_x, new_z):
            return
        self.update_node_occupancy(self.x, self.z, new_x, new_z)
        self.dx = (new_x - self.x) * (not self.is_mid_socializing) + (self.socialize_partner_pos[0] - self.x) * (
            self.is_mid_socializing)
        self.dz = (new_z - self.z) * (not self.is_mid_socializing) + (self.socialize_partner_pos[1] - self.z) * (
            self.is_mid_socializing)
        self.x = new_x
        self.z = new_z
        self.y = walkable_heightmap[new_x][new_z]
        self.state.add_prosperity(self.x, self.z, src.utils.ACTION_PROSPERITY.WALKING)
        self.state.agents[self] = (self.x, self.y, self.z)

    def update_node_occupancy(self, x1, z1, x2, z2):
        n1 = self.state.nodes(*self.state.node_pointers[(x1, z1)])
        n2 = self.state.nodes(*self.state.node_pointers[(x2, z2)])
        if n1 != n2:
            self.state.agent_nodes[n1.center].remove(self)
            self.state.agent_nodes[n2.center].add(self)
            self.node = n2

    def set_path(self, path):
        self.path = path

    def follow_path(self, state, walkable_heightmap):
        """
        Move forward in own path, performing appropriate action if destination reached
        :param state:
        :param walkable_heightmap:
        :return:
        """
        nx = nz = 0
        status = False
        if len(self.path) > 0:
            # MOVE FORWARD IN PATh
            nx, nz = self.path.pop()
            dx = max(min(nx - self.x, 1), -1)
            dz = max(min(nz - self.z, 1), -1)
            if self.state.legal_actions[self.x][self.z][
                self.DELTA_TO_DIR_IDX[(dx, dz)]] == 0:  # if not legal move (aka building was placed)
                self.choose_motive()
                return False
            self.move_self(nx, nz, state=state, walkable_heightmap=walkable_heightmap)
            self.turns_staying_still = 0
        else:
            # ACTION TREE
            original_motive = self.motive
            social_partner = self.socialize_partner
            if self.motive == self.Motive.REST.name:
                status = self.do_rest_task()
            if self.motive == self.Motive.WATER.name:
                self.is_busy = True
                status = self.do_water_task()
            if self.motive == self.Motive.BUILD.name:
                if self.build_params is None:
                    print("failed to get to build spot")
                else:
                    node_pos = self.build_params[1].center
                    self.dx = max(min(node_pos[0] - self.x, 1), -1)
                    self.dz = max(min(node_pos[1] - self.z, 1), -1)
                    self.do_build_task(*self.build_params)
                status = self.do_idle_task()
            elif self.motive == self.Motive.LOGGING.name:
                self.is_busy = True
                status = self.do_log_task()
            elif self.motive == self.Motive.REPLENISH_TREE.name:
                self.is_busy = True
                status = self.do_replenish_tree_task()
            elif self.motive == self.Motive.PROPAGATE.name:
                self.is_busy = True
                status = self.do_propagate_task()
            elif self.motive == self.Motive.SOCIALIZE_LOVER.name or self.motive == self.Motive.SOCIALIZE_FRIEND.name or self.motive == self.Motive.SOCIALIZE_ENEMY.name:
                if not self.is_mid_socializing:
                    if self.socialize_partner is None:  # there was an error so let's escape
                        self.complete_socialization()
                        self.choose_motive()
                    else:  # meet wait for agent
                        status, x, z = self.find_adjacent_agent(self.socialize_partner, 2, 2)
                        if status == src.manipulation.TASK_OUTCOME.SUCCESS:
                            self.do_socialize_task(self.socialize_partner, self.motive)
                            self.socialize_partner.do_socialize_task(self, self.motive)
                        elif status == src.manipulation.TASK_OUTCOME.IN_PROGRESS:
                            partner = self.socialize_partner
                            self.socialize_partner.complete_socialization()  # redundant but fixes edge cases
                            self.complete_socialization()
                            self.choose_motive()
                            partner.choose_motive()
                        else:  # in progress
                            pass
                else:
                    if len(self.path) > 0:
                        self.path.pop()
                    else:  # len(self.path) < 1:
                        self.socialize_partner.complete_socialization()  # redundant but fixes edge cases
                        self.complete_socialization()
                        self.choose_motive()
            elif self.motive == self.Motive.IDLE.name:
                self.is_mid_socializing = False
                status = self.do_idle_task()
            src.chronicle.chronicle_event(Agent.CHRONICLE_RATES[original_motive][1], original_motive, 'doing',
                                          self.state.step_number, self, social_partner)
        # STILLNESS CHECK
        if self.turns_staying_still > Agent.STAY_STILL_MAX_TURNS and status is False and self.motive != self.Motive.REST.name:  # _move in random direction if still for too long
            nx = nz = 0
            found_open = False
            for dir in src.legal.ALL_DIRS:
                nx = self.x + dir[0]
                nz = self.z + dir[1]
                ny = self.state.rel_ground_hm[nx][nz]
                if ny < self.state.rel_ground_hm[self.x][self.z]:  # only move down if possible
                    found_open = True
                    break
            if not found_open:
                nx, nz = choice(src.legal.ALL_DIRS)
                nx += self.x
                nz += self.z
            self.move_self(nx, nz, state=state, walkable_heightmap=walkable_heightmap)
            self.turns_staying_still = 0
        if nx == 0 and nz == 0:
            self.turns_staying_still += 1

    def find_adjacent_agent(self, agent, max_x, max_z):
        dx = agent.x - self.x
        dz = agent.z - self.z
        adx = abs(dx)
        adz = abs(dz)
        if adx <= 1 and adz <= 1:  # adjacent
            return src.manipulation.TASK_OUTCOME.SUCCESS, dx, dz
        if adx > max_x and adz > max_z:  # error
            return src.manipulation.TASK_OUTCOME.FAILURE, dx, dz
        else:
            return src.manipulation.TASK_OUTCOME.IN_PROGRESS, dx, dz

    def do_propagate_task(self):
        """
        Create an agent
        """
        self.courtship_current = 0
        self.lover.courtship_current = 0
        self.courtship_requirement += 1
        self.lover.courtship_requirement += 1

        empty_spot = (self.x, self.z)
        for dir in src.legal.ALL_DIRS:
            tx = self.x + dir[0]
            tz = self.z + dir[1]
            if self.state.sectors[tx][tz] == self.state.sectors[self.x][self.z]:
                empty_spot = (tx, tz)
                break

        child = Agent(self.state, *empty_spot, self.state.rel_ground_hm, name=names.get_first_name(),
                      head=choice(src.states.State.AGENT_HEADS), parent_1=self, parent_2=self.lover)
        self.state.add_agent(child)
        self.children.append(child)
        self.lover.children.append(child)
        self.set_motive(self.Motive.IDLE)
        return True

    def do_replenish_tree_task(self):
        """
        Perform REPLENISH task
        :return:
        """

        def is_in_state_saplings(state, x, y, z):
            result = (x, z) in state.saplings
            if self.state.blocks(x, self.state.static_ground_hm[x][z], z) in src.utils.BLOCK_TYPE.tile_sets[
                src.utils.TYPE.MAJOR_ROAD.value]:
                src.states.set_state_block(self.state, x, self.state.static_ground_hm[x][z] + 1, z, "minecraft:air")
                if (x, z) in state.saplings:
                    state.saplings.remove((x, z))
                result = False
            if result:
                if src.manipulation.is_log(state, x, y, z):
                    start = 0
                    if 'mine' in self.state.blocks(x, y, z)[:4]:
                        start = self.state.blocks(x, y, z).index(':') + 1
                    end = self.state.blocks(x, y, z).index('_')
                    src.manipulation.grow_type = self.state.blocks(x, y, z)[start:end]  # change replenish type
                elif src.manipulation.is_sapling(state, x, y + 1, z):
                    start = 0
                    if 'mine' in self.state.blocks(x, y + 1, z)[:4]:
                        start = self.state.blocks(x, y + 1, z).index(':') + 1
                    end = self.state.blocks(x, y + 1, z).index('_')
                    src.manipulation.grow_type = self.state.blocks(x, y + 1, z)[start:end]  # change replenish type
                else:
                    src.manipulation.grow_type = 'oak'
            return result

        if self.tree_grow_iteration < self.tree_grow_iterations_max + self.tree_leaves_height - 1:
            status, bx, bz = self.collect_from_adjacent_spot(self.state, check_func=is_in_state_saplings,
                                                             manip_func=src.manipulation.grow_tree_at,
                                                             prosperity_inc=src.utils.ACTION_PROSPERITY.REPLENISH_TREE)
            self.dx = bx - self.x
            self.dz = bz - self.z
            self.tree_grow_iteration += 1
            if status == src.manipulation.TASK_OUTCOME.FAILURE.name:
                self.tree_grow_iteration = 999  # so that they can go into else loop next run
            return True
        else:
            self.tree_grow_iteration = 0
            saps = set(self.state.saplings)
            for dir in src.legal.ALL_DIRS:  # remove sapling from state, add to trees instead
                x, z = (dir[0] + self.x, dir[1] + self.z)
                if self.state.out_of_bounds_2D(x, z): continue
                self.state.update_block_info(x, z)
                if (x, z) in saps:
                    self.state.saplings.remove((x, z))
                    leaf = 'minecraft:' + src.manipulation.grow_type + "_leaves[distance=7]"
                    src.manipulation.grow_leaves(self.state, x, self.state.rel_ground_hm[x][z], z, leaf,
                                                 leaves_height=self.tree_leaves_height)
                if src.manipulation.is_log(self.state, x, self.state.rel_ground_hm[x][z] - 1, z):
                    self.state.trees.append((x, z))
            self.set_motive(self.Motive.IDLE)
            return False

    def do_idle_task(self):
        """
        Safely reset MOTIVE
        :return:
        """
        self.choose_motive()
        return False

    def do_rest_task(self):
        """
        Perform REST action
        :return:
        """
        if self.unshared_resources['rest'] < self.rest_max:  # self.calc_motive() == self.Motive.REST:
            self.unshared_resources['rest'] += self.rest_inc_rate
            self.is_resting = True
            self.is_busy = True
            return True
        else:
            self.is_resting = False
            self.set_motive(self.Motive.IDLE)
            return False

    def do_water_task(self):
        """
        Perform WATER collection action
        :return:
        """
        if self.unshared_resources['water'] < self.water_max:  # and self.calc_motive() == self.Motive.WATER :
            status, sx, sz = self.collect_from_adjacent_spot(self.state, check_func=src.manipulation.is_water,
                                                             manip_func=src.manipulation.collect_water_at,
                                                             prosperity_inc=src.utils.ACTION_PROSPERITY.WATER)  # this may not inc an int
            self.dx = sx - self.x
            self.dz = sz - self.z
            if status == src.manipulation.TASK_OUTCOME.SUCCESS.name:
                self.unshared_resources['water'] += self.water_inc_rate
                return True
            elif status == src.manipulation.TASK_OUTCOME.FAILURE.name:  # if no water found
                self.set_motive(self.Motive.IDLE)
                return False
            return True  # in prograss
        else:
            self.set_motive(self.Motive.IDLE)
            return True

    def do_log_task(self):
        """
        Perform LOG tree action
        :return:
        """
        status, sx, sz = self.collect_from_adjacent_spot(self.state, check_func=src.manipulation.is_log,
                                                         manip_func=src.manipulation.cut_tree_at,
                                                         prosperity_inc=src.utils.ACTION_PROSPERITY.LOGGING)
        # get log type
        y = self.state.rel_ground_hm[sx][sz]
        if y - 1 >= 0:
            if src.manipulation.is_log(self.state, sx, y, sz):
                self.last_log_type = self.state.blocks(sx, y, sz)
                if self.last_log_type[:2] == "mi":
                    self.last_log_type = self.last_log_type[10:]
        # face tree
        self.dx = sx - self.x
        self.dz = sz - self.z
        if status == src.manipulation.TASK_OUTCOME.SUCCESS.name:
            src.agent.Agent.shared_resources[self.last_log_type] += 1
            self.set_motive(self.Motive.IDLE)
            return True
        elif status == src.manipulation.TASK_OUTCOME.FAILURE.name:  # if they got sniped
            for dir in src.legal.ALL_DIRS + ([0, 0],):
                point = (dir[0] + self.x, dir[1] + self.z)
                if point in self.state.trees:
                    self.state.trees.remove(point)
                if self.state.out_of_bounds_2D(*point): continue
                self.state.update_block_info(*point)
            self.set_motive(self.Motive.IDLE)
            return False
        else:
            src.agent.Agent.shared_resources[self.last_log_type] += 1
            return True

    # prepares for motive
    def set_motive(self, new_motive: Enum):
        """
        Set own MOTIVE and relevant information
        :param new_motive:
        :return:
        """
        self.is_resting = False
        self.is_busy = False
        self.motive = new_motive.name
        if self.motive in src.utils.AGENT_ITEMS:
            self.current_action_item = choice(src.utils.AGENT_ITEMS[self.motive])
        # MOTIVE TREE
        if new_motive.name == self.Motive.REST.name:
            places = list(self.state.built_heightmap.keys())
            self.set_path_to_nearest_of(places, 30, 10, 20, search_neighbors_instead=False)
            if len(self.path) < 1:
                self.turns_staying_still = self.STAY_STILL_MAX_TURNS
                self.unshared_resources[
                    'rest'] = self.rest_max  # this is a fallback needed for 1000x1000 optimizaiton, unfortunately
                self.do_idle_task()
        elif new_motive.name == self.Motive.WATER.name:
            self.set_path_to_nearest_of(self.state.water_near_land, 10, 10, 30, search_neighbors_instead=True)
            if len(self.path) < 1:
                self.turns_staying_still = self.STAY_STILL_MAX_TURNS
                self.unshared_resources[
                    'water'] = self.water_max  # this is a fallback needed for 1000x1000 optimizaiton, unfortunately
                self.do_idle_task()
        elif new_motive.name == self.Motive.BUILD.name:
            building, cost = self.get_appropriate_build(self.state.phase)
            result = self.state.find_build_spot(self.x, self.z, building, self.building_material[:-4],
                                                self.building_max_y_diff)
            # now move to the road
            if result:
                print(f"  {self.name} is building: {building[10:]}")
                self.build_params = result
                tx, tz = result[0].center
                path = self.state.pathfinder.search((self.x, self.z), (tx, tz), self.state.len_x, self.state.len_z,
                                                    self.state.legal_actions)
                self.build_cost = cost
                self.shared_resources[self.building_material] -= cost  # preemptively apply cost to avoid races
                self.is_busy = True
                self.set_path(path)
            else:
                # if it's been too hard to find a spot due to max_y_diff, increase it
                self.inc_building_max_y_diff += 1
                if self.inc_building_max_y_diff > 20:
                    self.building_max_y_diff = min(self.building_max_y_diff + 1, 5)
                    self.inc_building_max_y_diff = 0
                # there are no build spots. so let's do something else
                self.set_motive(self.Motive.LOGGING)
        elif new_motive.name == self.Motive.LOGGING.name:
            self.set_path_to_nearest_of(self.state.trees, 5, 9, 5,
                                        search_neighbors_instead=True)  # this affects spawl
            if len(self.path) < 1:  # if no trees were found
                self.set_motive(self.Motive.REPLENISH_TREE)
        elif new_motive.name == self.Motive.REPLENISH_TREE.name:
            new_spot_chance = random()
            # try for a totally new spot
            status = False
            if new_spot_chance > 0.5:
                nx = min(max(self.x + randint(-15, 15), 0), self.state.last_node_pointer_x)
                nz = min(max(self.z + randint(-15, 15), 0), self.state.last_node_pointer_z)
                if self.state.nodes(*self.state.node_pointers[(nx, nz)]) not in self.state.road_nodes:
                    status = self.set_path_to_nearest_of({(nx, nz)}, 60, 1, 1, search_neighbors_instead=True)

            # reuse a sapling spot
            if status == False: status = self.set_path_to_nearest_of(self.state.saplings, 10, 10, 10,
                                                                     search_neighbors_instead=True)
            if status == False:  # could not find sapling, so let's place one
                # choose random location that isn't in roads or built
                tries = 0
                max_tries = 50
                rad = 30
                tx = tz = 0
                node = None
                while node == None or tries < max_tries or node in self.state.built or node in self.state.roads:
                    tx = randint(self.x - rad, self.x + rad)
                    tz = randint(self.z - rad, self.z + rad)
                    if self.state.out_of_bounds_Node(tx, tz): continue
                    node = self.state.nodes(*self.state.node_pointers[(tx, tz)])
                    tries += 1
                if tries > max_tries:
                    tx = self.x
                    tz = self.z
                self.state.saplings.append((tx, tz))
                path = self.state.pathfinder.search((self.x, self.z), (tx, tz), self.state.len_x, self.state.len_z,
                                                    self.state.legal_actions)
                self.set_path(path)
                self.is_placing_sapling = True
            # self.is_busy = True  # dont get interrupted because operations were expensive
        elif new_motive.name == self.Motive.PROPAGATE.name:
            # TODO go to own house instead?
            places = list(self.state.built_heightmap.keys())
            self.set_path_to_nearest_of(places, 30, 10, 20, search_neighbors_instead=False)
        elif new_motive.name == self.Motive.SOCIALIZE_LOVER.name:
            pass
        elif new_motive.name == self.Motive.SOCIALIZE_ENEMY.name:
            pass
        elif new_motive.name == self.Motive.SOCIALIZE_FRIEND.name:
            pass
        elif new_motive.name == self.Motive.IDLE.name:  # just let it go into follow_path
            pass
        src.chronicle.chronicle_event(Agent.CHRONICLE_RATES[new_motive.name][0], new_motive.name, 'going',
                                      self.state.step_number, self)

    def set_path_to_nearest_of(self, search_array, starting_search_radius, max_iterations, radius_inc=1,
                               search_neighbors_instead=True):
        """
        Set own path to the nearest of a given array. Return True on success
        :param search_array:
        :param starting_search_radius:
        :param max_iterations:
        :param radius_inc:
        :param search_neighbors_instead:
        :return:
        """
        closed = set()
        for i in range(max_iterations):
            spots = src.pathfinding.find_nearest(self.state, self.x, self.z, search_array,
                                                 starting_search_radius + radius_inc * i, 1, radius_inc)
            if spots == [] or spots is None: continue
            while len(spots) > 0:
                chosen_spot = choice(spots)
                spots.remove(chosen_spot)
                if chosen_spot in closed:
                    continue
                # see if theres a path to an adjacent tile
                if search_neighbors_instead == True:
                    for pos in src.legal.get_pos_adjacents(self.state, *chosen_spot):
                        if self.state.sectors[pos[0], pos[1]] == self.state.sectors[self.x][self.z]:
                            path = self.state.pathfinder.search((self.x, self.z), pos, self.state.len_x,
                                                                self.state.len_z, self.state.legal_actions)
                            self.set_path(path)
                            return True
                    closed.add(chosen_spot)
                else:
                    if self.state.sectors[chosen_spot[0]][chosen_spot[1]] == self.state.sectors[self.x][self.z]:
                        path = self.state.pathfinder.search((self.x, self.z), (chosen_spot[0], chosen_spot[1]),
                                                            self.state.len_x, self.state.len_z,
                                                            self.state.legal_actions)
                        self.set_path(path)
                        return True
                    closed.add(chosen_spot)
        self.set_path([])  # FAILURE
        return False

    def collect_from_adjacent_spot(self, state, check_func, manip_func, prosperity_inc):
        """
        Perform given function on adjacent blocks
        :param state:
        :param check_func:
        :param manip_func:
        :param prosperity_inc:
        :return:
        """
        status = src.manipulation.TASK_OUTCOME.FAILURE.name
        for dir in src.legal.ALL_DIRS:
            xo, zo = dir
            bx = self.x + xo
            bz = self.z + zo
            if self.state.out_of_bounds_Node(bx, bz):
                continue
            by = int(state.abs_ground_hm[bx][bz]) - self.state.world_y  # this isn't being updated in heightmap
            if check_func(self.state, bx, by, bz):
                status = manip_func(self.state, bx, by, bz)
                state.add_prosperity(bx, bz, prosperity_inc)
                return status, bx, bz
        return status, 0, 0  # someone sniped this tree.

    def render(self):
        kill_cmd = """kill @e[name={name}]""".format(name=self.name)
        http_framework.interfaceUtils.runCommand(kill_cmd)
        R = self.is_resting * 2
        S = self.is_mid_socializing * ((self.motive == self.Motive.SOCIALIZE_LOVER.name) * 4) + (
                (self.motive == self.Motive.SOCIALIZE_FRIEND.name) * 6) + (
                    (self.motive == self.Motive.SOCIALIZE_ENEMY.name) * 8)
        self.walk_stage = min(((self.walk_stage - R > 0) ^ 1) + R + S, 9)  # flip bit
        # RENDERING COMMAND
        spawn_cmd = """\
summon minecraft:armor_stand {x} {y} {z} {{NoGravity: 1, ShowArms:1, NoBasePlate:1, CustomNameVisible:1, Rotation:[{rot}f,0f,0f], \
mall:{is_small}, CustomName: '{{"text":"{name}", "color":"customcolor", "bold":false, "underlined":false, \
"strikethrough":false, "italic":false, "obscurated":false}}', \
ArmorItems:[{{id:"{boots}",Count:1b}},\
{{id:"{lower_armor}",Count:1b,tag:{{display:{{color:{lower_armor_color}}}}}}},\
{{id:"{upper_armor}",Count:1b,tag:{{display:{{color:{upper_armor_color}}}}}}},\
{{id:"player_head",Count:1b,tag:{{{head}}}}}],\
HandItems:[{{id:"{hand1}", Count:1b}},{{id:"{hand2}", Count:1b}}],\
Pose:{{ \
Head:[{head_rot}], \
LeftLeg:[{left_leg}], \
RightLeg:[{right_leg}], \
LeftArm:[{left_arm}], \
RightArm:[{right_arm}]}}\
}}\
""".format(
            x=self.x + self.state.world_x,
            y=self.y + self.state.world_y,
            z=self.z + self.state.world_z,
            rot=src.utils.ROTATION_LOOKUP[max(min(self.dx, 1), -1, -1), max(min(self.dz, 1), -1)],
            name=self.name,
            is_small="false",
            head=self.head,
            boots=src.utils.BOOTS[self.state.phase],
            upper_armor="leather_chestplate",
            upper_armor_color=self.state.flag_color[1],
            lower_armor="leather_leggings",
            lower_armor_color=self.state.flag_color[1],
            hand1=self.current_action_item,
            hand2=self.favorite_item,
            head_rot=Agent.POSE[self.walk_stage]["Head"],
            left_leg=Agent.POSE[self.walk_stage]["LeftLeg"],
            right_leg=Agent.POSE[self.walk_stage]["RightLeg"],
            left_arm=Agent.POSE[self.walk_stage]["LeftArm"],
            right_arm=Agent.POSE[self.walk_stage]["RightArm"],
        )  # this can be related to resources! 330 is high, 400 is low
        http_framework.interfaceUtils.runCommand(spawn_cmd)

    def get_head_tilt(self):
        if self.is_resting:
            return '45'
        else:
            return '350'

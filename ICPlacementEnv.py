import random
import json
from typing import List
import gym
from gym import spaces
import pandas as pd
import numpy as np
from typing import List, Optional, Tuple
import rectangle_packing_solver as rps
from rectangle_packing_solver import SequencePair


class ICPlacementEnv(gym.Env):
    """A IC Placement environment for OpenAI gym"""
    metadata = {'render.modes': ['human']}

    def __init__(self, problem, state, block_idx, step_size=200, sa_count=5000):
        super(ICPlacementEnv, self).__init__()

        self.problem = problem
        self.state = state
        self.curblock = block_idx
        self.current_step = 0
        self.total_ppo = step_size
        self.current_epoc = 0
        self.sa_count = sa_count

        '''
        action space consists of choosing a candidate block bc from all blocks in response
        to the current Pseq and the input block bi
        . The agent eventually learns to select a candidate
        block such that the Pseq generated after a series of swaps between the candidate block bc
        and the input block bi results in a better initialization for SA.
        '''
        self.action_space = spaces.Discrete(problem.n)

        # observation space
        self.observation_space = spaces.Box(
            low=0, high=problem.n - 1, shape=(3, problem.n), dtype=np.int32)

    def _next_observation(self):
        #
        obsIdx = self.curblock
        while True:
            obsIdx = random.randint(0, self.problem.n)
            if obsIdx != self.curblock:
                break

        self.curblock = obsIdx

        gp, gn, rotation = self.retrieve_pairs(self.problem.n, self.state)

        # one hot encoding
        inputblock = [0 for _ in range(self.problem.n)]
        for i in range(len(inputblock)):
            if i == obsIdx:
                inputblock[i] = 1
                break

        obs = np.array([gp, gn, inputblock])

        return obs
    
    def _take_action(self, action):
        # Swap the current block and candidate block, set the current block
        gp, gn, rotation = self.retrieve_pairs(self.problem.n, self.state)
        initial_state: List[int] = self.state[:]

        curblockIdx = 0
        obsblokIdx = 0
        for i in range(len(gp)):
            if gp[i] == self.curblock:
                curblockIdx = i
                break

        for i in range(len(gp)):
            if gp[i] == action:
                obsblokIdx = i
                break

        # swap two
        self.state[curblockIdx], self.state[obsblokIdx] = initial_state[obsblokIdx], initial_state[curblockIdx]

        curblockIdx = 0
        obsblokIdx = 0
        for i in range(len(gn)):
            if gp[i] == self.curblock:
                curblockIdx = i
                break

        for i in range(len(gn)):
            if gp[i] == action:
                obsblokIdx = i
                break

        # swap two
        self.state[curblockIdx + self.problem.n], self.state[obsblokIdx + self.problem.n] = initial_state[obsblokIdx + self.problem.n], initial_state[curblockIdx + self.problem.n]

    def step(self, action):
        # Execute one time step within the environment
        gp_old, gn_old, rotation_old = self.retrieve_pairs(self.problem.n, self.state)
        seqpair_old = SequencePair(pair=(gp_old, gn_old))
        floorplan_old = seqpair_old.decode(problem=self.problem, rotations=rotation_old)
        # take the action
        self._take_action(action)

        # at the first loop of each epoc, let's calcuate the cost function first for the global reward
        if self.current_step == 0:
            self.prevCost = float(floorplan_old.area)

        self.current_step += 1

        # get new observation
        obs = self._next_observation()
        gp_new, gn_new, rotation_new = self.retrieve_pairs(self.problem.n, self.state)

        if self.current_step < self.total_ppo:
            done = False

            # calculate the reward based on the new and old sequence pairs
            seqpair_new = SequencePair(pair=(gp_new, gn_new))
            floorplan_new = seqpair_new.decode(problem=self.problem, rotations=rotation_new)

            # difference of two costs functions will be the reward
            reward = float(floorplan_new.area) - float(floorplan_old.area)
        else:
            self.current_epoc += 1
            print(f'End of Epoc: {self.current_epoc}')

            done = True
            solution = rps.Solver().solve(problem=self.problem, init_gp=gp_new, init_gn=gn_new, simanneal_minutes=1.0,
                                          simanneal_steps=self.sa_count)

            reward = float(solution.floorplan.area) - self.prevCost

            print(f'Epoc: {self.current_epoc} Soulution : {solution}')

            self.render()

        #reward = -reward

        return obs, reward, done, {}

    def reset(self):
        # Reset the state of the environment to an initial state
        self.current_step = 0
        self.curblock = random.randint(0, self.problem.n)
        init_gp = list(range(self.problem.n))
        init_gn = list(range(self.problem.n))
        random.shuffle(init_gp)
        random.shuffle(init_gn)
        init_rot = [0 for _ in range(self.problem.n)]
        init_state = init_gp + init_gn + init_rot
        self.state = init_state

        return self._next_observation()

    def render(self, mode='human', close=False):
        # Render the environment to the screen
        pass

    @classmethod
    def retrieve_pairs(cls, n: int, state: List[int]) -> Tuple[List[int], List[int], List[int]]:
        """
        Retrieve G_{+}, G_{-}, and rotations from a state.
        """
        gp = state[0:n]
        gn = state[n : 2 * n]
        rotations = state[2 * n : 3 * n]
        return (gp, gn, rotations)

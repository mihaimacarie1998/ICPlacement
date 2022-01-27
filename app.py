from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common.vec_env import SubprocVecEnv
from stable_baselines import PPO2

import ICPlacementEnv
import rectangle_packing_solver as rps
import random
from typing import Dict, List
from flask import Flask, jsonify, request
import json
import hashlib
import time
import threading


app = Flask(__name__)

SA_STEP = 100
N_STEPS = 200
N_EPOCH = 4


CONST_STR_WIDTH = "width"
CONST_STR_HEIGHT = "height"
CONST_STR_TOP = "top"
CONST_STR_BOTTOM = "bottom"
CONST_STR_LEFT = "left"
CONST_STR_RIGHT = "right"
CONST_STR_COMPONENTS = "Components"
CONST_STR_PREDEFINED_BLOCKS = "PreDefinedBlocks"
CONST_STR_TOP_LAYER = "TopLayer"
CONST_STR_BOTTOM_LAYER = "BottomLayer"
CONST_STR_EPOCH = "Epoch"
CONST_STR_SA_COUNTS = "SACount"
CONST_STR_RL_AGENT_STEPS = "RLSteps"


def _create_dummy_problem() -> Dict:
    random.seed(1337)

    range_width = (10, 50)
    range_height = (10, 50)

    # Let's create the dummy components with Dict, this one will be provided through the API calls
    components_t = []
    components_b = []
    fixed_blocks_t = []
    fixed_blocks_b = []

    for _ in range(0, 10):
        components_t.append({
            CONST_STR_WIDTH: random.randint(range_width[0], range_width[1]),
            CONST_STR_HEIGHT: random.randint(range_height[0], range_height[1]),
        })

        components_b.append({
            CONST_STR_WIDTH: random.randint(range_width[0], range_width[1]),
            CONST_STR_HEIGHT: random.randint(range_height[0], range_height[1]),
        })

    fixed_blocks_t.append({
        CONST_STR_TOP: 180,
        CONST_STR_BOTTOM: 80,
        CONST_STR_LEFT: 150,
        CONST_STR_RIGHT: 210,
    })
    fixed_blocks_b.append({
        CONST_STR_TOP: 180,
        CONST_STR_BOTTOM: 80,
        CONST_STR_LEFT: 150,
        CONST_STR_RIGHT: 210,
    })

    return {
        CONST_STR_TOP_LAYER:
            {
                CONST_STR_COMPONENTS: components_t,
                CONST_STR_PREDEFINED_BLOCKS: fixed_blocks_t,
            },
        CONST_STR_BOTTOM_LAYER:
            {
                CONST_STR_COMPONENTS: components_b,
                CONST_STR_PREDEFINED_BLOCKS: fixed_blocks_b,
            },
        CONST_STR_EPOCH: N_EPOCH,
        CONST_STR_SA_COUNTS: SA_STEP,
        CONST_STR_RL_AGENT_STEPS: N_STEPS,
    }


class ICPlacement:
    def __init__(self, problems_: Dict):
        self.problems = problems_
        self.top = False
        self.b_createfile = True

    @classmethod
    def _check_fixed_blocks(cls, components: List[Dict]) -> bool:
        for i in range(len(components)):
            for j in range(i + 1, len(components)):
                block_i = components[i]
                block_j = components[j]

                # check if two blocks are overlapped or not
                try:
                    if (block_i["left"] < block_j["right"]) and (block_i["right"] > block_j["left"]) \
                            and (block_i["top"] > block_j["bottom"]) and (block_i["bottom"] < block_j["top"]):
                        return False
                except Exception as e:
                    print(f"Error was occurred while checking if pre defined blocks are overlapped or not. {e}")
        return True

    def _get_optimized_placement(self, problem: rps.Problem, top) -> rps.Solution:
        # Define the sequence pair, this pair will be defined outside later
        init_gp = list(range(problem.n))
        init_gn = list(range(problem.n))
        random.shuffle(init_gp)
        random.shuffle(init_gn)
        init_rot = [0 for _ in range(problem.n)]
        init_state = init_gp + init_gn + init_rot

        # set #epoch
        n_epoch = N_EPOCH
        if self.problems.get(CONST_STR_EPOCH) is not None:
            n_epoch = self.problems[CONST_STR_EPOCH]

        # set # RL agent steps
        n_steps = N_STEPS
        if self.problems.get(CONST_STR_RL_AGENT_STEPS) is not None:
            n_steps = self.problems[CONST_STR_RL_AGENT_STEPS]

        # set # SA steps
        n_sa_count = SA_STEP
        if self.problems.get(CONST_STR_SA_COUNTS) is not None:
            n_sa_count = self.problems[CONST_STR_SA_COUNTS]

        # result when using pure SA algorithm
        '''
        solution = rps.Solver().solve(problem=problem, simanneal_minutes=1.0, simanneal_steps=n_sa_count)
        if self.b_createfile is True:
            path = "./figs/floorplan_pure_sa_t.png"
            if top is True:
                path = "./figs/floorplan_pure_sa_b.png"

            rps.Visualizer().visualize(solution=solution, fixed_blocks=problem.fixed_blocks, path=path)
        print("solution Pure SA:", solution)
        '''

        init_block_idx = random.randint(0, problem.n)

        # The algorithms require a vectorized environment to run
        env = SubprocVecEnv([lambda: ICPlacementEnv.ICPlacementEnv(problem, init_state, init_block_idx, n_steps, n_sa_count), lambda: ICPlacementEnv.ICPlacementEnv(problem, init_state, init_block_idx, n_steps, n_sa_count)
                                , lambda: ICPlacementEnv.ICPlacementEnv(problem, init_state, init_block_idx, n_steps, n_sa_count), lambda: ICPlacementEnv.ICPlacementEnv(problem, init_state, init_block_idx, n_steps, n_sa_count)])
        model = PPO2(MlpPolicy, env, n_steps=n_steps)

        print("problem:", problem)

        model.learn(total_timesteps=n_epoch * n_steps)
        obs = env.reset()

        # result when trained by using RL and SA
        action, _states = model.predict(obs)
        obs, rewards, done, info = env.step(action)
        solution = rps.Solver().solve(problem=problem, init_gp=obs[0][0].tolist(), init_gn=obs[0][1].tolist(), simanneal_minutes=1.0, simanneal_steps=n_sa_count)

        '''
        if self.b_createfile is True:
            path = "./figs/floorplan_RL_t.png"
            if top is True:
                path = "./figs/floorplan_RL_b.png"

            rps.Visualizer().visualize(solution=solution, fixed_blocks=problem.fixed_blocks, path=path)
        print("solution RL:", solution)
        '''

        return solution

    def get_result(self) -> Dict:
        try:
            blocks_t = self.problems["TopLayer"]
            blocks_b = self.problems["BottomLayer"]

            if (blocks_t is not None) and (blocks_t.get(CONST_STR_PREDEFINED_BLOCKS) is not None):
                if self._check_fixed_blocks(blocks_t[CONST_STR_PREDEFINED_BLOCKS]) is False:
                    print("Pre defined blocks are overlapped")
                    exit(0)

            if (blocks_b is not None) and (blocks_b.get(CONST_STR_PREDEFINED_BLOCKS) is not None):
                if self._check_fixed_blocks(blocks_b[CONST_STR_PREDEFINED_BLOCKS]) is False:
                    print("Pre defined blocks are overlapped")
                    exit(0)

            solution_t = None
            if (blocks_t is not None) and blocks_t.get(CONST_STR_COMPONENTS) is not None:
                # Define the problems first, assumes that 20 components with different widths and heights are generated for testing
                problem_t = rps.Problem(rectangles=blocks_t[CONST_STR_COMPONENTS], fixed_blocks=blocks_t[CONST_STR_PREDEFINED_BLOCKS])
                solution_t = self._get_optimized_placement(problem_t, False)

            solution_b = None
            if (blocks_t is not None) and blocks_b.get(CONST_STR_COMPONENTS) is not None:
                # Define the problems first, assumes that 20 components with different widths and heights are generated for testing
                problem_b = rps.Problem(rectangles=blocks_b[CONST_STR_COMPONENTS], fixed_blocks=blocks_b[CONST_STR_PREDEFINED_BLOCKS])
                solution_b = self._get_optimized_placement(problem_b, True)

            return {
                CONST_STR_TOP_LAYER:
                    {
                        "positions": str(solution_t.floorplan.positions),
                        "bounding_box": str(solution_t.floorplan.bounding_box),
                        "area": str(solution_t.floorplan.area)
                    },
                CONST_STR_BOTTOM_LAYER:
                    {
                        "positions": str(solution_b.floorplan.positions),
                        "bounding_box": str(solution_b.floorplan.bounding_box),
                        "area": str(solution_b.floorplan.area)
                    },
            }
        except Exception as e:
            print(f"{e}")
            return {
                CONST_STR_TOP_LAYER: None,
                CONST_STR_BOTTOM_LAYER: None,
            }


# ## Run it
'''
if __name__ == "__main__":
    problems = _create_dummy_problem()
    placement = ICPlacement(problems)
    result = placement.get_result()
    print(result)
'''


@app.route('/')
def hello_world():
    return 'Hello World!'


placement_dict = {}


def solving_problems():
    while True:
        try:
            time.sleep(1)
            for key, value in placement_dict.items():
                try:
                    if value['status'] is not 0:
                        continue
                    value['status'] = 1
                    placement = ICPlacement(value['problems'])
                    value['result'] = placement.get_result()
                    value['status'] = 2
                except Exception as e:
                    value['status'] = 3
                    value['error'] = str(e)
        except Exception as e:
            print(str(e))


def run_solving_problems():
    try:
        thread = threading.Thread(target=solving_problems)
        thread.start()
    except Exception as e:
        print(str(e))


@app.route('/ICPlacement', methods=['GET', 'POST'])
def ic_placement():
    try:
        content = request.get_json()
        if 'problems_id' in content:
            prob_id = content['problems_id']
            if prob_id in placement_dict:
                task = placement_dict[prob_id]
                if task['status'] is 0:
                    result = {'problems_id': prob_id, 'status': "Not started yet", 'result': None}
                elif task['status'] is 1:
                    result = {'problems_id': prob_id, 'status': "Still running", 'result': None}
                elif task['status'] is 2:
                    result = {'problems_id': prob_id, 'status': "Success", 'result': task['result']}
                elif task['status'] is 3:
                    result = {'problems_id': prob_id, 'status': "Failed", 'result': task['error']}
                else:
                    result = {'problems_id': prob_id, 'status': "Failed", 'result': 'Unknown'}
                return jsonify(result)
            else:
                result = {'problems_id': prob_id, 'status': "doesn't exist", 'result': None}
                return jsonify(result)
        elif 'problems' not in content:
            result = {'status': 'Unknown json'}
            return jsonify(result)

        problems = content["problems"]
        str_problems = str(problems)
        hash_obj = hashlib.sha256(str(str_problems).encode('utf-8'))
        str_hash = str(hash_obj.hexdigest())
        result = {'problems_id': str_hash, 'status': 'Already existed problems'}
        if str_hash in placement_dict:
            return jsonify(result)
        new_task = {'problems': problems, 'status': 0, 'result': None, 'error': ''}  # 0: not started yet, 1: running, 2: success, 3: failed
        placement_dict[str_hash] = new_task
        result['status'] = 'Pushed new task'
        return jsonify(result)
    except Exception as e:
        print("ICPlacement request error:" + str(e))
        return jsonify(str(e))


run_solving_problems()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

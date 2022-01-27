import random
from typing import Dict, List
import json


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


# ## Run it
if __name__ == "__main__":
    problems = _create_dummy_problem()
    import requests
    url = 'http://localhost:80/ICPlacement'
    problems = {'problems': problems}
    resp = requests.post(url, json=problems)
    if resp.status_code is 200:
        result = json.loads(resp.text)
        prob_id = result['problems_id']
        if 'status' in result and result['status'] is not None:
            print(result['status'])
        prob_id = {'problems_id': prob_id}
        task = requests.post(url, json=prob_id)
        if task.status_code is 200:
            result = json.loads(task.text)
            if 'status' in result and result['status'] is not None:
                print(result['status'])
            if 'result' in result and result['result'] is not None:
                print(str(result['result']))
        else:
            print(resp.reason)
    else:
        print(resp.reason)



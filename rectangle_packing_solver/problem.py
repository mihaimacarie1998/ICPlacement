# Copyright 2021 Kotaro Terada
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Dict, List, Tuple, Union


class Problem:
    """
    A class to represent a rectangle packing problem.
    """

    def __init__(self, rectangles: List[Union[Dict, List, Tuple]], fixed_blocks: List[Union[Dict, List, Tuple]] = None) -> None:
        self.rectangles = []
        self.fixed_blocks = []
        self.n = 0
        self.nblocks = 0

        if not isinstance(rectangles, list):
            raise TypeError("Invalid argument: 'rectangles' must be a list.")

        if fixed_blocks is not None:
            for r in fixed_blocks:
                if isinstance(r, (list, tuple)):
                    self.fixed_blocks.append(
                        {
                            "id": self.nblocks,
                            "top": r[0],
                            "left": r[1],
                            "right": r[2],
                            "bottom": r[3],
                        }
                    )
                elif isinstance(r, dict):
                    self.fixed_blocks.append(
                        {
                            "id": self.nblocks,
                            "top": r["top"],
                            "left": r["left"],
                            "bottom": r["bottom"],
                            "right": r["right"],
                        }
                    )
                else:
                    raise TypeError("A pre-defined blocks must be a list, tuple, or dict.")

                self.nblocks += 1

        for r in rectangles:
            if isinstance(r, (list, tuple)):
                self.rectangles.append(
                    {
                        "id": self.n,
                        "width": r[0],
                        "height": r[1],
                        "rotatable": r[2] if len(r) >= 3 else False,
                    }
                )
            elif isinstance(r, dict):
                self.rectangles.append(
                    {
                        "id": self.n,
                        "width": r["width"],
                        "height": r["height"],
                        "rotatable": r["rotatable"] if "rotatable" in r else False,
                    }
                )
            else:
                raise TypeError("A rectangle must be a list, tuple, or dict.")

            self.n += 1

    def __repr__(self) -> str:
        s = "Problem({"
        s += "'n': " + str(self.n) + ", "
        s += "'rectangles': " + str(self.rectangles) + "})"

        return s

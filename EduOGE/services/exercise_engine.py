from __future__ import annotations

from typing import Callable, Dict, Any
from EduOGE.services.generators import generate_task

GeneratorFn = Callable[[int], Any]

GENERATORS: Dict[str, GeneratorFn] = {
    "auto": generate_task,
    "type16": generate_task,
    "type16_auto": generate_task,
}


class GeneratorError(Exception):
    pass


def get_generator(generator_key: str) -> GeneratorFn:
    gen = GENERATORS.get(generator_key)
    if not gen:
        raise GeneratorError(f"Unknown generator_key: {generator_key}")
    return gen


def build_task_payload(*, generator_key: str, seed: int) -> dict:
    gen = get_generator(generator_key)
    task = gen(seed)

    if not getattr(task, "tests", None):
        raise GeneratorError("Generator returned no tests")

    main_test = task.tests[0]

    statement = (getattr(task, "statement", "") or "").strip()
    example_inp = (main_test.inp or "").strip()
    example_out = (main_test.out or "").strip()

    tests = [{"inp": (t.inp or "").strip(), "out": (t.out or "").strip()} for t in task.tests]

    meta = {
        "generator_key": generator_key,
        "tests": tests,
        "statement": statement,
        "example_inp": example_inp,
        "example_out": example_out,
        "solution_py": (getattr(task, "solution_py", "") or "").strip(),
        "solution_js": (getattr(task, "solution_js", "") or "").strip(),
    }

    return {
        "statement": statement,
        "example_inp": example_inp,
        "example_out": example_out,
        "solution_py": meta["solution_py"],
        "solution_js": meta["solution_js"],
        "correct_answer": example_out,
        "meta": meta,
    }
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Protocol
import importlib
import random

GEN_VERSION = "gen_v2"

# Тут ты перечисляешь модули с семействами задач
GENERATOR_MODULES = [
    "EduOGE.services.generator_families.type16",
]


# -------------------------
# Data structures
# -------------------------

@dataclass
class TestCase:
    inp: str
    out: str


@dataclass
class GeneratedTask:
    statement: str
    tests: List[TestCase]
    solution_py: str
    solution_js: str

    # Новое: воспроизводимость и дебаг
    family_key: str
    params: Dict[str, Any]
    gen_version: str = GEN_VERSION


class TaskFamily(Protocol):
    key: str

    def sample_params(self, rng: random.Random) -> Dict[str, Any]: ...
    def make_statement(self, p: Dict[str, Any]) -> str: ...
    def make_solution_py(self, p: Dict[str, Any]) -> str: ...
    def make_solution_js(self, p: Dict[str, Any]) -> str: ...

    def gen_input(self, rng: random.Random, p: Dict[str, Any]) -> Any: ...
    def format_input(self, data: Any, p: Dict[str, Any]) -> str: ...
    def solve(self, data: Any, p: Dict[str, Any]) -> str: ...


# -------------------------
# Helpers
# -------------------------

def normalize(s: str) -> str:
    s = s or ""
    return "\n".join(line.rstrip() for line in s.strip().splitlines()).strip()


# -------------------------
# Module loader
# -------------------------

_FAMILIES_CACHE: List[TaskFamily] | None = None

def load_families() -> List[TaskFamily]:
    global _FAMILIES_CACHE
    if _FAMILIES_CACHE is not None:
        return _FAMILIES_CACHE

    families: List[TaskFamily] = []
    for mod_path in GENERATOR_MODULES:
        mod = importlib.import_module(mod_path)
        if not hasattr(mod, "get_families"):
            raise RuntimeError(f"Generator module '{mod_path}' must define get_families()")
        part = mod.get_families()
        if not isinstance(part, list) or not part:
            raise RuntimeError(f"Generator module '{mod_path}' returned empty families list")
        families.extend(part)

    # простая проверка уникальности ключей
    seen = set()
    for f in families:
        if f.key in seen:
            raise RuntimeError(f"Duplicate family key: {f.key}")
        seen.add(f.key)

    _FAMILIES_CACHE = families
    return families


# -------------------------
# Main generator
# -------------------------

def generate_task(seed: int) -> GeneratedTask:
    rng = random.Random(seed)

    families = load_families()
    family = rng.choice(families)
    params = family.sample_params(rng)

    tests: List[TestCase] = []
    # анти-угадайка: несколько тестов
    for _ in range(5):
        data = family.gen_input(rng, params)
        inp = normalize(family.format_input(data, params))
        out = normalize(family.solve(data, params))
        tests.append(TestCase(inp=inp, out=out))

    statement = normalize(family.make_statement(params))
    sol_py = normalize(family.make_solution_py(params))
    sol_js = normalize(family.make_solution_js(params))

    # валидация, чтобы “не из воздуха”
    if not statement:
        raise RuntimeError(f"Empty statement for family={family.key}")
    if not tests or not tests[0].inp:
        raise RuntimeError(f"Empty tests for family={family.key}")
    if any(t.out is None for t in tests):
        raise RuntimeError(f"Bad test output for family={family.key}")

    return GeneratedTask(
        statement=statement,
        tests=tests,
        solution_py=sol_py,
        solution_js=sol_js,
        family_key=family.key,
        params=params,
    )

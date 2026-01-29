from __future__ import annotations

from typing import List, Dict, Any
import random

from EduOGE.services.generators import TaskFamily, normalize


# -------------------------
# Helpers (локально для модуля)
# -------------------------

def pick_multiple(rng: random.Random, *, base: int, lo: int, hi: int) -> int:
    lo_k = (lo + base - 1) // base
    hi_k = hi // base
    if lo_k > hi_k:
        return (hi // base) * base if hi >= base else base
    return rng.randint(lo_k, hi_k) * base


def gen_n_list(rng: random.Random, *, n_max: int, value_max: int) -> List[int]:
    n = rng.randint(1, n_max)
    return [rng.randint(1, value_max) for _ in range(n)]


def gen_until_zero(rng: random.Random, *, count_max: int, value_max: int) -> List[int]:
    n = rng.randint(1, count_max)
    data = [rng.randint(1, value_max) for _ in range(n)]
    data.append(0)
    return data


def format_n_list(data: List[int]) -> str:
    return "\n".join([str(len(data))] + [str(x) for x in data])


def format_until_zero(data: List[int]) -> str:
    return "\n".join(str(x) for x in data)


def format_two_numbers(a: int, b: int) -> str:
    return f"{a}\n{b}"


def ensure_divisible_in_list(rng: random.Random, data: List[int], d: int) -> None:
    idx = rng.randrange(0, len(data))
    upper = max(max(data), d)
    k = rng.randint(1, upper // d)
    data[idx] = k * d


def pick_divisor_2_10(rng: random.Random) -> int:
    return rng.randint(2, 10)


def pick_digit_0_9(rng: random.Random) -> int:
    return rng.randint(0, 9)


def pick_count_limit_mult_5(rng: random.Random) -> int:
    return rng.choice([10, 15, 20, 25, 30])


def pick_value_limit_mult_500(rng: random.Random) -> int:
    return rng.choice([500, 1000, 1500, 2000, 2500])


def pick_base_2_10(rng: random.Random) -> int:
    return rng.randint(2, 10)


# -------------------------
# Families
# -------------------------

class SumDivisibleNList:
    key = "sum_divisible_n_list"

    def sample_params(self, rng):
        d = pick_divisor_2_10(rng)
        n_max = pick_count_limit_mult_5(rng)
        v_max = pick_value_limit_mult_500(rng)
        return {"d": d, "n_max": n_max, "v_max": v_max}

    def make_statement(self, p):
        return normalize(f"""
Напишите программу подсчёта суммы элементов последовательности натуральных чисел, кратных {p["d"]}.

На вход программе сначала подается количество элементов последовательности N (1 ≤ N ≤ {p["n_max"]}),
затем каждый элемент последовательности в отдельной строке. Введённые числа по модулю не превышают {p["v_max"]}.

Программа должна вывести одно число: сумму чисел, кратных {p["d"]}.
""")

    def gen_input(self, rng, p):
        return gen_n_list(rng, n_max=p["n_max"], value_max=p["v_max"])

    def format_input(self, data, p):
        return format_n_list(data)

    def solve(self, data, p):
        s = 0
        for x in data:
            if x % p["d"] == 0:
                s += x
        return str(s)

    def make_solution_py(self, p):
        return normalize(f"""
n = int(input())
s = 0
for _ in range(n):
    x = int(input())
    if x % {p["d"]} == 0:
        s += x
print(s)
""")

    def make_solution_js(self, p):
        return normalize(f"""
const fs = require('fs');
const raw = fs.readFileSync(0,'utf8').trim();
const a = raw ? raw.split(/\\s+/).map(Number) : [];
let i = 0;
const n = a[i++];
let s = 0;
for (let k = 0; k < n; k++) {{
  const x = a[i++];
  if (x % {p["d"]} === 0) s += x;
}}
process.stdout.write(String(s));
""")


class CountEndingDigitNList:
    key = "count_ending_digit_n_list"

    def sample_params(self, rng):
        digit = pick_digit_0_9(rng)
        n_max = pick_count_limit_mult_5(rng)
        v_max = pick_value_limit_mult_500(rng)
        return {"digit": digit, "n_max": n_max, "v_max": v_max}

    def make_statement(self, p):
        return normalize(f"""
Напишите программу подсчёта количества элементов последовательности натуральных чисел, оканчивающихся на цифру {p["digit"]}.

На вход программе сначала подается количество элементов последовательности N (1 ≤ N ≤ {p["n_max"]}),
затем каждый элемент последовательности в отдельной строке. Введённые числа по модулю не превышают {p["v_max"]}.

Программа должна вывести одно число: количество чисел, оканчивающихся на {p["digit"]}.
""")

    def gen_input(self, rng, p):
        return gen_n_list(rng, n_max=p["n_max"], value_max=p["v_max"])

    def format_input(self, data, p):
        return format_n_list(data)

    def solve(self, data, p):
        c = 0
        d = p["digit"]
        for x in data:
            if x % 10 == d:
                c += 1
        return str(c)

    def make_solution_py(self, p):
        return normalize(f"""
n = int(input())
c = 0
for _ in range(n):
    x = int(input())
    if x % 10 == {p["digit"]}:
        c += 1
print(c)
""")

    def make_solution_js(self, p):
        return normalize(f"""
const fs = require('fs');
const raw = fs.readFileSync(0,'utf8').trim();
const a = raw ? raw.split(/\\s+/).map(Number) : [];
let i = 0;
const n = a[i++];
let c = 0;
for (let k = 0; k < n; k++) {{
  const x = a[i++];
  if (x % 10 === {p["digit"]}) c++;
}}
process.stdout.write(String(c));
""")


class MinDivisibleGuaranteedNList:
    key = "min_divisible_guaranteed"

    def sample_params(self, rng):
        d = pick_divisor_2_10(rng)
        n_max = pick_count_limit_mult_5(rng)
        v_max = pick_value_limit_mult_500(rng)
        return {"d": d, "n_max": n_max, "v_max": v_max}

    def make_statement(self, p):
        return normalize(f"""
Напишите программу поиска минимального числа в последовательности натуральных чисел, кратного {p["d"]}.
Гарантируется, что в последовательности есть хотя бы одно число, кратное {p["d"]}.

На вход программе сначала подается количество элементов последовательности N (1 ≤ N ≤ {p["n_max"]}),
затем каждый элемент последовательности в отдельной строке. Введённые числа по модулю не превышают {p["v_max"]}.

Программа должна вывести одно число: минимальное число, кратное {p["d"]}.
""")

    def gen_input(self, rng, p):
        data = gen_n_list(rng, n_max=p["n_max"], value_max=p["v_max"])
        ensure_divisible_in_list(rng, data, p["d"])
        return data

    def format_input(self, data, p):
        return format_n_list(data)

    def solve(self, data, p):
        d = p["d"]
        m = None
        for x in data:
            if x % d == 0:
                if m is None or x < m:
                    m = x
        return str(m)

    def make_solution_py(self, p):
        return normalize(f"""
n = int(input())
m = None
for _ in range(n):
    x = int(input())
    if x % {p["d"]} == 0:
        if m is None or x < m:
            m = x
print(m)
""")

    def make_solution_js(self, p):
        return normalize(f"""
const fs = require('fs');
const raw = fs.readFileSync(0,'utf8').trim();
const a = raw ? raw.split(/\\s+/).map(Number) : [];
let i = 0;
const n = a[i++];
let m = null;
for (let k = 0; k < n; k++) {{
  const x = a[i++];
  if (x % {p["d"]} === 0) {{
    if (m === null || x < m) m = x;
  }}
}}
process.stdout.write(String(m));
""")


class SumAndCountDivisibleNList:
    key = "sum_and_count_divisible"

    def sample_params(self, rng):
        d = pick_divisor_2_10(rng)
        n_max = pick_count_limit_mult_5(rng)
        v_max = pick_value_limit_mult_500(rng)
        return {"d": d, "n_max": n_max, "v_max": v_max}

    def make_statement(self, p):
        return normalize(f"""
Напишите программу подсчёта суммы и количества элементов последовательности натуральных чисел, кратных {p["d"]}.
В ответе выведите два числа: сначала сумму, затем количество.

На вход программе сначала подается количество элементов последовательности N (1 ≤ N ≤ {p["n_max"]}),
затем каждый элемент последовательности в отдельной строке. Введённые числа по модулю не превышают {p["v_max"]}.

Программа должна вывести два числа: сумму и количество чисел, кратных {p["d"]}.
""")

    def gen_input(self, rng, p):
        return gen_n_list(rng, n_max=p["n_max"], value_max=p["v_max"])

    def format_input(self, data, p):
        return format_n_list(data)

    def solve(self, data, p):
        s = 0
        c = 0
        d = p["d"]
        for x in data:
            if x % d == 0:
                s += x
                c += 1
        return f"{s} {c}"

    def make_solution_py(self, p):
        return normalize(f"""
n = int(input())
s = 0
c = 0
for _ in range(n):
    x = int(input())
    if x % {p["d"]} == 0:
        s += x
        c += 1
print(s, c)
""")

    def make_solution_js(self, p):
        return normalize(f"""
const fs = require('fs');
const raw = fs.readFileSync(0,'utf8').trim();
const a = raw ? raw.split(/\\s+/).map(Number) : [];
let i = 0;
const n = a[i++];
let s = 0, c = 0;
for (let k = 0; k < n; k++) {{
  const x = a[i++];
  if (x % {p["d"]} === 0) {{ s += x; c++; }}
}}
process.stdout.write(`${{s}} ${{c}}`);
""")


class MaxAndYesNoDivisibleNList:
    key = "max_and_yesno_divisible"

    def sample_params(self, rng):
        d = pick_divisor_2_10(rng)
        n_max = pick_count_limit_mult_5(rng)
        v_max = pick_value_limit_mult_500(rng)
        return {"d": d, "n_max": n_max, "v_max": v_max}

    def make_statement(self, p):
        return normalize(f"""
Напишите программу, которая находит максимальный элемент последовательности натуральных чисел
и определяет, кратен ли он {p["d"]}. В ответе выведите два значения: максимальное число и слово YES или NO.

На вход программе сначала подается количество элементов последовательности N (1 ≤ N ≤ {p["n_max"]}),
затем каждый элемент последовательности в отдельной строке. Введённые числа по модулю не превышают {p["v_max"]}.

Программа должна вывести: максимальное число и YES (если оно кратно {p["d"]}) или NO (иначе).
""")

    def gen_input(self, rng, p):
        return gen_n_list(rng, n_max=p["n_max"], value_max=p["v_max"])

    def format_input(self, data, p):
        return format_n_list(data)

    def solve(self, data, p):
        m = max(data)
        return f"{m} {'YES' if (m % p['d'] == 0) else 'NO'}"

    def make_solution_py(self, p):
        return normalize(f"""
n = int(input())
m = None
for _ in range(n):
    x = int(input())
    if m is None or x > m:
        m = x
print(m, "YES" if m % {p["d"]} == 0 else "NO")
""")

    def make_solution_js(self, p):
        return normalize(f"""
const fs = require('fs');
const raw = fs.readFileSync(0,'utf8').trim();
const a = raw ? raw.split(/\\s+/).map(Number) : [];
let i = 0;
const n = a[i++];
let m = null;
for (let k = 0; k < n; k++) {{
  const x = a[i++];
  if (m === null || x > m) m = x;
}}
const ans = (m % {p["d"]} === 0) ? "YES" : "NO";
process.stdout.write(`${{m}} ${{ans}}`);
""")


class AvgDivisibleOrNoNList:
    key = "avg_divisible_or_no"

    def sample_params(self, rng):
        d = pick_divisor_2_10(rng)
        n_max = pick_count_limit_mult_5(rng)
        v_max = pick_value_limit_mult_500(rng)
        return {"d": d, "n_max": n_max, "v_max": v_max}

    def make_statement(self, p):
        return normalize(f"""
Напишите программу вычисления среднего арифметического элементов последовательности натуральных чисел,
кратных {p["d"]}. Если таких чисел нет, выведите NO.

На вход программе сначала подается количество элементов последовательности N (1 ≤ N ≤ {p["n_max"]}),
затем каждый элемент последовательности в отдельной строке. Введённые числа по модулю не превышают {p["v_max"]}.

Программа должна вывести либо NO, либо одно число — среднее арифметическое (с одним знаком после запятой).
""")

    def gen_input(self, rng, p):
        return gen_n_list(rng, n_max=p["n_max"], value_max=p["v_max"])

    def format_input(self, data, p):
        return format_n_list(data)

    def solve(self, data, p):
        s = 0
        c = 0
        d = p["d"]
        for x in data:
            if x % d == 0:
                s += x
                c += 1
        if c == 0:
            return "NO"
        return f"{(s / c):.1f}"

    def make_solution_py(self, p):
        return normalize(f"""
n = int(input())
s = 0
c = 0
for _ in range(n):
    x = int(input())
    if x % {p["d"]} == 0:
        s += x
        c += 1
if c == 0:
    print("NO")
else:
    print(f"{{s / c:.1f}}")
""")

    def make_solution_js(self, p):
        return normalize(f"""
const fs = require('fs');
const raw = fs.readFileSync(0,'utf8').trim();
const a = raw ? raw.split(/\\s+/).map(Number) : [];
let i = 0;
const n = a[i++];
let s = 0, c = 0;
for (let k = 0; k < n; k++) {{
  const x = a[i++];
  if (x % {p["d"]} === 0) {{ s += x; c++; }}
}}
if (c === 0) process.stdout.write("NO");
else process.stdout.write((s / c).toFixed(1));
""")


class UntilZeroAvg:
    key = "until_zero_avg"

    def sample_params(self, rng):
        count_max = pick_count_limit_mult_5(rng)
        v_max = pick_value_limit_mult_500(rng)
        return {"count_max": count_max, "v_max": v_max}

    def make_statement(self, p):
        return normalize(f"""
Напишите программу вычисления среднего арифметического введённых натуральных чисел.
Ввод заканчивается числом 0 (оно не входит в последовательность).

На вход программе подаются натуральные числа (каждое в отдельной строке), затем 0.
Количество введённых чисел не превышает {p["count_max"]}, введённые числа по модулю не превышают {p["v_max"]}.

Программа должна напечатать только одно число — среднее арифметическое (с одним знаком после запятой).
""")

    def gen_input(self, rng, p):
        return gen_until_zero(rng, count_max=p["count_max"], value_max=p["v_max"])

    def format_input(self, data, p):
        return format_until_zero(data)

    def solve(self, data, p):
        s = 0
        c = 0
        for x in data:
            if x == 0:
                break
            s += x
            c += 1
        return f"{(s / c):.1f}"

    def make_solution_py(self, p):
        return normalize("""
s = 0
c = 0
while True:
    x = int(input())
    if x == 0:
        break
    s += x
    c += 1
print(f"{s / c:.1f}")
""")

    def make_solution_js(self, p):
        return normalize("""
const fs = require('fs');
const raw = fs.readFileSync(0,'utf8').trim();
const a = raw ? raw.split(/\\s+/).map(Number) : [];
let s = 0, c = 0;
for (const x of a) {
  if (x === 0) break;
  s += x; c++;
}
process.stdout.write((s / c).toFixed(1));
""")


class RangeCountDivisible:
    key = "range_count_divisible"

    def sample_params(self, rng):
        d = pick_divisor_2_10(rng)
        v_max = pick_value_limit_mult_500(rng)
        delta_max = pick_count_limit_mult_5(rng)
        return {"d": d, "v_max": v_max, "delta_max": delta_max}

    def make_statement(self, p):
        return normalize(f"""
Даны два целых числа a и b (a ≤ b). Напишите программу подсчёта количества чисел, кратных {p["d"]}, на отрезке [a; b].
В ответе запишите только количество.

На вход программе подаются два целых числа a и b (каждое в отдельной строке).
Гарантируется, что 1 ≤ a ≤ b ≤ {p["v_max"]}, при этом b − a ≤ {p["delta_max"]}.

Программа должна вывести одно число: количество чисел, кратных {p["d"]}, на отрезке [a; b].
""")

    def gen_input(self, rng, p):
        a = rng.randint(1, p["v_max"])
        b = min(p["v_max"], a + rng.randint(0, p["delta_max"]))
        return (a, b)

    def format_input(self, data, p):
        a, b = data
        return format_two_numbers(a, b)

    def solve(self, data, p):
        a, b = data
        d = p["d"]
        c = 0
        for x in range(a, b + 1):
            if x % d == 0:
                c += 1
        return str(c)

    def make_solution_py(self, p):
        return normalize(f"""
a = int(input())
b = int(input())
c = 0
for x in range(a, b + 1):
    if x % {p["d"]} == 0:
        c += 1
print(c)
""")

    # ВОТ ТУТ БЫЛ БАГ: не f-string
    def make_solution_js(self, p):
        return normalize(f"""
const fs = require('fs');
const raw = fs.readFileSync(0,'utf8').trim();
const a = raw ? raw.split(/\\s+/).map(Number) : [];
const A = a[0], B = a[1];
let c = 0;
for (let x = A; x <= B; x++) {{
  if (x % {p["d"]} === 0) c++;
}}
process.stdout.write(String(c));
""")


class SumBaseLastDigitNList:
    key = "sum_base_last_digit_n_list"

    def sample_params(self, rng):
        base = pick_base_2_10(rng)
        last = rng.randint(0, base - 1)
        n_max = pick_count_limit_mult_5(rng)
        v_max = pick_value_limit_mult_500(rng)
        return {"base": base, "last": last, "n_max": n_max, "v_max": v_max}

    def make_statement(self, p):
        return normalize(f"""
Напишите программу подсчёта суммы элементов последовательности натуральных чисел, запись которых в {p["base"]}-ричной системе
счисления оканчивается на цифру {p["last"]}. В ответе запишите только сумму.

На вход программе сначала подается количество элементов последовательности N (1 ≤ N ≤ {p["n_max"]}),
затем каждый элемент последовательности в отдельной строке. Введённые числа по модулю не превышают {p["v_max"]}.

Программа должна вывести одно число — искомую сумму в десятичной системе.
""")

    def gen_input(self, rng, p):
        return gen_n_list(rng, n_max=p["n_max"], value_max=p["v_max"])

    def format_input(self, data, p):
        return format_n_list(data)

    def solve(self, data, p):
        s = 0
        for x in data:
            if x % p["base"] == p["last"]:
                s += x
        return str(s)

    def make_solution_py(self, p):
        return normalize(f"""
n = int(input())
s = 0
for _ in range(n):
    x = int(input())
    if x % {p["base"]} == {p["last"]}:
        s += x
print(s)
""")

    # ВОТ ТУТ ТОЖЕ БЫЛ БАГ: не f-string
    def make_solution_js(self, p):
        return normalize(f"""
const fs = require('fs');
const raw = fs.readFileSync(0,'utf8').trim();
const a = raw ? raw.split(/\\s+/).map(Number) : [];
let i = 0;
const n = a[i++];
let s = 0;
for (let k = 0; k < n; k++) {{
  const x = a[i++];
  if (x % {p["base"]} === {p["last"]}) s += x;
}}
process.stdout.write(String(s));
""")


class SumThreeDigitDivisibleUntilZero:
    key = "sum_three_digit_divisible_until_zero"

    def sample_params(self, rng):
        d = pick_divisor_2_10(rng)
        count_max = pick_count_limit_mult_5(rng)
        v_max = pick_value_limit_mult_500(rng)
        return {"d": d, "count_max": count_max, "v_max": v_max}

    def make_statement(self, p):
        return normalize(f"""
Напишите программу, которая в последовательности натуральных чисел вычисляет сумму трехзначных чисел, кратных {p["d"]}.
Программа получает на вход натуральные числа, количество введенных чисел неизвестно, последовательность чисел заканчивается числом 0
(0 — признак окончания ввода, не входит в последовательность).
Количество чисел не превышает {p["count_max"]}. Введенные числа не превышают {p["v_max"]}.
""")

    def gen_input(self, rng, p):
        return gen_until_zero(rng, count_max=p["count_max"], value_max=p["v_max"])

    def format_input(self, data, p):
        return format_until_zero(data)

    def solve(self, data, p):
        s = 0
        for x in data:
            if x == 0:
                break
            if 100 <= x <= 999 and x % p["d"] == 0:
                s += x
        return str(s)

    def make_solution_py(self, p):
        return normalize(f"""
s = 0
while True:
    x = int(input())
    if x == 0:
        break
    if 100 <= x <= 999 and x % {p["d"]} == 0:
        s += x
print(s)
""")

    def make_solution_js(self, p):
        return normalize(f"""
const fs = require('fs');
const raw = fs.readFileSync(0,'utf8').trim();
const a = raw ? raw.split(/\\s+/).map(Number) : [];
let s = 0;
for (const x of a) {{
  if (x === 0) break;
  if (x >= 100 && x <= 999 && x % {p["d"]} === 0) s += x;
}}
process.stdout.write(String(s));
""")


def get_families() -> List[TaskFamily]:
    return [
        SumDivisibleNList(),
        CountEndingDigitNList(),
        MinDivisibleGuaranteedNList(),
        SumAndCountDivisibleNList(),
        MaxAndYesNoDivisibleNList(),
        AvgDivisibleOrNoNList(),
        UntilZeroAvg(),
        RangeCountDivisible(),
        SumBaseLastDigitNList(),
        SumThreeDigitDivisibleUntilZero(),
    ]

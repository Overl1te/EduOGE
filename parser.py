from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List, Tuple

from bs4 import BeautifulSoup, Tag


@dataclass
class Problem:
    problem_id: int
    type_num: Optional[int]
    body_id: Optional[str]
    sol_id: Optional[str]
    statement_text: str
    sample_input: Optional[str]
    sample_output: Optional[str]
    python_solution: Optional[str]


TYPE_RE = re.compile(r"Тип\s+(\d+)")
PROBLEM_ID_RE = re.compile(r"problem_(\d+)")


def read_local_html(path: str) -> str:
    # В сохранённом .htm обычно UTF-8, но бывает зоопарк.
    # errors="replace" спасает от мусора.
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def clean_text(s: str) -> str:
    s = re.sub(r"\u00a0", " ", s)  # nbsp
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def extract_sample_from_table(table: Tag) -> Tuple[Optional[str], Optional[str]]:
    """
    На странице примеры часто лежат в table с 2 колонками: "Входные данные" / "Выходные данные".
    Берём первую строку данных (после заголовка).
    """
    rows = table.find_all("tr")
    if len(rows) < 2:
        return None, None

    cells = rows[1].find_all(["td", "th"])
    if len(cells) < 2:
        return None, None

    sample_in = clean_text(cells[0].get_text("\n", strip=True))
    sample_out = clean_text(cells[1].get_text("\n", strip=True))
    return sample_in or None, sample_out or None


def extract_python_solution(sol_div: Tag) -> Optional[str]:
    code_block = sol_div.select_one("div.source_code.lang_python")
    if not code_block:
        return None
    code = code_block.get_text("\n", strip=True)
    return clean_text(code) or None


def parse_problems(html: str) -> List[Problem]:
    soup = BeautifulSoup(html, "html.parser")

    problems: List[Problem] = []

    # В 1.htm каждая задача живёт в div.prob_maindiv (см. id="maindiv967774" data-id="967774")
    for container in soup.select("div.prob_maindiv[id^='maindiv'][data-id]"):
        internal_id = container.get("data-id")  # типа 967774 (внутренний)
        body_div = container.select_one(f"div.pbody#body{internal_id}")
        sol_div = container.select_one(f"div.solution#sol{internal_id}")

        # ID задачи берём из ссылки вида /problem?id=43682 внутри span.prob_nums
        problem_id = None
        type_num = None

        prob_nums = container.select_one("span.prob_nums")
        if prob_nums:
            tm = TYPE_RE.search(prob_nums.get_text(" ", strip=True))
            if tm:
                type_num = int(tm.group(1))

            a = prob_nums.select_one("a[href*='problem?id=']")
            if a and a.get("href"):
                m = re.search(r"problem\?id=(\d+)", a["href"])
                if m:
                    problem_id = int(m.group(1))

        # если почему-то ссылки нет, fallback: пропускаем
        if problem_id is None:
            continue

        statement_text = ""
        sample_input = None
        sample_output = None

        if body_div:
            statement_text = clean_text(body_div.get_text("\n", strip=True))
            table = body_div.find("table")
            if table:
                sample_input, sample_output = extract_sample_from_table(table)

        python_solution = extract_python_solution(sol_div) if sol_div else None

        problems.append(
            Problem(
                problem_id=problem_id,
                type_num=type_num,
                body_id=body_div.get("id") if body_div else None,
                sol_id=sol_div.get("id") if sol_div else None,
                statement_text=statement_text,
                sample_input=sample_input,
                sample_output=sample_output,
                python_solution=python_solution,
            )
        )

    return problems


def export_txt(problems: List[Problem], out_path: str) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        for i, p in enumerate(problems, start=1):
            f.write(f"Задача #{i}\n")
            f.write(f"ID: {p.problem_id}\n")
            f.write(f"Тип: {p.type_num}\n")
            f.write("=" * 60 + "\n")
            f.write(p.statement_text + "\n")

            if p.sample_input or p.sample_output:
                f.write("\nПример:\n")
                if p.sample_input:
                    f.write("Входные данные:\n")
                    f.write(p.sample_input + "\n")
                if p.sample_output:
                    f.write("Выходные данные:\n")
                    f.write(p.sample_output + "\n")

            if p.python_solution:
                f.write("\nРешение (Python):\n")
                f.write(p.python_solution + "\n")

            f.write("\n" + "#" * 60 + "\n\n")


def export_json(problems: List[Problem], out_path: str) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump([asdict(p) for p in problems], f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Путь к сохранённому HTML (.htm/.html) с задачами",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="output.txt",
        help="Куда сохранить результат (по умолчанию output.txt)",
    )
    parser.add_argument(
        "--format",
        choices=["txt", "json"],
        default="txt",
        help="Формат экспорта: txt или json",
    )
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        raise FileNotFoundError(f"Файл не найден: {in_path}")

    html = read_local_html(str(in_path))
    problems = parse_problems(html)

    if args.format == "txt":
        export_txt(problems, args.output)
    else:
        export_json(problems, args.output)

    print(f"Готово. Задач: {len(problems)}. Файл: {args.output}")


if __name__ == "__main__":
    main()

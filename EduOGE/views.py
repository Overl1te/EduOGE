from __future__ import annotations

import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import ExerciseType, TaskTemplate, Attempt
from EduOGE.services.exercise_engine import build_task_payload, GeneratorError
from EduOGE.services.code_runner import run_python, run_js, RunnerError


# -------------------------
# Pages
# -------------------------

def home(request):
    types = ExerciseType.objects.filter(is_active=True)
    return render(request, "eduoge/home.html", {"types": types})


def exercise_page(request):
    type_code = int(request.GET.get("type", 16))
    etype = ExerciseType.objects.get(code=type_code)
    return render(request, "eduoge/exercise.html", {"etype": etype})


# -------------------------
# API
# -------------------------

@csrf_exempt
def api_check_answer(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST only"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"ok": False, "error": "Bad JSON"}, status=400)

    # ожидаем: type, seed, language/lang, code
    try:
        type_code = int(payload.get("type", 16))
        seed = int(payload.get("seed"))
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "Bad type/seed"}, status=400)

    # фронт обычно шлёт `language`, но старые клиенты могли слать `lang`
    lang = (payload.get("language") or payload.get("lang") or "py").lower()
    code = (payload.get("code") or "").strip()
    if not code:
        return JsonResponse({"ok": False, "error": "Empty code"}, status=400)

    try:
        etype = ExerciseType.objects.get(code=type_code)
    except ExerciseType.DoesNotExist:
        return JsonResponse({"ok": False, "error": f"Unknown type: {type_code}"}, status=404)

    attempt = Attempt.objects.filter(exercise_type=etype, seed=str(seed)).first()
    if not attempt or not attempt.task_vars:
        return JsonResponse({"ok": False, "error": "Task not generated for this seed"}, status=404)

    tests = attempt.task_vars.get("tests") or []
    if not tests:
        return JsonResponse({"ok": False, "error": "No tests in task_vars"}, status=500)

    runner = run_python if lang in ("py", "python") else run_js if lang in ("js", "javascript") else None
    if runner is None:
        return JsonResponse({"ok": False, "error": f"Unsupported lang: {lang}"}, status=400)

    def norm_out(s: str) -> str:
        # НЕ режем stdout тотально: важны пробелы и переносы.
        # Сравниваем "как люди": rstrip по строкам + обрезка крайних пустых строк.
        s = s or ""
        return "\n".join(line.rstrip() for line in s.strip().splitlines()).strip()

    stdout_first = ""

    # прогоняем по всем тестам
    for idx, t in enumerate(tests, start=1):
        inp = (t.get("inp") or "").strip()
        expected = (t.get("out") or "").strip()

        try:
            got_raw = runner(code, inp)
        except RunnerError as e:
            return JsonResponse({
                "ok": True,
                "is_correct": False,
                "error_kind": e.kind,
                "error": e.message,
                "failed_test": idx,
                "passed": idx - 1,
            }, status=200)

        if idx == 1:
            stdout_first = got_raw

        got_norm = norm_out(got_raw)

        if got_norm != expected:
            return JsonResponse({
                "ok": True,
                "is_correct": False,
                "failed_test": idx,
                "passed": idx - 1,
                "expected": expected,
                "got": got_norm,
                "stdout": got_raw,
            }, status=200)

    return JsonResponse({
        "ok": True,
        "is_correct": True,
        "passed": len(tests),
        "stdout": stdout_first,
    })


@csrf_exempt
def api_generate_exercise(request):
    try:
        type_code = int(request.GET.get("type", 16))
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "Bad type"}, status=400)

    try:
        seed = int(request.GET.get("seed"))
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "Bad seed"}, status=400)

    try:
        etype = ExerciseType.objects.get(code=type_code)
    except ExerciseType.DoesNotExist:
        return JsonResponse({"ok": False, "error": f"Unknown type: {type_code}"}, status=404)

    # 1) Сначала пробуем вернуть уже сохранённую попытку (стабильно по seed)
    attempt = Attempt.objects.filter(exercise_type=etype, seed=str(seed)).first()
    if attempt and attempt.task_vars:
        tv = attempt.task_vars
        # минимальная проверка консистентности
        if tv.get("statement") and tv.get("example_inp") is not None and tv.get("example_out") is not None:
            return JsonResponse({
                "ok": True,
                "type": type_code,
                "seed": str(seed),
                "statement": tv.get("statement", ""),
                "example_inp": tv.get("example_inp", ""),
                "example_out": tv.get("example_out", ""),
                "solution_py": tv.get("solution_py", ""),
                "solution_js": tv.get("solution_js", ""),
            })

    # 2) Если attempt нет (или пустой) — выбираем шаблон и генерируем
    templates = list(TaskTemplate.objects.filter(exercise_type=etype, is_active=True))
    if not templates:
        template = TaskTemplate.objects.create(
            exercise_type=etype,
            title="Автоген (default)",
            text_template="Автоматически сгенерированная задача.",
            generator_key="auto",
            difficulty=1,
            tags="auto",
            is_active=True,
        )
        templates = [template]

    rng = __import__("random").Random(seed)
    template = templates[rng.randrange(0, len(templates))]

    try:
        payload = build_task_payload(generator_key=template.generator_key, seed=seed)
    except GeneratorError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Generator failed: {e}"}, status=500)

    meta = payload["meta"]
    meta["template_id"] = template.id  # полезно для дебага
    correct_answer = payload["correct_answer"]

    if attempt:
        attempt.template = template
        attempt.task_vars = meta
        attempt.correct_answer = correct_answer
        attempt.save(update_fields=["template", "task_vars", "correct_answer"])
    else:
        Attempt.objects.create(
            exercise_type=etype,
            template=template,
            seed=str(seed),
            task_vars=meta,
            correct_answer=correct_answer,
        )

    return JsonResponse({
        "ok": True,
        "type": type_code,
        "seed": str(seed),
        "statement": payload["statement"],
        "example_inp": payload["example_inp"],
        "example_out": payload["example_out"],
        "solution_py": payload.get("solution_py", ""),
        "solution_js": payload.get("solution_js", ""),
    })

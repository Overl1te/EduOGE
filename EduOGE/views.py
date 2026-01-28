from __future__ import annotations

import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from EduOGE.services.code_runner import RunnerError

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

    attempt = Attempt.objects.filter(exercise_type=etype, seed=str(seed)).first()

    # Если attempt уже есть и там сохранены данные задачи (включая solution_*)
    if attempt and attempt.task_vars:
        tv = attempt.task_vars
        if tv.get("statement") and tv.get("example_inp") is not None:
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

    try:
        payload = build_task_payload(generator_key=template.generator_key, seed=seed)
    except GeneratorError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Generator failed: {e}"}, status=500)

    meta = payload["meta"]
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


@csrf_exempt
def api_check_answer(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
        type_code = int(payload.get("type", 16))
        seed = str(int(payload.get("seed")))
        language = str(payload.get("language", "python"))
        code = str(payload.get("code", ""))

        # Берём попытку, чтобы тесты совпадали с тем, что показано пользователю
        try:
            etype_obj = ExerciseType.objects.get(code=type_code)
        except ExerciseType.DoesNotExist:
            return JsonResponse({"ok": False, "error": f"Unknown type: {type_code}"}, status=404)

        attempt = Attempt.objects.filter(exercise_type=etype_obj, seed=seed).first()
        if not attempt or not attempt.task_vars or not attempt.task_vars.get("tests"):
            return JsonResponse({
                "ok": False,
                "error": "Tests not found for this seed. Open the task first (/api/exercise)."
            }, status=400)

        tests = attempt.task_vars["tests"]

        stdout_example = ""  # вывод на примере (tests[0])

        for idx, t in enumerate(tests):
            inp = t["inp"]
            expected = (t["out"] or "").strip()

            try:
                if language == "js":
                    stdout = run_js(code, inp)
                else:
                    stdout = run_python(code, inp)
            except RunnerError as e:
                return JsonResponse({
                    "ok": True,
                    "is_correct": False,
                    "stdout": "",
                    "error_kind": e.kind,
                })

            if idx == 0:
                stdout_example = stdout  # сохраняем вывод на “примере”

            actual = (stdout or "").strip()
            if actual != expected:
                return JsonResponse({
                    "ok": True,
                    "is_correct": False,
                    "stdout": stdout,      # вывод на том тесте, где упали
                })

        # если всё ок, показываем stdout именно на “примере”, а не на последнем скрытом тесте
        return JsonResponse({
            "ok": True,
            "is_correct": True,
            "stdout": stdout_example,
        })

    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)





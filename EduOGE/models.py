from __future__ import annotations

from django.conf import settings
from django.db import models


class ExerciseType(models.Model):
    """Тип задания ОГЭ (например, 16)."""

    code = models.PositiveSmallIntegerField(unique=True)  # 16, 17, ...
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=100)

    class Meta:
        ordering = ["sort_order", "code"]

    def __str__(self) -> str:
        return f"{self.code}. {self.title}"


class TaskTemplate(models.Model):
    """Шаблон задачи + ссылка на генератор."""

    exercise_type = models.ForeignKey(ExerciseType, on_delete=models.CASCADE, related_name="templates")
    title = models.CharField(max_length=140, blank=True, default="")
    text_template = models.TextField(
        help_text="Используй {var} плейсхолдеры. Например: 'Найди {a}+{b}'."
    )
    generator_key = models.CharField(
        max_length=80,
        help_text="Ключ генератора из services/generators.py (например, 'type16_sum').",
    )
    difficulty = models.PositiveSmallIntegerField(default=1)  # 1..3 условно
    tags = models.CharField(max_length=200, blank=True, default="")  # 'арифметика;время;...'
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["exercise_type__code", "difficulty", "id"]

    def __str__(self) -> str:
        base = self.title or self.generator_key
        return f"[{self.exercise_type.code}] {base}"


class Attempt(models.Model):
    """Попытка решения."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    exercise_type = models.ForeignKey(ExerciseType, on_delete=models.CASCADE)
    template = models.ForeignKey(TaskTemplate, null=True, blank=True, on_delete=models.SET_NULL)

    seed = models.CharField(max_length=64)
    task_vars = models.JSONField(default=dict)
    correct_answer = models.CharField(max_length=200)

    user_answer = models.CharField(max_length=200, blank=True, default="")
    is_correct = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Attempt type={self.exercise_type.code} correct={self.is_correct} at={self.created_at:%Y-%m-%d %H:%M}"

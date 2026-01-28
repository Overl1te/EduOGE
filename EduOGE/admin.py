from django.contrib import admin
from .models import ExerciseType, TaskTemplate, Attempt


@admin.register(ExerciseType)
class ExerciseTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("title",)


@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "exercise_type", "generator_key", "difficulty", "is_active")
    list_filter = ("exercise_type", "difficulty", "is_active")
    search_fields = ("title", "text_template", "generator_key", "tags")


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "exercise_type", "user", "is_correct", "created_at")
    list_filter = ("exercise_type", "is_correct", "created_at")
    search_fields = ("user_answer", "correct_answer", "seed")

from django.contrib import admin
from .models import Exam, CorrectAnswerSheet, StudentAnswerSheet


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['subject_name', 'num_questions', 'num_options', 'created_at']
    search_fields = ['subject_name']
    list_filter = ['created_at']
    ordering = ['-created_at']

    verbose_name = "Prova"
    verbose_name_plural = "Provas"

    def get_model_perms(self, request):
        """
        Garante que o nome em português apareça na interface do Django Admin.
        """
        perms = super().get_model_perms(request)
        perms['name'] = self.verbose_name
        return perms


@admin.register(CorrectAnswerSheet)
class CorrectAnswerSheetAdmin(admin.ModelAdmin):
    list_display = ['exam', 'created_at']
    search_fields = ['exam__subject_name']
    list_filter = ['created_at']
    ordering = ['-created_at']

    verbose_name = "Gabarito Correto"
    verbose_name_plural = "Gabaritos Corretos"


@admin.register(StudentAnswerSheet)
class StudentAnswerSheetAdmin(admin.ModelAdmin):
    list_display = [
        'sheet_code', 'exam', 'student_name',
        'correct_items', 'incorrect_items', 'accuracy_percentage', 'submitted_at'
    ]
    search_fields = ['sheet_code', 'student_name', 'exam__subject_name']
    list_filter = ['submitted_at', 'exam']
    readonly_fields = ['sheet_code', 'correct_items', 'incorrect_items', 'accuracy_percentage']
    ordering = ['-submitted_at']

    verbose_name = "Gabarito do Aluno"
    verbose_name_plural = "Gabaritos dos Alunos"

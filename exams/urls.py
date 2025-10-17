from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExamViewSet, CorrectAnswerSheetViewSet, StudentAnswerSheetViewSet

router = DefaultRouter()
router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'correct-answer-sheets', CorrectAnswerSheetViewSet, basename='correct-answer-sheet')
router.register(r'student-answer-sheets', StudentAnswerSheetViewSet, basename='student-answer-sheet')

urlpatterns = [
    path('', include(router.urls)),
]

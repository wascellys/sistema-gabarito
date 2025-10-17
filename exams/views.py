import base64
import io

import requests
from PIL import Image as PilImage
from openai import OpenAI
from pdf2image import convert_from_bytes
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from config import settings
from .models import Exam, CorrectAnswerSheet, StudentAnswerSheet
from .serializers import (
    ExamSerializer,
    CorrectAnswerSheetSerializer,
    StudentAnswerSheetSerializer,
    StudentAnswerSheetUploadSerializer
)

import json

client = OpenAI(api_key=settings.OPENAI_API_KEY)


class ExamViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing exams.
    """
    queryset = Exam.objects.all()
    serializer_class = ExamSerializer

    @action(detail=True, methods=['post'])
    def generate_answer_sheets_pdf(self, request, pk=None):
        """
        Endpoint to generate PDF with blank answer sheets for students.
        """
        from .utils.pdf_generator import generate_answer_sheet_pdf

        exam = self.get_object()
        quantity = int(request.data.get('quantity', 1))

        # Generate the PDF
        pdf_buffer, generated_codes = generate_answer_sheet_pdf(exam, quantity)

        # Return the PDF as response
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="answer_sheets_{exam.subject_name}.pdf"'
        return response


class CorrectAnswerSheetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing correct answer sheets.
    """
    queryset = CorrectAnswerSheet.objects.all()
    serializer_class = CorrectAnswerSheetSerializer


class StudentAnswerSheetViewSet(viewsets.ModelViewSet):
    queryset = StudentAnswerSheet.objects.all()
    serializer_class = StudentAnswerSheetSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['exam']
    search_fields = ['sheet_code']

    @action(detail=False, methods=['post'])
    def upload_answer_sheet(self, request):
        """
        Processa um arquivo de imagem enviado diretamente,
        sem usar serializer, e envia para a IA interpretar.
        """
        file = request.FILES.get('sheet_image')
        exam_id = request.data.get('exam')

        if not file:
            return Response({"error": "Nenhuma imagem enviada."}, status=status.HTTP_400_BAD_REQUEST)
        if not exam_id:
            return Response({"error": "O campo 'exam' é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            file_bytes = file.read()

            # Detecta tipo (PDF ou imagem)
            content_type = getattr(file, 'content_type', '').lower()

            if "pdf" in content_type or file.name.lower().endswith(".pdf"):
                # Converte primeira página do PDF em imagem
                images = convert_from_bytes(file_bytes)
                if not images:
                    raise ValueError("PDF sem páginas.")
                image = images[0].convert("RGB")
            else:
                # Abre imagem comum (jpg, png, etc.)
                image = PilImage.open(io.BytesIO(file_bytes)).convert("RGB")

            # Converte para base64
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            buffer.seek(0)
            image_b64 = base64.b64encode(buffer.read()).decode("utf-8")

            # Envia para o modelo GPT-4o
            response = client.chat.completions.create(
                model="gpt-4o",
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Você é um sistema especialista em leitura automática de gabaritos de provas. "
                            "Analise a imagem e retorne as respostas no formato JSON puro."
                        )
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Analise a imagem de um gabarito de prova e identifique "
                                    "quais alternativas (A, B, C, D, E) estão marcadas. "
                                    "Se alguma estiver em branco, use ''. "
                                    "Retorne exatamente neste formato:\n\n"
                                    "{ \"sheet_code\": \"CÓDIGO\", \"answers\": { \"1\": \"A\", \"2\": \"B\", ... } }"
                                )
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                            }
                        ]
                    },
                ],
                temperature=0,
            )

            result_text = response.choices[0].message.content
            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                return Response({
                    "error": "Falha ao interpretar a resposta da IA.",
                    "raw_response": result_text
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Salva o resultado no banco
            answer_sheet = StudentAnswerSheet.objects.filter(sheet_code=result.get("sheet_code")).first()
            if not answer_sheet:
                return Response(
                    {"error": "Código do gabarito não reconhecido.", "sheet_code": result.get("sheet_code")},
                    status=status.HTTP_400_BAD_REQUEST)

            answer_sheet.sheet_code = result.get("sheet_code")
            answer_sheet.student_answers = result.get("answers", {})
            answer_sheet.sheet_image = request.data.get('sheet_image')
            answer_sheet.save()

            # Calcula o resultado do exame
            answer_sheet.calculate_result()

            return Response({
                "message": "Gabarito processado com sucesso pela IA.",
                "sheet_code": answer_sheet.sheet_code,
                "detected_answers": answer_sheet.student_answers,
                "correct_items": answer_sheet.correct_items,
                "incorrect_items": answer_sheet.incorrect_items,
                "accuracy_percentage": float(answer_sheet.accuracy_percentage),
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "error": f"Erro ao processar imagem com IA: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def export_results(self, request):
        """
        Endpoint to export results to Excel.
        """
        from .utils.excel_exporter import export_detailed_results_to_excel, export_results_to_excel

        exam_id = request.query_params.get('exam_id')
        detailed = request.query_params.get('detailed', 'true').lower() == 'true'

        if not exam_id:
            return Response(
                {'error': 'The exam_id parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return Response(
                {'error': 'Exam not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate the Excel file
        if detailed:
            excel_buffer = export_detailed_results_to_excel(exam)
        else:
            excel_buffer = export_results_to_excel(exam)

        # Return the Excel as response
        response = HttpResponse(
            excel_buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="results_{exam.subject_name}.xlsx"'
        return response

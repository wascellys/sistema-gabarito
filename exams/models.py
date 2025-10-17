from django.db import models
import uuid


class Exam(models.Model):
    """
    Representa uma prova cadastrada no sistema.
    """
    subject_name = models.CharField(max_length=255, verbose_name="Nome do Assunto")
    num_questions = models.IntegerField(verbose_name="Número de Questões")
    num_options = models.IntegerField(verbose_name="Número de Opções por Questão")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Prova"
        verbose_name_plural = "Provas"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject_name} ({self.num_questions} questões)"


class CorrectAnswerSheet(models.Model):
    """
    Armazena as respostas corretas de uma prova específica.
    """
    exam = models.OneToOneField(
        Exam,
        on_delete=models.CASCADE,
        related_name='correct_answer_sheet',
        verbose_name="Prova"
    )
    answers = models.JSONField(verbose_name="Respostas Corretas")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Gabarito Correto"
        verbose_name_plural = "Gabaritos Corretos"

    def __str__(self):
        return f"Gabarito correto da prova {self.exam.subject_name}"


class StudentAnswerSheet(models.Model):
    """
    Representa o gabarito preenchido por um aluno, com um código único e respostas detectadas.
    """
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='student_answer_sheets',
        verbose_name="Prova"
    )
    sheet_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name="Código do Gabarito"
    )
    student_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Nome do Aluno"
    )
    student_answers = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Respostas do Aluno"
    )
    correct_items = models.IntegerField(default=0, verbose_name="Itens Corretos")
    incorrect_items = models.IntegerField(default=0, verbose_name="Itens Incorretos")
    accuracy_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="Percentual de Acertos"
    )
    sheet_image = models.ImageField(
        upload_to='student_answer_sheets/',
        blank=True,
        null=True,
        verbose_name="Imagem do Gabarito"
    )
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="Enviado em")

    class Meta:
        verbose_name = "Gabarito do Aluno"
        verbose_name_plural = "Gabaritos dos Alunos"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Gabarito {self.sheet_code} - {self.student_name or 'Desconhecido'}"

    def save(self, *args, **kwargs):
        if not self.sheet_code:
            self.sheet_code = uuid.uuid4().hex[:5].upper()
        super().save(*args, **kwargs)

    def calculate_result(self):
        """
        Calcula o resultado comparando as respostas do aluno com o gabarito correto.
        """
        if not self.student_answers:
            return

        try:
            correct_answers = self.exam.correct_answer_sheet.answers
            correct_count = 0
            incorrect_count = 0

            for question_num, student_answer in self.student_answers.items():
                correct_answer = correct_answers.get(question_num)
                if student_answer == correct_answer:
                    correct_count += 1
                else:
                    incorrect_count += 1

            self.correct_items = correct_count
            self.incorrect_items = incorrect_count

            total_questions = self.exam.num_questions
            if total_questions > 0:
                self.accuracy_percentage = (correct_count / total_questions) * 100
            else:
                self.accuracy_percentage = 0

            self.save()

        except CorrectAnswerSheet.DoesNotExist:
            pass

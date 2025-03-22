

from django.db import models
from django.contrib.auth.models import User

class Job(models.Model):
    title = models.CharField(max_length=100)
    client_email = models.EmailField(unique=True)
    client_password = models.CharField(max_length=100)
    over_all_income = models.PositiveIntegerField(default=0)  # Total income for the job
    created_at = models.DateTimeField(auto_now_add=True)  # Add this field
    def __str__(self):
        return self.title

    def get_overall_progress(self):
        total_percentage = 0
        total_weight = 0

        # Используйте related_name для получения всех задач, связанных с объектом
        tasks = self.tasks.all()  # если related_name не задан, используйте _set

        for task in tasks:
            total_percentage += task.progress * (task.task_percentage / 100)
            total_weight += task.task_percentage

        if total_weight > 0:
            overall_progress = (total_percentage / total_weight) * 100
        else:
            overall_progress = 0

        return round(overall_progress)

# Добавьте в модель Task в models.py

class Task(models.Model):
    TASK_TYPE_CHOICES = [
        ('SIMPLE', 'Простая задача'),
        ('PATPIS', 'Повторяющаяся задача')
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=100)
    hours = models.PositiveIntegerField(default=1)
    description = models.TextField()
    assigned_users = models.ManyToManyField(User, related_name='developer_tasks')
    task_percentage = models.PositiveIntegerField()
    progress = models.PositiveIntegerField(default=0)
    start_date = models.DateField(auto_now_add=True, null=True)
    deadline = models.DateField(null=True, blank=True)
    feedback = models.TextField(blank=True, null=True)
    money_for_task = models.PositiveIntegerField(default=0)
    paid = models.BooleanField(default=False)
    task_type = models.CharField(
        max_length=7,
        choices=TASK_TYPE_CHOICES,
        default='SIMPLE'
    )
    # Новые поля для подтверждения задач
    confirmed = models.BooleanField(default=False)
    confirmation_date = models.DateTimeField(null=True, blank=True)
    confirmed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_tasks'
    )

    def __str__(self):
        return self.title

    def check_and_pay_developer(self):
        # Оплата производится только после подтверждения администратором
        if self.progress == 100 and self.confirmed and not self.paid:
            self.paid = True
            self.save()

from django.db import models
from django.contrib.auth.models import User

class DeductionLog(models.Model):
    developer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deductions')
    deducted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deduction_actions')  # Admin who deducted
    deduction_amount = models.PositiveIntegerField()
    deduction_date = models.DateTimeField(auto_now_add=True)  # Automatically logs the date and time of deduction

    def __str__(self):
        return f"{self.deducted_by.username} deducted {self.deduction_amount} USD from {self.developer.username} on {self.deduction_date}"

from django.db.models import Sum

def calculate_income_balance():
    # Sum all money_for_task from Task model
    total_task_money = Task.objects.aggregate(Sum('money_for_task'))['money_for_task__sum'] or 0

    # Sum all over_all_income from Job model
    total_job_income = Job.objects.aggregate(Sum('over_all_income'))['over_all_income__sum'] or 0

    # Calculate the remaining balance
    income_balance = total_job_income - total_task_money

    return {
        "total_task_money": total_task_money,
        "total_job_income": total_job_income,
        "income_balance": income_balance,
    }


# Add this to your models.py file

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
import calendar


# Add this method to your Task model
def create_monthly_recurring_tasks(self):
    """Create recurring monthly tasks for a year if task type is PATPIS (Follow Task)"""
    if self.task_type == 'PATPIS':
        # Get today's date
        today = timezone.now().date()
        # Get the base task name (without month name)
        base_title = self.title

        # Create tasks for the next 12 months (including current month)
        for i in range(12):
            # Calculate target month's date
            target_date = today.replace(day=1) + timedelta(days=32 * i)
            target_date = target_date.replace(
                day=min(today.day, calendar.monthrange(target_date.year, target_date.month)[1]))

            # Get month name
            month_name = target_date.strftime('%B')

            # Skip creating duplicate for current month as the current task serves for it
            if i == 0:
                # Update current task's title to include current month
                self.title = f"{base_title} ({month_name})"
                self.save()
                continue

            # Create a new task for each future month
            new_task = Task(
                job=self.job,
                title=f"{base_title} ({month_name})",
                hours=self.hours,
                description=self.description,
                task_percentage=self.task_percentage,
                money_for_task=self.money_for_task,
                task_type='PATPIS',
                deadline=target_date  # Set deadline to the same day in the target month
            )
            new_task.save()

            # Copy assigned users
            for user in self.assigned_users.all():
                new_task.assigned_users.add(user)



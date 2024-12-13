
#verison 2

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


class Task(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=100)
    hours = models.PositiveIntegerField(default=1)  # Default to 1 if not set
    description = models.TextField()
    assigned_users = models.ManyToManyField(User, related_name='developer_tasks')
    task_percentage = models.PositiveIntegerField()  # Percentage this task represents in the project
    progress = models.PositiveIntegerField(default=0)  # Developer's current progress (0-100%)
    start_date = models.DateField(auto_now_add=True, null=True)  # Start date for the task
    deadline = models.DateField(null=True, blank=True)  # Deadline for the task
    feedback = models.TextField(blank=True, null=True)  # Feedback from developer
    money_for_task = models.PositiveIntegerField(default=0)  # Payment for the task
    paid = models.BooleanField(default=False)  # To track if the developer has been paid

    def __str__(self):
        return self.title

    def check_and_pay_developer(self):
        # If progress is 100% and the developer hasn't been paid, mark the task as paid
        if self.progress == 100 and not self.paid:
            self.paid = True
            self.save()
            # Logic to handle payment to developers can go here, e.g., sending a notification
            # Example: pay_to_developer(self.assigned_users, self.money_for_task)


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

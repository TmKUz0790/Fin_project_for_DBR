# serializers.py - CREATE THIS AS A NEW FILE
# This file doesn't exist in your project, so it's 100% safe to add

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Job, Task, DeductionLog


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class TaskSerializer(serializers.ModelSerializer):
    assigned_users = UserSerializer(many=True, read_only=True)
    assigned_user_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    job_title = serializers.CharField(source='job.title', read_only=True)
    days_until_deadline = serializers.SerializerMethodField()
    status_color = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'hours', 'progress',
            'task_percentage', 'money_for_task', 'paid', 'task_type',
            'start_date', 'deadline', 'feedback', 'confirmed',
            'confirmation_date', 'confirmed_by', 'assigned_users',
            'assigned_user_ids', 'job', 'job_title', 'days_until_deadline',
            'status_color'
        ]
        read_only_fields = ['start_date', 'confirmation_date', 'confirmed_by']

    def get_days_until_deadline(self, obj):
        if obj.deadline:
            from django.utils import timezone
            today = timezone.now().date()
            return (obj.deadline - today).days
        return None

    def get_status_color(self, obj):
        if obj.deadline:
            from django.utils import timezone
            today = timezone.now().date()
            days_until = (obj.deadline - today).days

            if obj.progress == 100:
                return 'completed'
            elif days_until < 0:
                return 'overdue'
            elif days_until == 0:
                return 'due_today'
            elif days_until <= 5:
                return 'task_red'
            elif days_until <= 10:
                return 'task_yellow'
            else:
                return 'task_green'
        return 'no_deadline'

    def create(self, validated_data):
        assigned_user_ids = validated_data.pop('assigned_user_ids', [])
        task = Task.objects.create(**validated_data)

        if assigned_user_ids:
            users = User.objects.filter(id__in=assigned_user_ids)
            task.assigned_users.set(users)

        return task

    def update(self, instance, validated_data):
        assigned_user_ids = validated_data.pop('assigned_user_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if assigned_user_ids is not None:
            users = User.objects.filter(id__in=assigned_user_ids)
            instance.assigned_users.set(users)

        return instance


class JobSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    overall_progress = serializers.SerializerMethodField()
    total_tasks = serializers.SerializerMethodField()
    completed_tasks = serializers.SerializerMethodField()
    overdue_tasks = serializers.SerializerMethodField()
    remaining_income = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'client_email', 'over_all_income',
            'created_at', 'tasks', 'overall_progress', 'total_tasks',
            'completed_tasks', 'overdue_tasks', 'remaining_income'
        ]
        read_only_fields = ['created_at']

    def get_overall_progress(self, obj):
        return obj.get_overall_progress()

    def get_total_tasks(self, obj):
        return obj.tasks.count()

    def get_completed_tasks(self, obj):
        return obj.tasks.filter(progress=100).count()

    def get_overdue_tasks(self, obj):
        from django.utils import timezone
        today = timezone.now().date()
        return obj.tasks.filter(deadline__lt=today, progress__lt=100).count()

    def get_remaining_income(self, obj):
        from django.db.models import Sum
        total_task_payment = obj.tasks.aggregate(Sum('money_for_task'))['money_for_task__sum'] or 0
        return obj.over_all_income - total_task_payment


class DeductionLogSerializer(serializers.ModelSerializer):
    developer_name = serializers.CharField(source='developer.username', read_only=True)
    deducted_by_name = serializers.CharField(source='deducted_by.username', read_only=True)

    class Meta:
        model = DeductionLog
        fields = [
            'id', 'developer', 'developer_name', 'deducted_by',
            'deducted_by_name', 'deduction_amount', 'deduction_date'
        ]
        read_only_fields = ['deduction_date']


class DashboardStatsSerializer(serializers.Serializer):
    total_projects = serializers.IntegerField()
    in_progress_projects = serializers.IntegerField()
    completed_projects = serializers.IntegerField()
    overdue_projects = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_customers = serializers.IntegerField()
    total_transactions = serializers.IntegerField()
    total_products = serializers.IntegerField()
    monthly_income = serializers.DecimalField(max_digits=10, decimal_places=2)
    income_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
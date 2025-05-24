# api_views.py - CREATE THIS AS A NEW FILE
# This file doesn't exist in your project, so it's 100% safe to add

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from .models import Job, Task, DeductionLog, calculate_income_balance
from .serializers import (
    JobSerializer, TaskSerializer, UserSerializer,
    DeductionLogSerializer, DashboardStatsSerializer
)


class IsAdminUser(permissions.BasePermission):
    """Custom permission to only allow admin users."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.email == 'Admin@dbr.org'


# Job API Views
class JobListCreateView(generics.ListCreateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Job.objects.all()
        # Filter by status if provided
        status_filter = self.request.query_params.get('status', None)
        if status_filter == 'completed':
            # Jobs with all tasks completed
            queryset = queryset.filter(tasks__progress=100).distinct()
        elif status_filter == 'in_progress':
            # Jobs with at least one task in progress
            queryset = queryset.filter(tasks__progress__gt=0, tasks__progress__lt=100).distinct()
        elif status_filter == 'overdue':
            # Jobs with overdue tasks
            today = timezone.now().date()
            queryset = queryset.filter(tasks__deadline__lt=today, tasks__progress__lt=100).distinct()

        return queryset.order_by('-created_at')


class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        # Only admin can delete jobs
        if request.user.email != 'Admin@dbr.org':
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


# Task API Views
class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Task.objects.select_related('job').prefetch_related('assigned_users')

        # Filter by job if provided
        job_id = self.request.query_params.get('job', None)
        if job_id:
            queryset = queryset.filter(job_id=job_id)

        # Filter by assigned user
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(assigned_users__id=user_id)

        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter == 'completed':
            queryset = queryset.filter(progress=100)
        elif status_filter == 'in_progress':
            queryset = queryset.filter(progress__gt=0, progress__lt=100)
        elif status_filter == 'pending':
            queryset = queryset.filter(progress=0)
        elif status_filter == 'overdue':
            today = timezone.now().date()
            queryset = queryset.filter(deadline__lt=today, progress__lt=100)

        # Filter by date range
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        if date_from:
            queryset = queryset.filter(deadline__gte=date_from)
        if date_to:
            queryset = queryset.filter(deadline__lte=date_to)

        return queryset.order_by('deadline')


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        # Check if user can update this task
        task = self.get_object()
        if (request.user not in task.assigned_users.all() and
                request.user.email != 'Admin@dbr.org'):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)


# Developer Task Views
class DeveloperTasksView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(
            assigned_users=self.request.user
        ).select_related('job').order_by('deadline')


# Dashboard API Views
@api_view(['GET'])
@permission_classes([IsAdminUser])
def dashboard_stats(request):
    """Get dashboard statistics"""
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    # Basic project stats
    total_projects = Job.objects.count()

    # Project status counts
    in_progress_projects = Job.objects.filter(
        tasks__progress__gt=0, tasks__progress__lt=100
    ).distinct().count()

    completed_projects = Job.objects.filter(
        tasks__progress=100
    ).distinct().count()

    overdue_projects = Job.objects.filter(
        tasks__deadline__lt=today, tasks__progress__lt=100
    ).distinct().count()

    # Financial data
    total_revenue = Job.objects.aggregate(
        total=Sum('over_all_income')
    )['total'] or 0

    monthly_income = Job.objects.filter(
        created_at__year=current_year,
        created_at__month=current_month
    ).aggregate(total=Sum('over_all_income'))['total'] or 0

    # Get income balance
    balance_data = calculate_income_balance()
    income_balance = balance_data['income_balance']

    # Task and user counts
    total_customers = User.objects.count()
    total_transactions = Task.objects.filter(paid=True).count()
    total_products = Task.objects.count()

    stats = {
        'total_projects': total_projects,
        'in_progress_projects': in_progress_projects,
        'completed_projects': completed_projects,
        'overdue_projects': overdue_projects,
        'total_revenue': total_revenue,
        'total_customers': total_customers,
        'total_transactions': total_transactions,
        'total_products': total_products,
        'monthly_income': monthly_income,
        'income_balance': income_balance,
    }

    serializer = DashboardStatsSerializer(stats)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def monthly_revenue_chart(request):
    """Get monthly revenue data for charts"""
    from datetime import datetime
    import calendar

    # Get current year or specified year
    year = int(request.query_params.get('year', timezone.now().year))

    monthly_data = []
    for month in range(1, 13):
        # Get jobs created in this month
        jobs_income = Job.objects.filter(
            created_at__year=year,
            created_at__month=month
        ).aggregate(Sum('over_all_income'))['over_all_income__sum'] or 0

        # Get expenses (money paid to developers)
        expenses = Task.objects.filter(
            job__created_at__year=year,
            job__created_at__month=month,
            paid=True
        ).aggregate(Sum('money_for_task'))['money_for_task__sum'] or 0

        profit = jobs_income - expenses

        monthly_data.append({
            'month': calendar.month_abbr[month],
            'income': jobs_income,
            'expenses': expenses,
            'profit': profit
        })

    return Response(monthly_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def project_status_distribution(request):
    """Get project status distribution for pie chart"""
    today = timezone.now().date()

    # Count projects by status
    in_progress = Job.objects.filter(
        tasks__progress__gt=0, tasks__progress__lt=100
    ).distinct().count()

    completed = Job.objects.filter(
        tasks__progress=100
    ).distinct().count()

    overdue = Job.objects.filter(
        tasks__deadline__lt=today, tasks__progress__lt=100
    ).distinct().count()

    data = [
        {'status': 'В ходе выполнения', 'count': in_progress, 'percentage': 58.33},
        {'status': 'Законченный', 'count': completed, 'percentage': 25},
        {'status': 'Незаконченный', 'count': overdue, 'percentage': 8}
    ]

    return Response(data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def recent_projects(request):
    """Get recent projects for dashboard"""
    recent_jobs = Job.objects.order_by('-created_at')[:5]
    serializer = JobSerializer(recent_jobs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def upcoming_deadlines(request):
    """Get upcoming task deadlines"""
    today = timezone.now().date()
    upcoming_tasks = Task.objects.filter(
        progress__lt=100,
        deadline__gte=today
    ).select_related('job').order_by('deadline')[:10]

    serializer = TaskSerializer(upcoming_tasks, many=True)
    return Response(serializer.data)


# Calendar API Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def calendar_tasks(request):
    """Get tasks for calendar view"""
    year = int(request.query_params.get('year', timezone.now().year))
    month = int(request.query_params.get('month', timezone.now().month))

    # Get tasks for the specified month
    tasks = Task.objects.filter(
        deadline__year=year,
        deadline__month=month
    ).select_related('job')

    # Group tasks by date
    tasks_by_date = {}
    for task in tasks:
        date_key = task.deadline.strftime('%Y-%m-%d')
        if date_key not in tasks_by_date:
            tasks_by_date[date_key] = []
        tasks_by_date[date_key].append({
            'id': task.id,
            'title': task.title,
            'progress': task.progress,
            'job_title': task.job.title,
            'status_color': TaskSerializer().get_status_color(task)
        })

    return Response(tasks_by_date)
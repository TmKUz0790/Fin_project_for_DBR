
from datetime import timezone, datetime, date
from django.db.models import F, Sum, Q
from django.utils.timezone import now
from django.core.paginator import Paginator
from collections import Counter

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse
import json

from . import models

from .forms import JobForm, TaskFormSet, ClientLoginForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Job, calculate_income_balance
from .forms import TaskFormSet
from django.core.paginator import Paginator
from django.shortcuts import render
from django.contrib.auth.models import User
from collections import Counter
from django.utils import timezone
from .models import Task, DeductionLog
from django.forms import modelformset_factory
from .models import Task

from django.shortcuts import render, get_object_or_404, redirect
from .models import Job
from .forms import TaskFormSet

from django.shortcuts import render, get_object_or_404, redirect
from .models import Job
from .forms import TaskFormSet
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.timezone import now
from django.contrib.auth.models import User
from .models import Task, DeductionLog

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.timezone import now
from django.contrib.auth.models import User
from .models import Task, DeductionLog
# Admin login view
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            # Fetch the user by email
            user = User.objects.get(email=email)
            # Authenticate using the username (Django default) and password
            if user.check_password(password):
                # Log the user in
                login(request, user)
                return redirect('admin_dashboard')
            else:
                messages.error(request, "Invalid password")
        except User.DoesNotExist:
            messages.error(request, "User with this email does not exist")
    return render(request, 'login.html')


@login_required
def create_job(request):
    # Check if the logged-in user has the allowed email
    if request.user.email != 'Admin@dbr.org':
        # Return a 403 Forbidden response if the user is not authorized
        return HttpResponseForbidden("You are not authorized to access this page.")

    if request.method == 'POST':
        job_form = JobForm(request.POST)
        if job_form.is_valid():
            job = job_form.save(commit=False)
            # Hash the client's password before saving
            job.client_password = make_password(job_form.cleaned_data['client_password'])
            job.save()
            return redirect('task_create', job_id=job.id)  # Redirect to task creation
    else:
        job_form = JobForm()

    return render(request, 'create_job.html', {'job_form': job_form})


def create_tasks(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == 'POST':
        task_formset = TaskFormSet(request.POST, instance=job)

        if task_formset.is_valid():
            # Calculate total hours for all tasks
            total_hours = sum([form.cleaned_data['hours'] for form in task_formset if form.cleaned_data.get('hours')])

            for form in task_formset:
                task = form.save(commit=False)
                # Calculate percentage this task represents in the project
                task.task_percentage = (form.cleaned_data['hours'] / total_hours) * 100
                task.job = job  # Ensure the task is associated with the job
                task.save()
                form.save_m2m()  # Save ManyToMany relationships like assigned users

            return redirect('job_list')  # Redirect to job list after saving tasks
    else:
        task_formset = TaskFormSet(instance=job)

    return render(request, 'create_tasks.html', {
        'task_formset': task_formset,
        'job': job,
    })






def job_list(request):
    # Retrieve all jobs
    jobs = Job.objects.all()

    # Set up pagination for jobs (10 jobs per page)
    paginator = Paginator(jobs, 20)  # Show 10 jobs per page
    page_number = request.GET.get('page')
    page_jobs = paginator.get_page(page_number)

    return render(request, 'job_list.html', {
        'jobs': page_jobs,  # Pass the paginated jobs
    })


def client_login(request):
    if request.method == 'POST':
        form = ClientLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Find the job associated with this client
            try:
                job = Job.objects.get(client_email=email)
                if check_password(password, job.client_password):
                    # Store job id in session and redirect to progress page
                    request.session['client_job_id'] = job.id
                    return redirect('client_progress')
                else:
                    messages.error(request, 'Invalid password')
            except Job.DoesNotExist:
                messages.error(request, 'No job found for this email')
    else:
        form = ClientLoginForm()

    return render(request, 'client_login.html', {'form': form})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Task

@login_required
def update_feedback(request):
    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        feedback = request.POST.get('feedback')

        # Получение задачи по идентификатору и проверка прав доступа
        task = get_object_or_404(Task, id=task_id)
        if task:
            task.feedback = feedback
            task.save()
            messages.success(request, "Feedback успешно обновлен!")
        else:
            messages.error(request, "Задача не найдена.")

        return redirect('developer_tasks')  # Перенаправление на страницу со списком задач разработчика

    return HttpResponseForbidden("Метод не поддерживается")


from django.shortcuts import get_object_or_404, redirect, render
from django.utils.safestring import mark_safe
import json

def get_tasks_data(job):
    return [
        {
            'title': task.title,
            'start_date': task.start_date.strftime("%Y-%m-%d") if task.start_date else None,
            'deadline': task.deadline.strftime("%Y-%m-%d") if task.deadline else None,
            'progress': task.progress,
            'description': task.description,
            'task_percentage': task.task_percentage,
            'feedback': task.feedback
        }
        for task in job.tasks.all()
    ]



from django import template

register = template.Library()

@register.filter
def get_item(list_obj, index):
    try:
        return list_obj[index]
    except:
        return None


def client_progress(request):
    job_id = request.session.get('client_job_id')
    if not job_id:
        return redirect('client_login')


    job = get_object_or_404(Job, id=job_id)

    # Import Sum for calculating total hours
    from django.db.models import Sum

    # Filter tasks by type - only get SIMPLE tasks for list view
    simple_tasks = Task.objects.filter(job=job, task_type='SIMPLE')

    # Calculate total hours for simple tasks
    total_simple_hours = simple_tasks.aggregate(Sum('hours'))['hours__sum'] or 0

    # Max hours quota (120)
    max_hours = 120

    # Convert queryset to list of task data dictionaries
    simple_tasks_data = []
    for task in simple_tasks:
        # Get assigned users emails
        assigned_users = [user.email for user in task.assigned_users.all()]

        # Format deadline (if exists)
        deadline = None
        if task.deadline:
            deadline = task.deadline.strftime('%Y-%m-%d')

        # Create task data object
        task_data = {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'progress': task.progress,
            'task_percentage': task.task_percentage,
            'money_for_task': task.money_for_task,
            'deadline': deadline,
            'assigned_users': assigned_users,
            'task_type': task.task_type,
            'hours': task.hours  # Include hours
        }

        simple_tasks_data.append(task_data)

    # Get PATPIS (Follow) tasks for timeline view
    follow_tasks = Task.objects.filter(job=job, task_type='PATPIS').select_related()

    # Initialize variables for sheet view
    all_months = []
    task_groups = {}
    task_matrix = []
    show_follow_tasks = follow_tasks.exists()

    # Process follow tasks for sheet view
    if show_follow_tasks:
        import re
        from datetime import datetime, timedelta

        # Find earliest and latest deadlines
        from django.db.models import Min, Max
        follow_task_stats = follow_tasks.aggregate(
            earliest_deadline=Min('deadline'),
            latest_follow_deadline=Max('deadline')
        )

        earliest_deadline = follow_task_stats['earliest_deadline']
        latest_follow_deadline = follow_task_stats['latest_follow_deadline']

        # Get current month for timeline color coding
        current_month = datetime.now().strftime("%B %Y")

        if earliest_deadline and latest_follow_deadline:
            # Ensure we have at least 12 months from earliest date
            min_end_date = earliest_deadline + timedelta(days=365)
            if latest_follow_deadline < min_end_date:
                latest_follow_deadline = min_end_date

            # Generate all months between earliest and latest deadline
            current_date = earliest_deadline.replace(day=1)
            while current_date <= latest_follow_deadline:
                month_str = current_date.strftime("%B %Y")
                all_months.append(month_str)
                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)

        # Compile regex once outside the loop
        pattern = re.compile(r'(.*) \((.*)\)')

        # Extract all months and base names from tasks
        for task in follow_tasks:
            match = pattern.match(task.title)
            if match:
                base_name = match.group(1)
                month = match.group(2)

                # If month isn't in our all_months list, add it
                if month not in all_months:
                    all_months.append(month)

                # Initialize the task group if it doesn't exist
                if base_name not in task_groups:
                    task_groups[base_name] = {}

                # For each base_name+month combination, store related tasks
                if month not in task_groups[base_name]:
                    task_groups[base_name][month] = []

                # Add this task to the list for this month
                task_groups[base_name][month].append(task)

        # Cache for parsed dates to avoid repeated parsing
        month_cache = {}

        # Sort months chronologically
        def month_sort_key(month_str):
            if month_str in month_cache:
                return month_cache[month_str]

            try:
                date_obj = datetime.strptime(month_str, "%B %Y")
                month_cache[month_str] = date_obj
                return date_obj
            except ValueError:
                try:
                    date_obj = datetime.strptime(month_str, "%B")
                    date_obj = date_obj.replace(year=datetime.now().year)
                    month_cache[month_str] = date_obj
                    return date_obj
                except ValueError:
                    month_cache[month_str] = datetime.now()
                    return datetime.now()

        all_months.sort(key=month_sort_key)

        # Build the matrix with month type information for color coding
        for base_name in sorted(task_groups.keys()):
            row = {
                'base_name': base_name,
                'cells': []
            }

            # Find when this task type first appears
            first_task_month = None
            for month in all_months:
                if month in task_groups[base_name]:
                    first_task_month = month
                    break

            first_month_found = False

            for i, month in enumerate(all_months):
                # If we haven't found the first month for this task yet, and this isn't it,
                # add empty cell to create gap
                if not first_month_found and month != first_task_month:
                    row['cells'].append({
                        'tasks': [],
                        'empty': True,
                        'month_type': None  # No month type for empty cells
                    })
                # Once we find the first month or have already found it, process normally
                elif month in task_groups[base_name] or first_month_found:
                    first_month_found = True
                    if month in task_groups[base_name]:
                        # Determine month type for color coding
                        task_progress = task_groups[base_name][month][0].progress

                        if task_progress == 100:
                            month_type = "completed"
                        elif month == current_month:
                            month_type = "current"
                        elif month_sort_key(month) < month_sort_key(current_month):
                            month_type = "past"
                        else:
                            month_type = "future"

                        row['cells'].append({
                            'tasks': task_groups[base_name][month],
                            'empty': False,
                            'month_type': month_type  # Add month type to each cell
                        })
                    else:
                        row['cells'].append({
                            'tasks': [],
                            'empty': True,
                            'month_type': None
                        })

            task_matrix.append(row)

    # Prepare context with hours tracking data
    latest_deadline = Task.objects.filter(job=job).aggregate(Max('deadline'))['deadline__max']
    current_date = datetime.now()

    # Format the latest deadline for display (if it exists)
    formatted_latest_deadline = None
    if latest_deadline:
        formatted_latest_deadline = latest_deadline.strftime("%b %d, %Y")  # e.g., "Mar 25, 2025"

    # Add it to your context
    context = {
        'job': job,
        'tasks': mark_safe(json.dumps(simple_tasks_data)),  # Only simple tasks for list view
        'latest_deadline': latest_deadline,
        'formatted_latest_deadline': formatted_latest_deadline,
        'current_date': current_date,

        'show_follow_tasks': show_follow_tasks,
        'all_months': all_months,
        'task_matrix': task_matrix,
        'total_simple_hours': total_simple_hours,  # Add total hours to context
        'max_hours': max_hours,  # Add max hours to context
        'hours_percentage': int((total_simple_hours / max_hours) * 100) if max_hours > 0 else 0  # Calculate percentage
    }

    return render(request, 'client_progress.html', context)

def get_tasks_data(tasks_queryset):
    """
    Converts a tasks queryset to a JSON-serializable format for the client.
    Fixed to properly iterate through the queryset.
    """
    tasks_data = []

    for task in tasks_queryset:
        # Get assigned users emails
        assigned_users = [user.email for user in task.assigned_users.all()]

        # Format deadline (if exists)
        deadline = None
        if task.deadline:
            deadline = task.deadline.strftime('%Y-%m-%d')

        # Create task data object
        task_data = {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'progress': task.progress,
            'task_percentage': task.task_percentage,
            'money_for_task': task.money_for_task,
            'deadline': deadline,
            'assigned_users': assigned_users,
            'task_type': task.task_type
        }

        tasks_data.append(task_data)

    return tasks_data

def client_progress_details(request):
    job_id = request.session.get('client_job_id')
    if not job_id:
        return redirect('client_login')

    job = get_object_or_404(Job, id=job_id)
    tasks_data = get_tasks_data(job)

    context = {
        'job': job,
        'tasks': mark_safe(json.dumps(tasks_data))  # Сериализуем данные в JSON
    }
    return render(request, 'client_progress_details.html', context)


def developer_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Authenticate based on email (developers log in using email)
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                # Log the developer in
                login(request, user)
                return redirect('developer_tasks')  # Redirect to developer's tasks
            else:
                messages.error(request, 'Invalid password')
        except User.DoesNotExist:
            messages.error(request, 'User with this email does not exist')
    return render(request, 'developer_login.html')




from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import Task, DeductionLog

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Task, DeductionLog

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Task, DeductionLog

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Task, DeductionLog

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Task, DeductionLog

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Task, DeductionLog


@login_required
def developer_tasks(request):
    try:
        developer = request.user
        # Get all tasks assigned to the developer with related job data
        tasks = Task.objects.filter(assigned_users=developer) \
            .select_related('job') \
            .prefetch_related('assigned_users') \
            .order_by('deadline')

        # Get the section parameter from URL (if any)
        section = request.GET.get('section', 'task-list')

        # Get feedback tasks (tasks that can receive feedback)
        feedback_tasks = tasks.filter(progress__gt=0)  # Only allow feedback for started tasks

        # Process tasks for display
        processed_tasks = []
        for task in tasks:
            # Calculate wave animation offset based on progress
            progress_offset = 125.6 - (task.progress / 100 * 125.6)
            task.progress_offset = progress_offset

            # Calculate task status and deadline info
            if task.deadline:
                days_until_deadline = (task.deadline - timezone.now().date()).days
                if days_until_deadline > 10:
                    task.status = 'task_green'
                elif 5 < days_until_deadline <= 10:
                    task.status = 'task_yellow'
                elif 0 <= days_until_deadline <= 5:
                    task.status = 'task_red'
                else:
                    task.status = 'overdue'
            else:
                task.status = 'no_deadline'

            processed_tasks.append(task)

        # Paginate main task list
        paginator = Paginator(processed_tasks, 15)  # Show 15 tasks per page
        page_number = request.GET.get('page')
        page_tasks = paginator.get_page(page_number)

        # Paginate feedback tasks separately
        feedback_paginator = Paginator(feedback_tasks, 10)  # Show 10 feedback tasks per page
        feedback_page = request.GET.get('feedback_page')
        page_feedback_tasks = feedback_paginator.get_page(feedback_page)

        # Calculate total balance from paid tasks
        total_balance = sum(task.money_for_task for task in tasks.filter(paid=True))

        # Get recent notifications or updates
        recent_updates = DeductionLog.objects.filter(developer=developer).order_by('-deduction_date')[:5]

        # Prepare task statistics
        task_stats = {
            'total_tasks': tasks.count(),
            'completed_tasks': tasks.filter(progress=100).count(),
            'in_progress_tasks': tasks.filter(progress__gt=0, progress__lt=100).count(),
            'pending_tasks': tasks.filter(progress=0).count(),
            'overdue_tasks': tasks.filter(deadline__lt=timezone.now().date(), progress__lt=100).count()
        }

        context = {
            'tasks': page_tasks,
            'feedback_tasks': page_feedback_tasks,
            'balance': total_balance,
            'section': section,
            'recent_updates': recent_updates,
            'task_stats': task_stats,
            'active_page': 'developer_tasks',
            'today': timezone.now().date(),
        }

        return render(request, 'developer_tasks.html', context)

    except Exception as e:
        print(f"Error in developer_tasks view: {str(e)}")
        # Log the full error traceback
        import traceback
        traceback.print_exc()

        # Return error page with message
        return render(request, 'error.html', {
            'error_message': 'An error occurred while loading tasks.',
            'error_details': str(e),
            'show_details': request.user.is_staff  # Only show error details to staff
        }, status=500)
@login_required
def payment_history(request):
    developer = request.user
    deduction_logs = DeductionLog.objects.filter(developer=developer).order_by('-deduction_date')

    return render(request, 'payment_history.html', {
        'developer': developer,
        'deduction_logs': deduction_logs
    })



from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q, F, Min, Max
from django.utils.timezone import now
from collections import Counter
from datetime import timedelta

from .models import Job, Task, DeductionLog, calculate_income_balance


@login_required
def admin_dashboard(request):
    # Permission check
    if request.user.email != 'Admin@dbr.org':
        return HttpResponseForbidden("You are not authorized to access this page.")

    today = now().date()
    current_month = today.month
    current_year = today.year

    # Basic job & task stats
    jobs = Job.objects.all()
    total_jobs = jobs.count()

    # Count this month's jobs
    this_month_jobs = Job.objects.filter(
        created_at__year=current_year,
        created_at__month=current_month
    ).count()

    # Task counts by type
    simple_tasks_count = Task.objects.filter(
        task_type='SIMPLE',
        progress__lt=100  # less than 100% complete
    ).count()

    # Get all monthly tasks
    monthly_tasks = Task.objects.filter(
        task_type='MONTHLY'
    ).count()

    # Get this month's tasks (both simple and monthly)
    this_month_tasks = Task.objects.filter(
        deadline__year=current_year,
        deadline__month=current_month,
        task_type__in=['SIMPLE', 'MONTHLY']
    ).count()

    # Financial data
    total_income = jobs.aggregate(total_income=Sum('over_all_income'))['total_income'] or 0
    in_time_processes_money = calculate_income_balance()["income_balance"]

    # Overdue task count
    overdue_task_count = Task.objects.filter(
        progress__lt=100,
        deadline__lt=today
    ).count()

    # Calculate monthly income (jobs created this month)
    monthly_income = Job.objects.filter(
        created_at__year=current_year,
        created_at__month=current_month
    ).aggregate(monthly_total=Sum('over_all_income'))['monthly_total'] or 0

    # Get developer data with task status
    developers = User.objects.prefetch_related('developer_tasks')
    developer_data = []

    for developer in developers:
        assigned_tasks = Task.objects.filter(assigned_users=developer).select_related('job')
        status_counter = Counter({'task_green': 0, 'task_yellow': 0, 'task_red': 0, 'overdue': 0, 'done': 0})
        task_info = []

        for task in assigned_tasks:
            days_until_deadline = (task.deadline - today).days if task.deadline else None

            if task.progress == 100:
                task_color = 'done'
                status_counter['done'] += 1
            else:
                if days_until_deadline is not None:
                    if days_until_deadline > 10:
                        task_color = 'task_green'
                        status_counter['task_green'] += 1
                    elif 5 < days_until_deadline <= 10:
                        task_color = 'task_yellow'
                        status_counter['task_yellow'] += 1
                    elif 0 <= days_until_deadline <= 5:
                        task_color = 'task_red'
                        status_counter['task_red'] += 1
                    else:
                        task_color = 'overdue'
                        status_counter['overdue'] += 1
                else:
                    task_color = None

            task_info.append({
                'task': task,
                'days_until_deadline': days_until_deadline,
                'color': task_color
            })

        # Get 5 most recent tasks for the detail view
        from django.core.paginator import Paginator
        task_paginator = Paginator(task_info, 5)
        page_number = request.GET.get(f'page_{developer.id}', 1)
        page_obj = task_paginator.get_page(page_number)

        # Calculate balance
        balance = assigned_tasks.filter(paid=True).aggregate(
            total_balance=Sum('money_for_task')
        )['total_balance'] or 0

        developer_data.append({
            'developer': developer,
            'tasks': page_obj,
            'balance': balance,
            'status_counts': status_counter,
        })

    # Limit developer data for dashboard display
    developer_data = developer_data[:4]  # Show only 4 developers on dashboard

    # Get recent jobs (5 most recent)
    recent_jobs = Job.objects.order_by('-created_at')[:5]

    # Add job.get_overall_progress and get_overdue_tasks_count methods to the Job model
    for job in recent_jobs:
        if not hasattr(job, 'get_overall_progress'):
            job.get_overall_progress = lambda: Task.objects.filter(job=job).aggregate(
                avg_progress=Sum(F('progress') * F('task_percentage')) / 100
            )['avg_progress'] or 0

        if not hasattr(job, 'get_overdue_tasks_count'):
            job.get_overdue_tasks_count = Task.objects.filter(
                job=job,
                progress__lt=100,
                deadline__lt=today
            ).count()

        if not hasattr(job, 'get_latest_deadline'):
            job.get_latest_deadline = Task.objects.filter(job=job).aggregate(
                latest=Max('deadline')
            )['latest']

    # Get upcoming deadlines (10 tasks with closest deadlines that aren't overdue)
    upcoming_tasks = Task.objects.filter(
        progress__lt=100,  # Not completed
        deadline__gte=today  # Not overdue
    ).order_by('deadline')[:8]

    # Add days_until_deadline property to tasks
    for task in upcoming_tasks:
        task.days_until_deadline = (task.deadline - today).days if task.deadline else None

    # Overall completion rate for all active projects
    total_progress = Task.objects.aggregate(
        weighted_progress=Sum(F('progress') * F('task_percentage')) / 100
    )['weighted_progress'] or 0
    overall_completion_rate = int(total_progress)

    context = {
        'total_jobs': total_jobs,
        'this_month_jobs': this_month_jobs,  # New context variable for this month's jobs
        'total_income': total_income,
        'in_time_processes_money': in_time_processes_money,
        'overdue_task_count': overdue_task_count,
        'monthly_income': monthly_income,
        'developer_data': developer_data,
        'simple_tasks_count': simple_tasks_count,
        'monthly_tasks': monthly_tasks,
        'this_month_tasks': this_month_tasks,  # All tasks for this month
        'recent_jobs': recent_jobs,
        'upcoming_tasks': upcoming_tasks,
        'overall_completion_rate': overall_completion_rate,
    }

    return render(request, 'admin_dashboard.html', context)
# @login_required
# def admin_dashboard(request):
#     # Permission check
#     if request.user.email != 'Admin@dbr.org':
#         return HttpResponseForbidden("You are not authorized to access this page.")
#
#     today = now().date()
#
#     # Basic job & task stats
#     jobs = Job.objects.all()
#     total_jobs = jobs.count()
#
#     # Task counts by type
#     simple_tasks_count = Task.objects.filter(
#         task_type='SIMPLE',
#         progress__lt=100  # less than 100% complete
#     ).count()
#
#     monthly_tasks = Task.objects.filter(
#         task_type='MONTHLY',
#         progress__lt=100
#     ).count()
#
#     # Financial data
#     total_income = jobs.aggregate(total_income=Sum('over_all_income'))['total_income'] or 0
#     in_time_processes_money = calculate_income_balance()["income_balance"]
#
#     # Overdue task count
#     overdue_task_count = Task.objects.filter(
#         progress__lt=100,
#         deadline__lt=today
#     ).count()
#
#     # Calculate monthly income (jobs created this month)
#     current_month = now().month
#     current_year = now().year
#     monthly_income = Job.objects.filter(
#         created_at__year=current_year,
#         created_at__month=current_month
#     ).aggregate(monthly_total=Sum('over_all_income'))['monthly_total'] or 0
#
#     # Get developer data with task status
#     developers = User.objects.prefetch_related('developer_tasks')
#     developer_data = []
#
#     for developer in developers:
#         assigned_tasks = Task.objects.filter(assigned_users=developer).select_related('job')
#         status_counter = Counter({'task_green': 0, 'task_yellow': 0, 'task_red': 0, 'overdue': 0, 'done': 0})
#         task_info = []
#
#         for task in assigned_tasks:
#             days_until_deadline = (task.deadline - today).days if task.deadline else None
#
#             if task.progress == 100:
#                 task_color = 'done'
#                 status_counter['done'] += 1
#             else:
#                 if days_until_deadline is not None:
#                     if days_until_deadline > 10:
#                         task_color = 'task_green'
#                         status_counter['task_green'] += 1
#                     elif 5 < days_until_deadline <= 10:
#                         task_color = 'task_yellow'
#                         status_counter['task_yellow'] += 1
#                     elif 0 <= days_until_deadline <= 5:
#                         task_color = 'task_red'
#                         status_counter['task_red'] += 1
#                     else:
#                         task_color = 'overdue'
#                         status_counter['overdue'] += 1
#                 else:
#                     task_color = None
#
#             task_info.append({
#                 'task': task,
#                 'days_until_deadline': days_until_deadline,
#                 'color': task_color
#             })
#
#         # Get 5 most recent tasks for the detail view
#         from django.core.paginator import Paginator
#         task_paginator = Paginator(task_info, 5)
#         page_number = request.GET.get(f'page_{developer.id}', 1)
#         page_obj = task_paginator.get_page(page_number)
#
#         # Calculate balance
#         balance = assigned_tasks.filter(paid=True).aggregate(
#             total_balance=Sum('money_for_task')
#         )['total_balance'] or 0
#
#         developer_data.append({
#             'developer': developer,
#             'tasks': page_obj,
#             'balance': balance,
#             'status_counts': status_counter,
#         })
#
#     # Limit developer data for dashboard display
#     developer_data = developer_data[:4]  # Show only 4 developers on dashboard
#
#     # Get recent jobs (5 most recent)
#     recent_jobs = Job.objects.order_by('-created_at')[:5]
#
#     # Add job.get_overall_progress and get_overdue_tasks_count methods to the Job model
#     for job in recent_jobs:
#         if not hasattr(job, 'get_overall_progress'):
#             job.get_overall_progress = lambda: Task.objects.filter(job=job).aggregate(
#                 avg_progress=Sum(F('progress') * F('task_percentage')) / 100
#             )['avg_progress'] or 0
#
#         if not hasattr(job, 'get_overdue_tasks_count'):
#             job.get_overdue_tasks_count = Task.objects.filter(
#                 job=job,
#                 progress__lt=100,
#                 deadline__lt=today
#             ).count()
#
#         if not hasattr(job, 'get_latest_deadline'):
#             job.get_latest_deadline = Task.objects.filter(job=job).aggregate(
#                 latest=Max('deadline')
#             )['latest']
#
#     # Get upcoming deadlines (10 tasks with closest deadlines that aren't overdue)
#     upcoming_tasks = Task.objects.filter(
#         progress__lt=100,  # Not completed
#         deadline__gte=today  # Not overdue
#     ).order_by('deadline')[:8]
#
#     # Add days_until_deadline property to tasks
#     for task in upcoming_tasks:
#         task.days_until_deadline = (task.deadline - today).days if task.deadline else None
#
#     # Overall completion rate for all active projects
#     total_progress = Task.objects.aggregate(
#         weighted_progress=Sum(F('progress') * F('task_percentage')) / 100
#     )['weighted_progress'] or 0
#     overall_completion_rate = int(total_progress)
#
#     context = {
#         'total_jobs': total_jobs,
#         'total_income': total_income,
#         'in_time_processes_money': in_time_processes_money,
#         'overdue_task_count': overdue_task_count,
#         'monthly_income': monthly_income,
#         'developer_data': developer_data,
#         'simple_tasks_count': simple_tasks_count,
#         'monthly_tasks': monthly_tasks,
#         'recent_jobs': recent_jobs,
#         'upcoming_tasks': upcoming_tasks,
#         'overall_completion_rate': overall_completion_rate,
#     }
#
#     return render(request, 'admin_dashboard.html', context)


from django.db.models import Max, Sum



def job_details(request, job_id):
    # Fetch the specific job or return a 404 error if not found
    job = get_object_or_404(Job.objects.select_related(), id=job_id)

    # Retrieve all tasks associated with this job, keeping the original filtering
    regular_tasks = Task.objects.filter(job=job, task_type__in=['SIMPLE', 'MONTHLY']).select_related()
    follow_tasks = Task.objects.filter(job=job, task_type='PATPIS').select_related()

    from django.db.models import Min, Max, Sum

    # Set up pagination for regular tasks
    regular_paginator = Paginator(regular_tasks, 10)  # Show 10 tasks per page
    regular_page_number = request.GET.get('page')
    page_regular_tasks = regular_paginator.get_page(regular_page_number)

    # Set up pagination for follow tasks
    follow_paginator = Paginator(follow_tasks, 10)  # Show 10 tasks per page
    follow_page_number = request.GET.get('follow_page')
    page_follow_tasks = follow_paginator.get_page(follow_page_number)

    # Combine aggregations into a single query
    task_stats = Task.objects.filter(job=job).aggregate(
        latest_deadline=Max('deadline'),
        total_payment=Sum('money_for_task')
    )

    # Get values from the aggregation
    latest_deadline = task_stats['latest_deadline']
    total_task_payment = task_stats['total_payment'] or 0

    # Get the overall progress of the job
    overall_progress = job.get_overall_progress() if job.get_overall_progress() else 0

    # Calculate the remaining income
    remaining_income = job.over_all_income - total_task_payment

    # Process follow tasks for sheet view
    all_months = []
    task_groups = {}
    task_matrix = []

    if follow_tasks:
        import re
        from datetime import datetime, timedelta

        # Find earliest and latest deadlines to create a complete month range
        follow_task_stats = follow_tasks.aggregate(
            earliest_deadline=Min('deadline'),
            latest_follow_deadline=Max('deadline')
        )

        earliest_deadline = follow_task_stats['earliest_deadline']
        latest_follow_deadline = follow_task_stats['latest_follow_deadline']

        if earliest_deadline and latest_follow_deadline:
            # Ensure we have at least 12 months from earliest date
            min_end_date = earliest_deadline + timedelta(days=365)
            if latest_follow_deadline < min_end_date:
                latest_follow_deadline = min_end_date

            # Generate all months between earliest and latest deadline
            current_date = earliest_deadline.replace(day=1)
            while current_date <= latest_follow_deadline:
                month_str = current_date.strftime("%B %Y")
                all_months.append(month_str)
                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)

        # Compile regex once outside the loop
        pattern = re.compile(r'(.*) \((.*)\)')

        # Extract all months and base names from tasks
        for task in follow_tasks:
            match = pattern.match(task.title)
            if match:
                base_name = match.group(1)
                month = match.group(2)

                # If month isn't in our all_months list (might happen with unusual formatting),
                # add it to ensure all task data is displayed
                if month not in all_months:
                    all_months.append(month)

                # Initialize the task group if it doesn't exist
                if base_name not in task_groups:
                    task_groups[base_name] = {}

                # For each base_name+month combination, store all related tasks in a list
                if month not in task_groups[base_name]:
                    task_groups[base_name][month] = []

                # Add this task to the list for this month
                task_groups[base_name][month].append(task)

        # Cache for parsed dates to avoid repeated parsing
        month_cache = {}

        # Sort months chronologically
        def month_sort_key(month_str):
            if month_str in month_cache:
                return month_cache[month_str]

            try:
                date_obj = datetime.strptime(month_str, "%B %Y")
                month_cache[month_str] = date_obj
                return date_obj
            except ValueError:
                try:
                    date_obj = datetime.strptime(month_str, "%B")
                    date_obj = date_obj.replace(year=datetime.now().year)
                    month_cache[month_str] = date_obj
                    return date_obj
                except ValueError:
                    month_cache[month_str] = datetime.now()
                    return datetime.now()

        all_months.sort(key=month_sort_key)

        # Build the matrix
        for base_name in sorted(task_groups.keys()):
            row = {
                'base_name': base_name,
                'cells': []
            }

            # Find when this task type first appears
            first_task_month = None
            for month in all_months:
                if month in task_groups[base_name]:
                    first_task_month = month
                    break

            first_month_found = False

            for month in all_months:
                # If we haven't found the first month for this task yet, and this isn't it,
                # add empty cell to create gap
                if not first_month_found and month != first_task_month:
                    row['cells'].append({
                        'tasks': [],
                        'empty': True
                    })
                # Once we find the first month or have already found it, process normally
                elif month in task_groups[base_name] or first_month_found:
                    first_month_found = True
                    if month in task_groups[base_name]:
                        row['cells'].append({
                            'tasks': task_groups[base_name][month],
                            'empty': False
                        })
                    else:
                        row['cells'].append({
                            'tasks': [],
                            'empty': True
                        })

            task_matrix.append(row)

    return render(request, 'job_details.html', {
        'job': job,
        'regular_tasks': page_regular_tasks,
        'follow_tasks': page_follow_tasks,
        'latest_deadline': latest_deadline,
        'overall_progress': overall_progress,
        'total_task_payment': total_task_payment,
        'remaining_income': remaining_income,
        'show_follow_tasks': follow_tasks.exists(),
        # Sheet view data
        'all_months': all_months,
        'task_matrix': task_matrix,
    })






def deduction_logs_admin(request):
    # Fetch all users for the user filter dropdown
    users = User.objects.all()

    # Get unique months from DeductionLog dates
    all_deduction_logs = DeductionLog.objects.all()
    months = all_deduction_logs.dates('deduction_date', 'month')

    # Get selected user and month from the request parameters
    selected_user = request.GET.get('user')
    selected_month = request.GET.get('month')

    # Apply filters
    if selected_user:
        all_deduction_logs = all_deduction_logs.filter(developer__id=selected_user)
    if selected_month:
        year, month = map(int, selected_month.split('-'))
        all_deduction_logs = all_deduction_logs.filter(deduction_date__year=year, deduction_date__month=month)

    return render(request, 'deduction_logs_admin.html', {
        'all_deduction_logs': all_deduction_logs,
        'users': users,
        'months': months,
        'selected_user': selected_user,
        'selected_month': selected_month,
    })

@login_required
def deduct_balance(request, developer_id):
    developer = get_object_or_404(User, id=developer_id)
    tasks = Task.objects.filter(assigned_users=developer)

    if request.method == 'POST':
        deduction_amount = int(request.POST.get('deduction_amount', 0))
        current_balance = sum(task.money_for_task for task in tasks if task.paid)

        if deduction_amount <= current_balance:
            original_deduction_amount = deduction_amount  # Store the original deduction amount for logging

            for task in tasks.filter(paid=True):
                if deduction_amount <= 0:
                    break
                if task.money_for_task <= deduction_amount:
                    deduction_amount -= task.money_for_task
                    task.money_for_task = 0
                else:
                    task.money_for_task -= deduction_amount
                    deduction_amount = 0
                task.save()

            # Create a log entry
            DeductionLog.objects.create(
                developer=developer,
                deducted_by=request.user,
                deduction_amount=original_deduction_amount,  # Use the original amount for logging
                deduction_date=now(),  # Log the time of deduction
            )

            messages.success(request,
                             f"Successfully deducted {original_deduction_amount} USD from {developer.username}'s balance.")
        else:
            messages.error(request, "Deduction amount exceeds current balance.")
        return redirect('admin_dashboard')

    # Calculate current balance for the developer
    balance = sum(task.money_for_task for task in tasks if task.paid)

    return render(request, 'deduct_balance.html', {
        'developer': developer,
        'balance': balance,
    })

def deduction_page(request):
    # Retrieve all developers
    developers = User.objects.all()

    return render(request, 'deduction_page.html', {
        'developers': developers,
    })

@login_required
def all_deduction_logs(request):
    # Retrieve all deduction logs, ordered by date (latest first)
    logs = DeductionLog.objects.all().order_by('-deduction_date')
    return render(request, 'all_deduction_logs.html', {'deduction_logs': logs})


@login_required
def deduction_logs(request, developer_id):
    developer = get_object_or_404(User, id=developer_id)
    logs = DeductionLog.objects.filter(developer=developer).order_by('-deduction_date')
    return render(request, 'deduction_logs.html', {
        'developer': developer,
        'deduction_logs': logs,
    })
from django.shortcuts import render
from .models import DeductionLog
from django.utils.dateparse import parse_date
from django.db.models import Q

def payment_history(request):
    deduction_logs = DeductionLog.objects.all()

    # Получение параметров фильтрации из запроса
    amount = request.GET.get('amount')
    username = request.GET.get('username')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Фильтрация по сумме, если указана
    if amount:
        deduction_logs = deduction_logs.filter(deduction_amount=amount)

    # Фильтрация по имени пользователя, если указано
    if username:
        deduction_logs = deduction_logs.filter(deducted_by__username__icontains=username)

    # Фильтрация по дате, если указаны значения
    if start_date:
        deduction_logs = deduction_logs.filter(deduction_date__gte=parse_date(start_date))
    if end_date:
        deduction_logs = deduction_logs.filter(deduction_date__lte=parse_date(end_date))

    return render(request, 'payment_history.html', {'deduction_logs': deduction_logs})

@login_required
def overdue_tasks(request):
    # Fetch overdue tasks
    overdue_tasks = Task.objects.filter(
        progress__lt=100,  # Not completed
        deadline__lt=now().date()  # Deadline in the past
    ).select_related('job').prefetch_related('assigned_users')  # Use prefetch_related for many-to-many

    context = {
        'overdue_tasks': overdue_tasks,
    }
    return render(request, 'overdue_tasks.html', context)
from django.shortcuts import get_object_or_404, redirect, render
from django.forms import inlineformset_factory
from .models import Job, Task
from .forms import JobForm, TaskFormSet
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from .models import Job, Task
from .forms import JobForm, TaskForm

def update_job(request, job_id):
    # Get the job instance
    job = get_object_or_404(Job, id=job_id)

    # Create the inline formset for tasks
    TaskFormSet = inlineformset_factory(
        Job, Task,
        form=TaskForm,
        extra=0,  # Show no extra empty forms initially
        can_delete=True  # Allow deletion of tasks
    )

    # Bind forms with POST data if applicable
    job_form = JobForm(request.POST or None, instance=job)
    task_formset = TaskFormSet(request.POST or None, instance=job)

    if request.method == 'POST':
        # Check if both forms are valid
        if job_form.is_valid() and task_formset.is_valid():
            job_form.save()  # Save the job changes
            task_formset.save()  # Save changes to the tasks (add, edit, delete)
            return redirect('job_list')  # Redirect to job list or another appropriate page

    return render(request, 'update_job.html', {
        'job_form': job_form,
        'task_formset': task_formset,
        'job': job,
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from django.http import HttpResponse
from .models import Job, Task
from .forms import TaskForm
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from django.http import HttpResponse
from .models import Job, Task
from .forms import TaskForm
import logging

logger = logging.getLogger(__name__)
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from django.http import HttpResponse
from .models import Job, Task
from .forms import TaskForm
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from .models import Job, Task
from .forms import TaskForm
import logging

logger = logging.getLogger(__name__)
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from django.db import transaction
from .models import Job, Task
from .forms import TaskForm
import logging

logger = logging.getLogger(__name__)
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from django.db import transaction
from django.contrib import messages
from .models import Job, Task
from .forms import TaskForm
import logging

logger = logging.getLogger(__name__)
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import inlineformset_factory
from django.db import transaction
from django.contrib import messages
from django.db.models import Sum  # Correct import
from .models import Job, Task
from .forms import TaskForm
import logging

logger = logging.getLogger(__name__)



@login_required
def add_task_to_job(request, job_id):
    """Optimized view for adding tasks to a job without loading existing tasks in the form"""
    # Quick permission check
    if request.user.email != 'Admin@dbr.org':
        return HttpResponseForbidden("You are not authorized to add tasks.")

    # Get job with minimal query
    job = get_object_or_404(Job, id=job_id)

    # Create the form without the non-editable start_date field
    TaskFormSet = inlineformset_factory(
        Job, Task,
        form=TaskForm,
        exclude=['start_date'],
        extra=1,
        can_delete=False,
        max_num=1
    )

    if request.method == 'POST':
        # Initialize formset without querying existing tasks
        task_formset = TaskFormSet(request.POST, instance=job, queryset=Task.objects.none())

        if task_formset.is_valid():
            try:
                # Get date range directly from POST data
                range_start_date_str = request.POST.get('range_start_date')
                range_end_date_str = request.POST.get('range_end_date')

                # Parse dates
                from datetime import datetime
                start_date = None
                end_date = None

                if range_start_date_str:
                    try:
                        start_date = datetime.strptime(range_start_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        messages.error(request, "Invalid start date format")
                        return render(request, 'add_task_to_job.html', {
                            'task_formset': task_formset,
                            'job': job,
                        })

                if range_end_date_str:
                    try:
                        end_date = datetime.strptime(range_end_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        messages.error(request, "Invalid end date format")
                        return render(request, 'add_task_to_job.html', {
                            'task_formset': task_formset,
                            'job': job,
                        })

                # Default dates if not provided
                if not start_date:
                    start_date = timezone.now().date()

                if not end_date:
                    end_date = start_date.replace(year=start_date.year + 1)

                # Check if start date is before end date
                if start_date > end_date:
                    messages.error(request, "Start date must be before end date")
                    return render(request, 'add_task_to_job.html', {
                        'task_formset': task_formset,
                        'job': job,
                    })

                # Process tasks
                with transaction.atomic():
                    # Get total existing hours with a simple aggregation query
                    from django.db.models import Sum
                    existing_hours = Task.objects.filter(job=job).aggregate(Sum('hours'))['hours__sum'] or 0

                    # Get the new tasks
                    new_tasks = []
                    new_tasks_hours = 0

                    for form in task_formset:
                        if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                            new_task = form.save(commit=False)
                            new_task.job = job
                            new_tasks.append((form, new_task))
                            new_tasks_hours += new_task.hours

                    # Calculate total hours
                    total_hours = existing_hours + new_tasks_hours

                    if total_hours <= 0:
                        messages.error(request, "Total hours must be greater than zero.")
                        return render(request, 'add_task_to_job.html', {
                            'task_formset': task_formset,
                            'job': job,
                        })

                    # Save new tasks
                    for form, task in new_tasks:
                        # Set percentage
                        task.task_percentage = (task.hours / total_hours) * 100

                        # Special handling for PATPIS tasks
                        if task.task_type == 'PATPIS':
                            # Set deadline to start date
                            task.deadline = start_date

                            # Format title for first task
                            base_title = task.title
                            if '(' in base_title and ')' in base_title:
                                base_title = base_title[:base_title.rfind('(')].strip()

                            month_year = start_date.strftime('%B %Y')
                            task.title = f"{base_title} ({month_year})"

                        # Save first task
                        task.save()

                        # Save many-to-many relationships
                        form.save_m2m()

                        # Create recurring tasks if needed
                        if task.task_type == 'PATPIS' and start_date and end_date and start_date < end_date:
                            from dateutil.relativedelta import relativedelta
                            import calendar

                            base_date = start_date
                            day_of_month = base_date.day
                            current_date = base_date + relativedelta(months=1)

                            # Store assigned users
                            assigned_users = list(task.assigned_users.all())

                            # Create tasks for each month individually with proper assignments
                            month_count = 0
                            task_count = 1  # Starting at 1 to account for the first task

                            while current_date <= end_date:
                                month_count += 1
                                if month_count > 100:  # Safety limit
                                    break

                                # Adjust day for month length
                                max_day = calendar.monthrange(current_date.year, current_date.month)[1]
                                actual_day = min(day_of_month, max_day)
                                target_date = current_date.replace(day=actual_day)

                                if target_date > end_date:
                                    break

                                month_year = target_date.strftime('%B %Y')

                                # Create and save each recurring task individually
                                recurring_task = Task(
                                    job=job,
                                    title=f"{base_title} ({month_year})",
                                    hours=task.hours,
                                    description=task.description,
                                    task_percentage=task.task_percentage,
                                    money_for_task=task.money_for_task,
                                    task_type='PATPIS',
                                    deadline=target_date
                                )
                                # Save immediately to get an ID
                                recurring_task.save()
                                task_count += 1

                                # Assign users to the saved task
                                if assigned_users:
                                    for user in assigned_users:
                                        recurring_task.assigned_users.add(user)

                                # Move to next month
                                current_date = current_date + relativedelta(months=1)

                    # Update existing task percentages
                    if existing_hours > 0 and new_tasks_hours > 0:
                        # Update all existing tasks in one query using Django's update method
                        from django.db.models import F, ExpressionWrapper, FloatField
                        Task.objects.filter(job=job).exclude(
                            id__in=[t[1].id for t in new_tasks]
                        ).update(
                            task_percentage=ExpressionWrapper(
                                (F('hours') * 100) / total_hours,
                                output_field=FloatField()
                            )
                        )

                # Success - redirect to job details
                messages.success(request, "Tasks successfully added to the job.")
                return redirect('job_details', job_id=job.id)

            except Exception as e:
                import traceback
                traceback.print_exc()
                messages.error(request, f"An error occurred: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # For GET requests, don't load existing tasks
        task_formset = TaskFormSet(instance=job, queryset=Task.objects.none())

    return render(request, 'add_task_to_job.html', {
        'task_formset': task_formset,
        'job': job,
    })





from django.db.models import Sum
from django.shortcuts import render
from .models import Task, DeductionLog, User

def developer_payment_sheet(request):
    # Get the developer_id from query parameters
    developer_id = request.GET.get('developer_id')

    # Fetch developers (all or filtered by ID if provided)
    if developer_id:
        developers = User.objects.filter(id=developer_id).prefetch_related('developer_tasks')
    else:
        developers = User.objects.prefetch_related('developer_tasks')

    developer_data = []

    for developer in developers:
        # Get all tasks assigned to this developer
        tasks = Task.objects.filter(assigned_users=developer).select_related('job')

        # Calculate total money earned by completed tasks (progress = 100%)
        total_earned = tasks.filter(progress=100).aggregate(total=Sum('money_for_task'))['total'] or 0

        # Calculate total money paid to the developer
        total_paid = tasks.filter(paid=True).aggregate(total=Sum('money_for_task'))['total'] or 0

        # Calculate total deductions for the developer
        total_deductions = DeductionLog.objects.filter(developer=developer).aggregate(total=Sum('deduction_amount'))['total'] or 0

        # Calculate remaining balance
        balance = total_paid - total_deductions

        # Gather task details
        task_details = [{
            'job_title': task.job.title,
            'task_title': task.title,
            'money_for_task': task.money_for_task,
            'progress': task.progress,
            'paid': task.money_for_task if task.paid else 0,
        } for task in tasks]

        developer_data.append({
            'developer': developer,
            'total_earned': total_earned,
            'total_paid': total_paid,
            'total_deductions': total_deductions,
            'balance': balance,
            'tasks': task_details,
        })

    # Fetch all developers for the dropdown filter
    all_developers = User.objects.all()

    return render(request, 'developer_balance_sheet.html', {
        'developer_data': developer_data,
        'all_developers': all_developers,
        'selected_developer_id': int(developer_id) if developer_id else None,
    })


# Add this to views.py
@login_required
def delete_task(request, task_id):
    # Only admin can delete tasks
    if request.user.email != 'Admin@dbr.org':
        return HttpResponseForbidden("You are not authorized to delete tasks.")

    task = get_object_or_404(Task, id=task_id)
    job = task.job  # Get the associated job before deleting the task

    if request.method == 'POST':
        # Delete the task
        task.delete()

        # Recalculate percentages for remaining tasks in the job
        remaining_tasks = Task.objects.filter(job=job)
        total_hours = remaining_tasks.aggregate(Sum('hours'))['hours__sum'] or 0

        if total_hours > 0:  # Only recalculate if there are remaining tasks
            for remaining_task in remaining_tasks:
                remaining_task.task_percentage = (remaining_task.hours / total_hours) * 100
                remaining_task.save()

        messages.success(request, f"Task '{task.title}' has been successfully deleted.")

        # Redirect back to the job details page
        return redirect('job_details', job_id=job.id)

    # If it's a GET request, show confirmation page
    return render(request, 'delete_task_confirmation.html', {
        'task': task,
        'job': job
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.utils.safestring import mark_safe


def payment_load(request):
    job_id = request.session.get('client_job_id')
    if not job_id:
        return redirect('client_login')

    job = get_object_or_404(Job, id=job_id)
    tasks_data = get_tasks_data(job)

    # Make sure job is passed to the template
    context = {
        'job': job,
        'debug': True  # Enable debug mode
    }

    return render(request, 'payment_load.html', context)


@login_required
def update_progress(request):
    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        progress = request.POST.get('progress')

        try:
            # Convert progress to integer and validate range
            progress = int(progress)
            if not (0 <= progress <= 100):
                messages.error(request, "Progress must be between 0 and 100")
                return redirect('developer_tasks')

            # Get the task and verify the current user is assigned to it
            task = get_object_or_404(Task, id=task_id)
            if request.user not in task.assigned_users.all():
                return HttpResponseForbidden("You are not authorized to update this task.")

            # Update the progress
            task.progress = progress
            task.save()

            # Check if task is completed and handle payment if needed
            if progress == 100:
                task.check_and_pay_developer()

            messages.success(request, f"Progress for '{task.title}' updated to {progress}%")

        except ValueError:
            messages.error(request, "Invalid progress value")
        except Task.DoesNotExist:
            messages.error(request, "Task not found")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

    return redirect('developer_tasks')


# @login_required
# def delete_job(request, job_id):
#     # Only allow POST requests for deletion
#     if request.method == 'POST':
#         # Only allow admin to delete jobs
#         if request.user.email == 'Admin@dbr.org':
#             job = get_object_or_404(Job, id=job_id)
#             job_title = job.title
#             job.delete()
#             messages.success(request, f'Проект "{job_title}" успешно удален.')
#         else:
#             messages.error(request, 'У вас нет прав для удаления проектов.')
#
#     return redirect('job_list')



@login_required
def delete_job(request, job_id):
    # Only allow POST requests for deletion (for security)
    if request.method == 'POST':
        # Only allow admin to delete jobs
        if request.user.email == 'Admin@dbr.org':
            job = get_object_or_404(Job, id=job_id)
            job_title = job.title
            job.delete()
            messages.success(request, f'Project "{job_title}" has been successfully deleted.')
        else:
            messages.error(request, 'You do not have permission to delete projects.')

    # Redirect back to the job list page
    return redirect('job_list')

@login_required
def change_task_status(request, task_id):
    try:
        if request.method == 'POST':
            task = get_object_or_404(Task, id=task_id)

            # Toggle the task type
            if task.task_type == 'SIMPLE':
                task.task_type = 'MONTHLY'
                status_message = 'Задача изменена на ежемесячную'
            else:
                task.task_type = 'SIMPLE'
                status_message = 'Задача изменена на простую'

            task.save()
            messages.success(request, status_message)

            # Make sure we're returning to the correct job detail page
            return redirect('job_details', job_id=task.job.id)

    except Exception as e:
        messages.error(request, f'Произошла ошибка: {str(e)}')
        print(f"Error in change_task_status: {str(e)}")  # For debugging


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from .models import Task
from datetime import timedelta
from django.contrib.auth.decorators import login_required

from django.utils import timezone
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import Task
from datetime import timedelta

from django.contrib.auth.decorators import login_required

from django.utils import timezone
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import Task
from datetime import timedelta


@login_required
def all_developer_tasks(request):
    """
    View to show daily tasks for all developers with pagination and filtering.
    Uses summary data instead of loading all task details at once.
    """
    # Only allow admin to view all developer tasks
    if request.user.email != 'Admin@dbr.org':
        return HttpResponseForbidden("You are not authorized to view all developer tasks.")

    today = timezone.now().date()

    # Get selected filters
    selected_developer_id = request.GET.get('developer')
    selected_category = request.GET.get('category', 'today')  # Default to today's tasks

    # Get all developers
    developers = User.objects.annotate(
        task_count=Count('developer_tasks'),
        overdue_count=Count('developer_tasks',
                            filter=Q(developer_tasks__deadline__lt=today, developer_tasks__progress__lt=100)),
        today_count=Count('developer_tasks',
                          filter=Q(developer_tasks__deadline=today)),
        tomorrow_count=Count('developer_tasks',
                             filter=Q(developer_tasks__deadline=today + timedelta(days=1))),
        week_count=Count('developer_tasks',
                         filter=Q(
                             developer_tasks__deadline__gt=today + timedelta(days=1),
                             developer_tasks__deadline__lte=today + timedelta(days=7)
                         ))
    ).order_by('username')

    # Filter developers if needed
    if selected_developer_id:
        developers = developers.filter(id=selected_developer_id)

    # Paginate developers - show 5 per page
    developers_paginator = Paginator(developers, 5)
    developers_page = request.GET.get('page', 1)
    page_developers = developers_paginator.get_page(developers_page)

    # Get tasks for the selected category for visible developers only
    developer_tasks = {}

    for developer in page_developers:
        if selected_category == 'overdue':
            tasks = Task.objects.filter(
                assigned_users=developer,
                deadline__lt=today,
                progress__lt=100
            )
        elif selected_category == 'today':
            tasks = Task.objects.filter(
                assigned_users=developer,
                deadline=today
            )
        elif selected_category == 'tomorrow':
            tasks = Task.objects.filter(
                assigned_users=developer,
                deadline=today + timedelta(days=1)
            )
        elif selected_category == 'week':
            tasks = Task.objects.filter(
                assigned_users=developer,
                deadline__gt=today + timedelta(days=1),
                deadline__lte=today + timedelta(days=7)
            )
        else:
            # Default to all tasks
            tasks = Task.objects.filter(assigned_users=developer)

        # Select related data to reduce queries
        tasks = tasks.select_related('job').order_by('deadline')

        # Process tasks to add status information
        for task in tasks:
            if task.deadline:
                days_until_deadline = (task.deadline - today).days
                if days_until_deadline < 0:
                    task.status = 'overdue'
                    task.status_display = f'Overdue by {abs(days_until_deadline)} days'
                elif days_until_deadline == 0:
                    task.status = 'due_today'
                    task.status_display = 'Due today'
                elif days_until_deadline == 1:
                    task.status = 'due_tomorrow'
                    task.status_display = 'Due tomorrow'
                elif days_until_deadline <= 5:
                    task.status = 'task_red'
                    task.status_display = f'Due in {days_until_deadline} days'
                elif days_until_deadline <= 10:
                    task.status = 'task_yellow'
                    task.status_display = f'Due in {days_until_deadline} days'
                else:
                    task.status = 'task_green'
                    task.status_display = f'Due in {days_until_deadline} days'
            else:
                task.status = 'no_deadline'
                task.status_display = 'No deadline'

        developer_tasks[developer] = tasks

    context = {
        'today': today,
        'developers': page_developers,
        'developer_tasks': developer_tasks,
        'all_developers': developers,
        'selected_developer_id': selected_developer_id,
        'selected_category': selected_category,
        'active_page': 'all_developer_tasks',
    }

    return render(request, 'all_developer_tasks.html', context)


@login_required
def enhanced_tasks_view(request):
    """
    Enhanced view for tasks with date filtering capabilities.
    Allows viewing today's tasks, specific dates, this week, and future tasks.
    """
    # Only allow admin access
    if request.user.email != 'Admin@dbr.org':
        return HttpResponseForbidden("You are not authorized to view this page.")

    today = timezone.now().date()

    # Initialize date filtering variables
    filter_type = request.GET.get('filter_type', 'today')  # Default to today's tasks
    custom_date = request.GET.get('custom_date', None)

    # Date range for this week (from today to end of week)
    week_end = today + timedelta(days=(6 - today.weekday()))

    # Set the title and tasks based on filter type
    if filter_type == 'today':
        title = f"Today's Tasks ({today.strftime('%A, %B %d, %Y')})"
        tasks = Task.objects.filter(deadline=today)
    elif filter_type == 'tomorrow':
        tomorrow = today + timedelta(days=1)
        title = f"Tomorrow's Tasks ({tomorrow.strftime('%A, %B %d, %Y')})"
        tasks = Task.objects.filter(deadline=tomorrow)
    elif filter_type == 'week':
        title = f"This Week's Tasks ({today.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')})"
        tasks = Task.objects.filter(deadline__gte=today, deadline__lte=week_end)
    elif filter_type == 'future':
        next_week_start = week_end + timedelta(days=1)
        next_month_end = (today.replace(day=1) + timedelta(days=60)).replace(day=1) - timedelta(days=1)
        title = f"Future Tasks ({next_week_start.strftime('%b %d')} - {next_month_end.strftime('%b %d, %Y')})"
        tasks = Task.objects.filter(deadline__gt=week_end, deadline__lte=next_month_end)
    elif filter_type == 'custom' and custom_date:
        try:
            # Parse the custom date from the input
            parsed_date = datetime.strptime(custom_date, '%Y-%m-%d').date()
            title = f"Tasks for {parsed_date.strftime('%A, %B %d, %Y')}"
            tasks = Task.objects.filter(deadline=parsed_date)
        except ValueError:
            # If date parsing fails, default to today
            title = f"Today's Tasks ({today.strftime('%A, %B %d, %Y')})"
            tasks = Task.objects.filter(deadline=today)
            messages.error(request, "Invalid date format. Showing today's tasks instead.")
    else:
        # Default fallback
        title = f"Today's Tasks ({today.strftime('%A, %B %d, %Y')})"
        tasks = Task.objects.filter(deadline=today)

    # Get full task data with prefetching to minimize database hits
    tasks = tasks.select_related('job').prefetch_related('assigned_users').order_by('job__title', 'title')

    # Get stats for quick links
    today_count = Task.objects.filter(deadline=today).count()
    tomorrow_count = Task.objects.filter(deadline=today + timedelta(days=1)).count()
    week_count = Task.objects.filter(deadline__gte=today, deadline__lte=week_end).count()
    future_count = Task.objects.filter(deadline__gt=week_end).count()

    context = {
        'title': title,
        'tasks': tasks,
        'filter_type': filter_type,
        'custom_date': custom_date,
        'today': today,
        'today_count': today_count,
        'tomorrow_count': tomorrow_count,
        'week_count': week_count,
        'future_count': future_count,
        'active_page': 'enhanced_tasks',
    }

    return render(request, 'enhanced_tasks.html', context)


# Add this to your views.py file

@login_required
def change_task_status(request, task_id):
    try:
        if request.method == 'POST':
            task = get_object_or_404(Task, id=task_id)

            # Get the original task type to check if it's changing to PATPIS
            original_type = task.task_type

            # Toggle the task type
            if task.task_type == 'SIMPLE':
                task.task_type = 'MONTHLY'
                status_message = 'Задача изменена на ежемесячную'
            elif task.task_type == 'MONTHLY':
                task.task_type = 'PATPIS'
                status_message = 'Задача изменена на повторяющуюся (Follow Task)'
            else:
                task.task_type = 'SIMPLE'
                status_message = 'Задача изменена на простую'

            task.save()

            # If task was changed to PATPIS, create recurring tasks
            if original_type != 'PATPIS' and task.task_type == 'PATPIS':
                task.create_monthly_recurring_tasks()
                status_message += ' и созданы повторения на год'

            messages.success(request, status_message)

            # Make sure we're returning to the correct job detail page
            return redirect('job_details', job_id=task.job.id)

    except Exception as e:
        messages.error(request, f'Произошла ошибка: {str(e)}')
        print(f"Error in change_task_status: {str(e)}")  # For debugging
        return redirect('job_list')  # Fallback redirect


@login_required
def edit_task(request, task_id):
    """
    View for editing an existing task.
    Only admin users can edit tasks.
    """
    # Permission check
    if request.user.email != 'Admin@dbr.org':
        return HttpResponseForbidden("You are not authorized to edit tasks.")

    # Get the task instance
    task = get_object_or_404(Task, id=task_id)
    job = task.job  # Get the associated job

    if request.method == 'POST':
        # Create a form instance with the POST data
        form = TaskForm(request.POST, instance=task)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Get the original hours
                    original_hours = task.hours

                    # Save the form but don't commit yet
                    updated_task = form.save(commit=False)

                    # Check if hours have changed
                    if original_hours != updated_task.hours:
                        # Recalculate all task percentages for this job
                        all_job_tasks = Task.objects.filter(job=job)
                        total_hours = sum(t.hours for t in all_job_tasks if t.id != task.id) + updated_task.hours

                        # Update percentages
                        for job_task in all_job_tasks:
                            if job_task.id == task.id:
                                job_task.task_percentage = (updated_task.hours / total_hours) * 100
                            else:
                                job_task.task_percentage = (job_task.hours / total_hours) * 100
                            job_task.save()
                    else:
                        # If hours haven't changed, just save the task
                        updated_task.save()

                    # Save many-to-many relationships
                    form.save_m2m()

                    messages.success(request, f"Task '{task.title}' has been successfully updated.")
                    return redirect('job_details', job_id=job.id)
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
                import traceback
                traceback.print_exc()  # Print detailed error for debugging
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Create a form pre-populated with task data
        form = TaskForm(instance=task)

    return render(request, 'edit_task.html', {
        'form': form,
        'task': task,
        'job': job,
    })



@login_required
def job_statistics(request):
    # Get all jobs with their task statistics
    jobs_stats = []

    for job in Job.objects.all():
        # Get all tasks for this job
        tasks = job.tasks.all()

        # Count different types of tasks
        monthly_tasks = tasks.filter(task_type='MONTHLY').count()
        simple_tasks = tasks.filter(task_type='SIMPLE').count()
        overdue_tasks = tasks.filter(
            Q(deadline__lt=date.today()) &
            Q(progress__lt=100)
        ).count()

        # Calculate total tasks
        total_tasks = tasks.count()

        # Add to stats list
        jobs_stats.append({
            'job': job,
            'total_tasks': total_tasks,
            'monthly_tasks': monthly_tasks,
            'simple_tasks': simple_tasks,
            'overdue_tasks': overdue_tasks,
            'overall_progress': job.get_overall_progress()
        })

    context = {
        'jobs_stats': jobs_stats
    }

    return render(request, 'job_statistics.html', context)


# Add these imports at the top of views.py if not already imported
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

#
# @login_required
# def confirm_completed_task(request, task_id):
#     """
#     View to allow admin to confirm a completed task.
#     Only tasks with 100% progress can be confirmed.
#     Only admin users can confirm tasks.
#     """
#     # Permission check - only admin can confirm tasks
#     if request.user.email != 'Admin@dbr.org':
#         return HttpResponseForbidden("You are not authorized to confirm tasks.")
#
#     # Get the task instance
#     task = get_object_or_404(Task, id=task_id)
#
#     # Check if task is complete (progress = 100%)
#     if task.progress < 100:
#         messages.error(request, "Only completed tasks can be confirmed.")
#         return redirect('job_details', job_id=task.job.id)
#
#     # Handle confirmation
#     if request.method == 'POST':
#         action = request.POST.get('action')
#
#         if action == 'confirm':
#             # Confirm the task
#             task.confirmed = True
#             task.confirmation_date = timezone.now()
#             task.confirmed_by = request.user
#             task.save()
#
#             # Check if payment should be processed
#             task.check_and_pay_developer()
#
#             messages.success(request, f"Task '{task.title}' has been confirmed.")
#
#         elif action == 'unconfirm':
#             # Unconfirm the task if it's already confirmed
#             if task.confirmed:
#                 # If the task was already paid, we need to handle that
#                 if task.paid:
#                     task.paid = False
#                     # You might want to add additional logic for reversing payments
#
#                 task.confirmed = False
#                 task.confirmation_date = None
#                 task.confirmed_by = None
#                 task.save()
#
#                 messages.success(request, f"Task '{task.title}' confirmation has been revoked.")
#             else:
#                 messages.info(request, "This task was not previously confirmed.")
#
#     # Redirect back to job details page
#     return redirect('job_details', job_id=task.job.id)
#
#
# @login_required
# def tasks_pending_confirmation(request):
#     """
#     View to display all tasks with 100% progress for admin confirmation.
#     Handles both pending and already confirmed tasks.
#     """
#     # Permission check
#     if request.user.email != 'Admin@dbr.org':
#         return HttpResponseForbidden("You are not authorized to access this page.")
#
#     # Get filter parameter (pending or confirmed)
#     filter_param = request.GET.get('filter', 'pending')
#
#     # Build query based on filter
#     if filter_param == 'confirmed':
#         # Get confirmed tasks
#         tasks_query = Task.objects.filter(
#             progress=100,
#             confirmed=True
#         ).select_related('job', 'confirmed_by').prefetch_related('assigned_users')
#     else:
#         # Get pending tasks (default)
#         tasks_query = Task.objects.filter(
#             progress=100,
#             confirmed=False
#         ).select_related('job').prefetch_related('assigned_users')
#
#     # Get counts for summary data
#     pending_count = Task.objects.filter(progress=100, confirmed=False).count()
#     confirmed_count = Task.objects.filter(progress=100, confirmed=True).count()
#
#     # Calculate total payment value
#     from django.db.models import Sum
#     payment_total = tasks_query.aggregate(Sum('money_for_task'))['money_for_task__sum'] or 0
#
#     # Get count of tasks by job for quick reference
#     from django.db.models import Count
#     job_task_counts = tasks_query.values('job__title').annotate(
#         task_count=Count('id')
#     ).order_by('-task_count')
#
#     # Set up pagination
#     paginator = Paginator(tasks_query.order_by('-deadline', 'job__title'), 15)  # Show 15 tasks per page
#     page_number = request.GET.get('page')
#     page_tasks = paginator.get_page(page_number)
#
#     context = {
#         'tasks': page_tasks,
#         'filter': filter_param,
#         'pending_count': pending_count,
#         'confirmed_count': confirmed_count,
#         'payment_total': payment_total,
#         'job_task_counts': job_task_counts,
#         'active_page': 'tasks_confirmation',
#     }
#
#     return render(request, 'tasks_pending_confirmation.html', context)
#
#
# @login_required
# def bulk_confirm_tasks(request):
#     """
#     View to handle bulk confirmation of tasks
#     """
#     # Permission check
#     if request.user.email != 'Admin@dbr.org':
#         return HttpResponseForbidden("You are not authorized to perform this action.")
#
#     if request.method == 'POST':
#         # Get task IDs from the form
#         task_ids = request.POST.getlist('task_ids')
#
#         if not task_ids:
#             messages.error(request, "No tasks were selected.")
#             return redirect('tasks_pending_confirmation')
#
#         # Confirm all selected tasks
#         confirm_count = 0
#         for task_id in task_ids:
#             try:
#                 task = Task.objects.get(id=task_id, progress=100, confirmed=False)
#                 task.confirmed = True
#                 task.confirmation_date = timezone.now()
#                 task.confirmed_by = request.user
#                 task.save()
#
#                 # Check if payment should be processed
#                 task.check_and_pay_developer()
#
#                 confirm_count += 1
#             except Task.DoesNotExist:
#                 # Skip tasks that don't exist or don't meet criteria
#                 continue
#
#         messages.success(request, f"Successfully confirmed {confirm_count} tasks.")
#
#     return redirect('tasks_pending_confirmation')


# Оптимизация представлений для подтверждения задач

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q, F
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.db import transaction

from .models import Task, Job, DeductionLog


# Оптимизированное представление для подтверждения одной задачи
@login_required
@require_POST  # Ограничиваем только POST-запросами для безопасности
def confirm_completed_task(request, task_id):
    """
    Оптимизированное представление для подтверждения выполненной задачи.
    Используем транзакции и select_related для ускорения.
    """
    # Проверка прав доступа - только админ может подтверждать задачи
    if request.user.email != 'Admin@dbr.org':
        return HttpResponseForbidden("У вас нет прав для подтверждения задач.")

    # Получаем задачу с предварительной загрузкой связанных данных
    task = get_object_or_404(Task.objects.select_related('job'), id=task_id)

    # Проверяем, завершена ли задача (прогресс = 100%)
    if task.progress < 100:
        messages.error(request, "Только выполненные задачи могут быть подтверждены.")
        return redirect('job_details', job_id=task.job.id)

    # Получаем действие из формы
    action = request.POST.get('action')

    # Используем транзакцию для атомарности операций
    with transaction.atomic():
        if action == 'confirm':
            # Подтверждаем задачу
            task.confirmed = True
            task.confirmation_date = timezone.now()
            task.confirmed_by = request.user
            task.save(update_fields=['confirmed', 'confirmation_date', 'confirmed_by'])

            # Проверяем, должна ли быть произведена оплата
            task.check_and_pay_developer()

            messages.success(request, f"Задача '{task.title}' подтверждена.")

        elif action == 'unconfirm':
            # Отмена подтверждения задачи
            if task.confirmed:
                # Если задача уже была оплачена, обрабатываем это
                if task.paid:
                    task.paid = False
                    # Здесь можно добавить логику для отмены платежа

                task.confirmed = False
                task.confirmation_date = None
                task.confirmed_by = None
                task.save(update_fields=['confirmed', 'confirmation_date', 'confirmed_by', 'paid'])

                messages.success(request, f"Подтверждение задачи '{task.title}' отменено.")
            else:
                messages.info(request, "Эта задача ранее не была подтверждена.")

    # Проверяем, был ли запрос AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'action': action})

    # Перенаправляем обратно на страницу деталей проекта
    return redirect('job_details', job_id=task.job.id)


# Оптимизированное представление для страницы подтверждения задач
@login_required
def tasks_pending_confirmation(request):
    """
    Оптимизированное представление для отображения задач, требующих подтверждения.
    Используем кэширование и оптимизированные запросы.
    """
    # Проверка прав доступа
    if request.user.email != 'Admin@dbr.org':
        return HttpResponseForbidden("У вас нет прав для доступа к этой странице.")

    # Получаем фильтр (ожидающие или подтвержденные)
    filter_param = request.GET.get('filter', 'pending')

    # Оптимизированный запрос с select_related и prefetch_related
    if filter_param == 'confirmed':
        # Получаем подтвержденные задачи
        tasks_query = Task.objects.filter(
            progress=100,
            confirmed=True
        ).select_related('job', 'confirmed_by').prefetch_related('assigned_users')
    else:
        # Получаем ожидающие задачи (по умолчанию)
        tasks_query = Task.objects.filter(
            progress=100,
            confirmed=False
        ).select_related('job').prefetch_related('assigned_users')

    # Оптимизация: выполняем агрегационные запросы за один раз
    from django.db.models import Count, Sum

    stats = Task.objects.filter(progress=100).aggregate(
        pending_count=Count('id', filter=Q(confirmed=False)),
        confirmed_count=Count('id', filter=Q(confirmed=True)),
        payment_total=Sum('money_for_task', filter=Q(progress=100))
    )

    pending_count = stats['pending_count']
    confirmed_count = stats['confirmed_count']
    payment_total = stats['payment_total'] or 0

    # Получаем аналитику по проектам с оптимизацией запроса
    job_task_counts = (
        Task.objects.filter(
            progress=100
        ).values('job__id', 'job__title')
        .annotate(
            task_count=Count('id', filter=Q(confirmed=False)),
            confirmed_count=Count('id', filter=Q(confirmed=True)),
            payment_total=Sum('money_for_task')
        )
        .order_by('-task_count')
    )

    # Оптимизация пагинации - ограничиваем количество запросов
    paginator = Paginator(tasks_query.order_by('-deadline', 'job__title'), 15)
    page_number = request.GET.get('page', 1)

    # Устанавливаем orphans для предотвращения страниц с малым количеством элементов
    paginator.orphans = 3

    # Получаем только текущую страницу без лишних запросов
    page_tasks = paginator.get_page(page_number)

    context = {
        'tasks': page_tasks,
        'filter': filter_param,
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'payment_total': payment_total,
        'job_task_counts': job_task_counts,
        'active_page': 'tasks_confirmation',
    }

    return render(request, 'tasks_pending_confirmation.html', context)


# Оптимизированное представление для массового подтверждения задач
@login_required
@require_POST
@transaction.atomic  # Оборачиваем всю функцию в транзакцию для атомарности
def bulk_confirm_tasks(request):
    """
    Оптимизированное представление для массового подтверждения задач.
    Используем транзакции и пакетное обновление.
    """
    # Проверка прав доступа
    if request.user.email != 'Admin@dbr.org':
        return HttpResponseForbidden("У вас нет прав для выполнения этого действия.")

    # Получаем ID задач из формы
    task_ids = request.POST.getlist('task_ids')

    if not task_ids:
        messages.error(request, "Не выбрано ни одной задачи.")
        return redirect('tasks_pending_confirmation')

    # Получаем текущее время для всех задач
    now_time = timezone.now()

    # Выбираем только задачи, которые соответствуют критериям
    tasks_to_confirm = Task.objects.filter(
        id__in=task_ids,
        progress=100,
        confirmed=False
    )

    confirm_count = tasks_to_confirm.count()

    if confirm_count > 0:
        # Массовое обновление всех задач за один запрос
        tasks_to_confirm.update(
            confirmed=True,
            confirmation_date=now_time,
            confirmed_by=request.user
        )

        # Получаем обновленные задачи и обрабатываем оплату
        for task in tasks_to_confirm:
            task.check_and_pay_developer()

        messages.success(request, f"Успешно подтверждено {confirm_count} задач.")
    else:
        messages.warning(request, "Не найдено задач для подтверждения.")

    # Проверяем, был ли запрос AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'count': confirm_count,
            'redirect': request.META.get('HTTP_REFERER', '/tasks/pending-confirmation/')
        })

    return redirect('tasks_pending_confirmation')


# Add to views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, F
from django.db import transaction


@login_required
def client_task_confirmation(request):
    """
    View for client to see tasks that need confirmation.
    Only shows tasks that have been confirmed by admin already.
    """
    # Get the job_id from the session
    job_id = request.session.get('client_job_id')
    if not job_id:
        return redirect('client_login')

    # Get the job
    job = get_object_or_404(Job, id=job_id)

    # Filter parameter (pending or confirmed)
    filter_param = request.GET.get('filter', 'pending')

    if filter_param == 'confirmed':
        # Get tasks confirmed by client
        tasks = Task.objects.filter(
            job=job,
            confirmed=True,  # Admin confirmed
            client_confirmed=True  # Client confirmed
        ).order_by('-client_confirmation_date')
    elif filter_param == 'all':
        # Get all completed tasks
        tasks = Task.objects.filter(
            job=job,
            progress=100
        ).order_by('-deadline')
    else:
        # Get tasks pending client confirmation (default)
        tasks = Task.objects.filter(
            job=job,
            confirmed=True,  # Admin confirmed
            client_confirmed=False  # Not client confirmed yet
        ).order_by('deadline')

    # Count statistics
    pending_count = Task.objects.filter(job=job, confirmed=True, client_confirmed=False).count()
    confirmed_count = Task.objects.filter(job=job, client_confirmed=True).count()
    completed_count = Task.objects.filter(job=job, progress=100).count()

    # Paginate results
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page', 1)
    page_tasks = paginator.get_page(page_number)

    context = {
        'job': job,
        'tasks': page_tasks,
        'filter': filter_param,
        'pending_count': pending_count,
        'confirmed_count': confirmed_count,
        'completed_count': completed_count
    }

    return render(request, 'client_task_confirmation.html', context)


@login_required
@require_POST
def confirm_task_by_client(request, task_id):
    """
    Handle client confirmation for a specific task
    """
    # Get job_id from session to verify client access
    job_id = request.session.get('client_job_id')
    if not job_id:
        return redirect('client_login')

    # Get the task and verify it belongs to client's job
    task = get_object_or_404(Task, id=task_id, job_id=job_id)

    # Verify the task is ready for client confirmation
    if not task.confirmed:
        messages.error(request, "Эта задача еще не подтверждена администратором.")
        return redirect('client_task_confirmation')

    # Get client action and comment
    action = request.POST.get('action')
    comment = request.POST.get('comment', '')

    # Use transaction for atomicity
    with transaction.atomic():
        if action == 'confirm':
            # Client confirms the task
            task.client_confirmed = True
            task.client_confirmation_date = timezone.now()
            task.client_comment = comment  # Store comment in English
            task.status = 'client_confirmed'
            task.save(update_fields=[
                'client_confirmed', 'client_confirmation_date',
                'client_comment', 'status'
            ])

            # Check if payment should be processed
            task.check_and_pay_developer()

            messages.success(request, "Задача успешно подтверждена.")

        elif action == 'reject':
            # Client rejects the task
            task.client_confirmed = False
            task.status = 'rejected'
            task.client_comment = comment  # Store rejection reason in English
            task.save(update_fields=['client_confirmed', 'status', 'client_comment'])

            messages.info(request, "Задача отклонена и отправлена обратно на доработку.")

    return redirect('client_task_confirmation')


@login_required
@require_POST
def bulk_confirm_client_tasks(request):
    """
    Handle bulk confirmation by client
    """
    # Verify client access
    job_id = request.session.get('client_job_id')
    if not job_id:
        return redirect('client_login')

    # Get selected task IDs
    task_ids = request.POST.getlist('task_ids')
    comment = request.POST.get('bulk_comment', '')

    if not task_ids:
        messages.error(request, "Вы не выбрали задачи для подтверждения.")
        return redirect('client_task_confirmation')

    # Get tasks that belong to client's job and are ready for confirmation
    tasks = Task.objects.filter(
        id__in=task_ids,
        job_id=job_id,
        confirmed=True,
        client_confirmed=False
    )

    # Confirm all selected tasks
    confirm_count = 0
    with transaction.atomic():
        for task in tasks:
            task.client_confirmed = True
            task.client_confirmation_date = timezone.now()
            task.client_comment = comment  # Same comment for all tasks
            task.status = 'client_confirmed'
            task.save(update_fields=[
                'client_confirmed', 'client_confirmation_date',
                'client_comment', 'status'
            ])

            # Check payment eligibility
            task.check_and_pay_developer()

            confirm_count += 1

    if confirm_count > 0:
        messages.success(request, f"Успешно подтверждено {confirm_count} задач.")
    else:
        messages.warning(request, "Не найдено задач для подтверждения.")

    return redirect('client_task_confirmation')



from datetime import timezone
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
from .models import Job, Task, DeductionLog, calculate_income_balance
from .forms import JobForm, TaskFormSet, ClientLoginForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Job
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
    if request.user.email != 'admin_tmk@gmail.com':
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



# def create_tasks(request, job_id):
#     job = get_object_or_404(Job, id=job_id)
#
#     if request.method == 'POST':
#         task_formset = TaskFormSet(request.POST, instance=job)
#
#         if task_formset.is_valid():
#             # Calculate total hours for all tasks
#             total_hours = sum([form.cleaned_data['hours'] for form in task_formset if form.cleaned_data.get('hours')])
#
#             # Iterate over the formset and calculate the percentage for each task
#             for form in task_formset:
#                 task = form.save(commit=False)
#                 task.task_percentage = (form.cleaned_data['hours'] / total_hours) * 100
#                 task.save()
#                 form.save_m2m()  # Save ManyToMany relationships, such as assigned users
#
#             return redirect('job_list')  # Redirect to job list after saving tasks
#     else:
#         task_formset = TaskFormSet(instance=job)
#
#     return render(request, 'create_tasks.html', {
#         'task_formset': task_formset,
#         'job': job,
#     })


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

def client_progress(request):
    job_id = request.session.get('client_job_id')
    if not job_id:
        return redirect('client_login')

    job = get_object_or_404(Job, id=job_id)
    tasks_data = get_tasks_data(job)

    context = {
        'job': job,
        'tasks': mark_safe(json.dumps(tasks_data)) 
    }
    return render(request, 'client_progress.html', context)

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


# @login_required
# def developer_tasks(request):
#     developer = request.user  # Assuming each developer is logged in
#     tasks = Task.objects.filter(assigned_users=developer)
#     balance = sum(task.money_for_task for task in tasks if task.paid)
#     deduction_logs = DeductionLog.objects.filter(developer=developer).order_by('-deduction_date')
#
#     if request.method == 'POST':
#         task_id = request.POST.get('task_id')
#         progress = request.POST.get('progress')
#
#         # Ensure you are fetching the correct task assigned to the developer
#         task = get_object_or_404(Task, id=task_id, assigned_users=developer)
#
#         # Update progress only if valid
#         if progress is not None:
#             task.progress = int(progress)
#             task.save()
#
#             # Check if the developer has completed the task (progress = 100%) and handle payment if needed
#             if task.progress == 100:
#                 task.check_and_pay_developer()  # Optional logic for payment
#
#         return redirect('developer_tasks')
#
#     return render(request, 'developer_tasks.html', {
#         'developer': developer,
#         'tasks': tasks,
#         'balance': balance,
#         'deduction_logs': deduction_logs
#     })

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
    developer = request.user

    # Sort tasks by deadline in ascending order and paginate for main task list
    tasks = Task.objects.filter(assigned_users=developer).order_by('deadline')
    paginator = Paginator(tasks, 15)  # Main task list pagination
    page_number = request.GET.get('page')
    page_tasks = paginator.get_page(page_number)

    # Pagination for Feedback Tasks
    feedback_paginator = Paginator(tasks, 10)  # Paginate feedback section, 3 tasks per page
    feedback_page_number = request.GET.get('feedback_page')
    feedback_page_tasks = feedback_paginator.get_page(feedback_page_number)

    balance = sum(task.money_for_task for task in tasks if task.paid)
    deduction_logs = DeductionLog.objects.filter(developer=developer).order_by('-deduction_date')

    if request.method == 'POST':
        task_id = request.POST.get('task_id')
        progress = request.POST.get('progress')
        task = get_object_or_404(Task, id=task_id, assigned_users=developer)

        if progress is not None:
            task.progress = int(progress)
            task.save()

            if task.progress == 100:
                task.check_and_pay_developer()

        return redirect('developer_tasks')

    return render(request, 'developer_tasks.html', {
        'developer': developer,
        'tasks': page_tasks,
        'feedback_tasks': feedback_page_tasks,  # Pass paginated feedback tasks to the template
        'balance': balance,
        'deduction_logs': deduction_logs
    })

@login_required
def payment_history(request):
    developer = request.user
    deduction_logs = DeductionLog.objects.filter(developer=developer).order_by('-deduction_date')

    return render(request, 'payment_history.html', {
        'developer': developer,
        'deduction_logs': deduction_logs
    })

# def admin_dashboard(request):
#     # Get all developers
#     developers = User.objects.all()
#     developer_data = []
#
#     # Loop through each developer to gather task data
#     for developer in developers:
#         assigned_tasks = Task.objects.filter(assigned_users=developer)
#
#         # Count task statuses for all tasks assigned to the developer
#         status_counter = Counter({'task_green': 0, 'task_yellow': 0, 'task_red': 0, 'overdue': 0})
#
#         for task in assigned_tasks:
#             days_until_deadline = None
#             if task.deadline:
#                 days_until_deadline = (task.deadline - timezone.now().date()).days
#
#             # Determine task color based on deadline or completion
#             task_color = None
#             if task.progress == 100:
#                 task_color = 'done'
#             elif days_until_deadline is not None:
#                 if days_until_deadline > 10:
#                     task_color = 'task_green'
#                 elif 5 < days_until_deadline <= 10:
#                     task_color = 'task_yellow'
#                 elif 0 <= days_until_deadline <= 5:
#                     task_color = 'task_red'
#                 else:
#                     task_color = 'overdue'
#
#             if task_color and task_color != 'done':  # Only count tasks that aren't marked as 'done'
#                 status_counter[task_color] += 1
#
#         # Paginate tasks for each developer (5 tasks per page for each developer)
#         task_paginator = Paginator(assigned_tasks, 5)
#         page_number = request.GET.get(f'page_{developer.id}', 1)
#         page_obj = task_paginator.get_page(page_number)
#
#         # Create task info including days until deadline
#         task_info = [{
#             'task': task,
#             'days_until_deadline': (task.deadline - timezone.now().date()).days if task.deadline else None
#         } for task in page_obj]
#
#         # Calculate the balance based on paid tasks
#         balance = sum(task.money_for_task for task in assigned_tasks if task.paid)
#
#         developer_data.append({
#             'developer': developer,
#             'tasks': task_info,
#             'balance': balance,
#             'paginator': task_paginator,
#             'page_obj': page_obj,
#             'status_counts': status_counter,  # Pass the full task status count
#         })
#
#     # Paginate the list of developers (5 developers per page)
#     developers_paginator = Paginator(developer_data, 2)
#     developers_page_number = request.GET.get('developer_page', 1)
#     developers_page_obj = developers_paginator.get_page(developers_page_number)
#
#     # Unassigned tasks and all deduction logs
#     unassigned_tasks = Task.objects.filter(assigned_users=None)
#     all_deduction_logs = DeductionLog.objects.select_related('developer', 'deducted_by').all()
#
#     context = {
#         'developer_data': developers_page_obj,  # Pass paginated developer data
#         'unassigned_tasks': unassigned_tasks,
#         'all_deduction_logs': all_deduction_logs,
#     }
#
#     return render(request, 'admin_dashboard.html', context)
#

from collections import Counter
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils import timezone
from .models import User, Task, DeductionLog
#
# def admin_dashboard(request):
#     # Get all developers
#     developers = User.objects.all()
#     developer_data = []
#
#     # Loop through each developer to gather task data
#     for developer in developers:
#         assigned_tasks = Task.objects.filter(assigned_users=developer)
#         status_counter = Counter({'task_green': 0, 'task_yellow': 0, 'task_red': 0, 'overdue': 0})
#
#         # Prepare task info with color coding and deadline calculation
#         task_info = []
#         for task in assigned_tasks:
#             days_until_deadline = (task.deadline - timezone.now().date()).days if task.deadline else None
#             task_color = 'done' if task.progress == 100 else None
#
#             # Set task color based on deadline and progress
#             if task_color is None and days_until_deadline is not None:
#                 if days_until_deadline > 10:
#                     task_color = 'task_green'
#                 elif 5 < days_until_deadline <= 10:
#                     task_color = 'task_yellow'
#                 elif 0 <= days_until_deadline <= 5:
#                     task_color = 'task_red'
#                 else:
#                     task_color = 'overdue'
#
#             # Add non-done tasks to the status counter
#             if task_color and task_color != 'done':
#                 status_counter[task_color] += 1
#
#             task_info.append({
#                 'task': task,
#                 'days_until_deadline': days_until_deadline,
#                 'color': task_color  # Pass color for easier frontend rendering
#             })
#
#         # Paginate tasks per developer (5 tasks per page)
#         task_paginator = Paginator(task_info, 5)
#         page_number = request.GET.get(f'page_{developer.id}', 1)
#         page_obj = task_paginator.get_page(page_number)
#
#         # Calculate balance based on paid tasks
#         balance = sum(task.money_for_task for task in assigned_tasks if task.paid)
#
#         developer_data.append({
#             'developer': developer,
#             'tasks': page_obj,
#             'balance': balance,
#             'status_counts': status_counter,
#         })
#
#     # Paginate developers (5 developers per page)
#     developers_paginator = Paginator(developer_data, 10)
#     developers_page_number = request.GET.get('developer_page', 1)
#     developers_page_obj = developers_paginator.get_page(developers_page_number)
#
#     # Fetch unassigned tasks and deduction logs
#     unassigned_tasks = Task.objects.filter(assigned_users=None)
#     all_deduction_logs = DeductionLog.objects.select_related('developer', 'deducted_by').all()
#
#     context = {
#         'developer_data': developers_page_obj,
#         'unassigned_tasks': unassigned_tasks,
#         'all_deduction_logs': all_deduction_logs,
#     }
#
#     return render(request, 'admin_dashboard.html', context)
#




from django.db.models import Count
#
# def admin_dashboard(request):
#     # Fetch all jobs and developers
#     jobs = Job.objects.all()
#     developers = User.objects.prefetch_related('developer_tasks')
#
#     # Calculate total jobs and total income
#     total_jobs = jobs.count()
#     total_income = jobs.aggregate(total_income=Sum('over_all_income'))['total_income'] or 0
#
#     # Calculate total remaining income
#     total_remaining_income = calculate_income_balance()["income_balance"]
#
#     # Calculate the count of all overdue tasks
#     overdue_task_count = Task.objects.filter(
#         progress__lt=100,  # Tasks not completed
#         deadline__lt=now().date()  # Deadline in the past
#     ).count()
#
#     # Developer task data and pagination
#     developer_data = []
#     for developer in developers:
#         assigned_tasks = Task.objects.filter(assigned_users=developer).select_related('job')
#
#         # Categorize tasks by status
#         status_counter = Counter({'task_green': 0, 'task_yellow': 0, 'task_red': 0, 'overdue': 0, 'done': 0})
#         task_info = []
#         for task in assigned_tasks:
#             days_until_deadline = None
#             if task.deadline:
#                 days_until_deadline = (task.deadline - now().date()).days
#
#             task_color = None
#             if task.progress == 100:
#                 task_color = 'done'
#                 status_counter['done'] += 1
#             elif days_until_deadline is not None:
#                 if days_until_deadline > 10:
#                     task_color = 'task_green'
#                     status_counter['task_green'] += 1
#                 elif 5 < days_until_deadline <= 10:
#                     task_color = 'task_yellow'
#                     status_counter['task_yellow'] += 1
#                 elif 0 <= days_until_deadline <= 5:
#                     task_color = 'task_red'
#                     status_counter['task_red'] += 1
#                 else:
#                     task_color = 'overdue'
#                     status_counter['overdue'] += 1
#
#             task_info.append({
#                 'task': task,
#                 'days_until_deadline': days_until_deadline,
#                 'color': task_color
#             })
#
#         task_paginator = Paginator(task_info, 5)
#         page_number = request.GET.get(f'page_{developer.id}', 1)
#         page_obj = task_paginator.get_page(page_number)
#
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
#     developers_paginator = Paginator(developer_data, 10)
#     developers_page_number = request.GET.get('developer_page', 1)
#     developers_page_obj = developers_paginator.get_page(developers_page_number)
#
#     unassigned_tasks = Task.objects.filter(assigned_users=None)
#     all_deduction_logs = DeductionLog.objects.select_related('developer', 'deducted_by').all()
#
#     context = {
#         'total_jobs': total_jobs,
#         'total_income': total_income,
#         'in_time_processes_money': total_remaining_income,
#         'overdue_task_count': overdue_task_count,  # Add overdue task count
#         'developer_data': developers_page_obj,
#         'unassigned_tasks': unassigned_tasks,
#         'all_deduction_logs': all_deduction_logs,
#     }
#
#     return render(request, 'admin_dashboard.html', context)

from django.db.models import Sum
from django.utils.timezone import now


from django.utils.timezone import now

@login_required
def admin_dashboard(request):
    jobs = Job.objects.all()
    total_jobs = jobs.count()
    total_income = jobs.aggregate(total_income=Sum('over_all_income'))['total_income'] or 0
    total_remaining_income = calculate_income_balance()["income_balance"]

    # Overdue task count
    overdue_task_count = Task.objects.filter(
        progress__lt=100,
        deadline__lt=now().date()
    ).count()

    # Calculate monthly income (jobs created this month)
    current_month = now().month
    current_year = now().year
    monthly_income = Job.objects.filter(
        created_at__year=current_year,
        created_at__month=current_month
    ).aggregate(monthly_total=Sum('over_all_income'))['monthly_total'] or 0

    developers = User.objects.prefetch_related('developer_tasks')
    developer_data = []
    for developer in developers:
        assigned_tasks = Task.objects.filter(assigned_users=developer).select_related('job')
        status_counter = Counter({'task_green': 0, 'task_yellow': 0, 'task_red': 0, 'overdue': 0, 'done': 0})
        task_info = []

        for task in assigned_tasks:
            days_until_deadline = (task.deadline - now().date()).days if task.deadline else None
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

        task_paginator = Paginator(task_info, 5)
        page_number = request.GET.get(f'page_{developer.id}', 1)
        page_obj = task_paginator.get_page(page_number)

        balance = assigned_tasks.filter(paid=True).aggregate(
            total_balance=Sum('money_for_task')
        )['total_balance'] or 0

        developer_data.append({
            'developer': developer,
            'tasks': page_obj,
            'balance': balance,
            'status_counts': status_counter,
        })

    developers_paginator = Paginator(developer_data, 10)
    developers_page_number = request.GET.get('developer_page', 1)
    developers_page_obj = developers_paginator.get_page(developers_page_number)

    unassigned_tasks = Task.objects.filter(assigned_users=None)
    all_deduction_logs = DeductionLog.objects.select_related('developer', 'deducted_by').all()

    context = {
        'total_jobs': total_jobs,
        'total_income': total_income,
        'in_time_processes_money': total_remaining_income,
        'overdue_task_count': overdue_task_count,
        'monthly_income': monthly_income,
        'developer_data': developers_page_obj,
        'unassigned_tasks': unassigned_tasks,
        'all_deduction_logs': all_deduction_logs,
    }
    return render(request, 'admin_dashboard.html', context)

from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from .models import Job, Task
from django.db.models import Max, Sum

def job_details(request, job_id):
    # Fetch the specific job or return a 404 error if not found
    job = get_object_or_404(Job, id=job_id)

    # Retrieve all tasks associated with this job
    tasks = Task.objects.filter(job=job)

    # Set up pagination for tasks (10 tasks per page)
    paginator = Paginator(tasks, 10)  # Show 10 tasks per page
    page_number = request.GET.get('page')
    page_tasks = paginator.get_page(page_number)

    # Calculate the latest deadline across all tasks if tasks are available
    latest_deadline = tasks.aggregate(Max('deadline'))['deadline__max'] if tasks else None

    # Get the overall progress of the job
    overall_progress = job.get_overall_progress() if job.get_overall_progress() else 0 




    # Calculate the total payment for all tasks
    total_task_payment = tasks.aggregate(Sum('money_for_task'))['money_for_task__sum'] or 0

    # Calculate the remaining income
    remaining_income = job.over_all_income - total_task_payment

    return render(request, 'job_details.html', {
        'job': job,
        'tasks': page_tasks,  # Pass the paginated tasks
        'latest_deadline': latest_deadline,
        'overall_progress': overall_progress,
        'total_task_payment': total_task_payment,
        'remaining_income': remaining_income,
    })

from django.shortcuts import render
from .models import DeductionLog


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

def add_task_to_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    TaskFormSet = inlineformset_factory(
        Job, Task,
        form=TaskForm,
        extra=1,
        can_delete=False
    )

    task_formset = TaskFormSet(request.POST or None, instance=job)

    if request.method == 'POST':
        if task_formset.is_valid():
            # Calculate total hours for all tasks related to the job
            existing_tasks = Task.objects.filter(job=job)
            existing_hours = existing_tasks.aggregate(total_hours=Sum('hours'))['total_hours'] or 0

            # Calculate total hours from the submitted formset
            formset_hours = 0
            for form in task_formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    hours = form.cleaned_data.get('hours', 0)
                    formset_hours += hours

            total_hours = existing_hours + formset_hours

            if total_hours == 0:
                messages.error(request, "Total hours cannot be zero.")
                return render(request, 'add_task_to_job.html', {
                    'task_formset': task_formset,
                    'job': job,
                })

            with transaction.atomic():
                # Save each form in the formset
                for form in task_formset:
                    if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                        task = form.save(commit=False)
                        hours = form.cleaned_data.get('hours', 0)
                        # Calculate task percentage based on total hours
                        task.task_percentage = (hours / total_hours) * 100
                        task.job = job  # Associate the task with the job
                        task.save()
                        form.save_m2m()  # Save many-to-many relationships

                # Update task percentages for existing tasks
                for task in existing_tasks:
                    task.task_percentage = (task.hours / total_hours) * 100
                    task.save()

                logger.info(f"Tasks successfully added to job: {job.title}")
                return redirect('job_list')
        else:
            logger.error("Formset validation failed.")
            logger.error(f"Formset errors: {task_formset.errors}")
            logger.error(f"Non-form errors: {task_formset.non_form_errors()}")
            for form in task_formset:
                logger.error(f"Form errors: {form.errors}")

    return render(request, 'add_task_to_job.html', {
        'task_formset': task_formset,
        'job': job,
    })




#
#
#
# def developer_payment_sheet(request):
#     developers = User.objects.prefetch_related('developer_tasks')
#
#     developer_data = []
#
#     for developer in developers:
#         # Get all tasks assigned to this developer
#         tasks = Task.objects.filter(assigned_users=developer).select_related('job')
#
#         # Calculate total money earned by completed tasks (progress = 100%)
#         total_earned = tasks.filter(progress=100).aggregate(total=Sum('money_for_task'))['total'] or 0
#
#         # Calculate total money paid to the developer
#         total_paid = tasks.filter(paid=True).aggregate(total=Sum('money_for_task'))['total'] or 0
#
#         # Calculate total deductions for the developer
#         total_deductions = DeductionLog.objects.filter(developer=developer).aggregate(total=Sum('deduction_amount'))['total'] or 0
#
#         # Calculate remaining balance
#         balance = total_paid - total_deductions
#
#         # Gather task details
#         task_details = [{
#             'job_title': task.job.title,
#             'task_title': task.title,
#             'money_for_task': task.money_for_task,
#             'progress': task.progress,
#             'paid': task.money_for_task if task.paid else 0,  # Show the amount paid if `paid=True`
#         } for task in tasks]
#
#         developer_data.append({
#             'developer': developer,
#             'total_earned': total_earned,
#             'total_paid': total_paid,
#             'total_deductions': total_deductions,
#             'balance': balance,
#             'tasks': task_details,
#         })
#
#     return render(request, 'developer_balance_sheet.html', {'developer_data': developer_data})


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

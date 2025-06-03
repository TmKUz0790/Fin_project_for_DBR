from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum
from django.utils.dateparse import parse_date
import json
from datetime import datetime

from .models import Task, Job


def api_response(data=None, message="Success", status_code=200, error=None):
    """
    Standardized API response format
    """
    response_data = {
        'success': status_code < 400,
        'message': message,
        'data': data,
        'error': error
    }
    return JsonResponse(response_data, status=status_code)


@csrf_exempt
@require_http_methods(["GET"])
def api_get_all_tasks(request, job_id):
    """
    GET /api/jobs/{job_id}/tasks/
    Get all tasks for a specific job
    """
    try:
        # Verify job exists
        job = get_object_or_404(Job, id=job_id)

        # Get all tasks for this job
        tasks = Task.objects.filter(job=job).select_related('job').prefetch_related('assigned_users')

        # Serialize tasks data
        tasks_data = []
        for task in tasks:
            # Get assigned users
            assigned_users = [
                {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
                for user in task.assigned_users.all()
            ]

            task_data = {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'hours': task.hours,
                'task_percentage': task.task_percentage,
                'progress': task.progress,
                'money_for_task': task.money_for_task,
                'paid': task.paid,
                'task_type': task.task_type,
                'confirmed': task.confirmed,
                'start_date': task.start_date.isoformat() if task.start_date else None,
                'deadline': task.deadline.isoformat() if task.deadline else None,
                'confirmation_date': task.confirmation_date.isoformat() if task.confirmation_date else None,
                'confirmed_by': task.confirmed_by.username if task.confirmed_by else None,
                'feedback': task.feedback,
                'assigned_users': assigned_users,
                'job': {
                    'id': job.id,
                    'title': job.title
                }
            }
            tasks_data.append(task_data)

        return api_response(
            data={
                'job': {
                    'id': job.id,
                    'title': job.title,
                    'client_email': job.client_email,
                    'over_all_income': job.over_all_income
                },
                'tasks': tasks_data,
                'total_tasks': len(tasks_data)
            },
            message=f"Retrieved {len(tasks_data)} tasks for job '{job.title}'"
        )

    except Job.DoesNotExist:
        return api_response(
            error="Job not found",
            message="The specified job does not exist",
            status_code=404
        )
    except Exception as e:
        return api_response(
            error=str(e),
            message="An error occurred while retrieving tasks",
            status_code=500
        )


@csrf_exempt
@require_http_methods(["GET"])
def api_get_task_detail(request, job_id, task_id):
    """
    GET /api/jobs/{job_id}/tasks/{task_id}/
    Get details of a specific task
    """
    try:
        # Verify job and task exist and are related
        job = get_object_or_404(Job, id=job_id)
        task = get_object_or_404(Task, id=task_id, job=job)

        # Get assigned users
        assigned_users = [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
            for user in task.assigned_users.all()
        ]

        task_data = {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'hours': task.hours,
            'task_percentage': task.task_percentage,
            'progress': task.progress,
            'money_for_task': task.money_for_task,
            'paid': task.paid,
            'task_type': task.task_type,
            'confirmed': task.confirmed,
            'start_date': task.start_date.isoformat() if task.start_date else None,
            'deadline': task.deadline.isoformat() if task.deadline else None,
            'confirmation_date': task.confirmation_date.isoformat() if task.confirmation_date else None,
            'confirmed_by': task.confirmed_by.username if task.confirmed_by else None,
            'feedback': task.feedback,
            'assigned_users': assigned_users,
            'job': {
                'id': job.id,
                'title': job.title,
                'client_email': job.client_email,
                'over_all_income': job.over_all_income
            }
        }

        return api_response(
            data=task_data,
            message=f"Retrieved task '{task.title}'"
        )

    except (Job.DoesNotExist, Task.DoesNotExist):
        return api_response(
            error="Task or Job not found",
            message="The specified task or job does not exist",
            status_code=404
        )
    except Exception as e:
        return api_response(
            error=str(e),
            message="An error occurred while retrieving task details",
            status_code=500
        )


@csrf_exempt
@require_http_methods(["POST"])
def api_create_task(request, job_id):
    """
    POST /api/jobs/{job_id}/tasks/
    Create a new task for a specific job

    Required fields:
    - title: string
    - description: string
    - hours: integer
    - money_for_task: integer

    Optional fields:
    - task_type: string (SIMPLE, PATPIS, MONTHLY) - default: SIMPLE
    - deadline: string (YYYY-MM-DD format)
    - assigned_user_ids: array of user IDs
    - progress: integer (0-100) - default: 0
    """
    try:
        # Verify job exists
        job = get_object_or_404(Job, id=job_id)

        # Parse JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return api_response(
                error="Invalid JSON",
                message="Request body must be valid JSON",
                status_code=400
            )

        # Validate required fields
        required_fields = ['title', 'description', 'hours', 'money_for_task']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]

        if missing_fields:
            return api_response(
                error="Missing required fields",
                message=f"Missing required fields: {', '.join(missing_fields)}",
                status_code=400
            )

        # Validate data types
        try:
            hours = int(data['hours'])
            money_for_task = int(data['money_for_task'])
            progress = int(data.get('progress', 0))

            if hours <= 0:
                return api_response(
                    error="Invalid hours",
                    message="Hours must be greater than 0",
                    status_code=400
                )

            if money_for_task < 0:
                return api_response(
                    error="Invalid money_for_task",
                    message="Money for task must be 0 or greater",
                    status_code=400
                )

            if not (0 <= progress <= 100):
                return api_response(
                    error="Invalid progress",
                    message="Progress must be between 0 and 100",
                    status_code=400
                )

        except ValueError:
            return api_response(
                error="Invalid data types",
                message="Hours, money_for_task, and progress must be integers",
                status_code=400
            )

        # Validate task_type
        task_type = data.get('task_type', 'SIMPLE')
        valid_task_types = ['SIMPLE', 'PATPIS', 'MONTHLY']
        if task_type not in valid_task_types:
            return api_response(
                error="Invalid task_type",
                message=f"Task type must be one of: {', '.join(valid_task_types)}",
                status_code=400
            )

        # Parse deadline if provided
        deadline = None
        if data.get('deadline'):
            try:
                deadline = parse_date(data['deadline'])
                if not deadline:
                    raise ValueError
            except ValueError:
                return api_response(
                    error="Invalid deadline format",
                    message="Deadline must be in YYYY-MM-DD format",
                    status_code=400
                )

        # Validate assigned users if provided
        assigned_users = []
        if data.get('assigned_user_ids'):
            user_ids = data['assigned_user_ids']
            if not isinstance(user_ids, list):
                return api_response(
                    error="Invalid assigned_user_ids",
                    message="assigned_user_ids must be an array",
                    status_code=400
                )

            assigned_users = User.objects.filter(id__in=user_ids)
            if len(assigned_users) != len(user_ids):
                found_ids = [user.id for user in assigned_users]
                missing_ids = [uid for uid in user_ids if uid not in found_ids]
                return api_response(
                    error="Invalid user IDs",
                    message=f"User IDs not found: {missing_ids}",
                    status_code=400
                )

        # Create task with transaction
        with transaction.atomic():
            # Calculate total hours and task percentage
            existing_tasks = Task.objects.filter(job=job)
            total_existing_hours = existing_tasks.aggregate(Sum('hours'))['hours__sum'] or 0
            total_hours = total_existing_hours + hours

            # Create the task
            task = Task.objects.create(
                job=job,
                title=data['title'],
                description=data['description'],
                hours=hours,
                money_for_task=money_for_task,
                progress=progress,
                task_type=task_type,
                deadline=deadline,
                task_percentage=(hours / total_hours) * 100
            )

            # Assign users
            if assigned_users:
                task.assigned_users.set(assigned_users)

            # Update percentages for all tasks in the job
            all_tasks = Task.objects.filter(job=job)
            for task_obj in all_tasks:
                task_obj.task_percentage = (task_obj.hours / total_hours) * 100
                task_obj.save(update_fields=['task_percentage'])

        # Return created task data
        assigned_users_data = [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
            for user in task.assigned_users.all()
        ]

        task_data = {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'hours': task.hours,
            'task_percentage': task.task_percentage,
            'progress': task.progress,
            'money_for_task': task.money_for_task,
            'paid': task.paid,
            'task_type': task.task_type,
            'confirmed': task.confirmed,
            'start_date': task.start_date.isoformat() if task.start_date else None,
            'deadline': task.deadline.isoformat() if task.deadline else None,
            'feedback': task.feedback,
            'assigned_users': assigned_users_data,
            'job_id': job.id
        }

        return api_response(
            data=task_data,
            message=f"Task '{task.title}' created successfully",
            status_code=201
        )

    except Job.DoesNotExist:
        return api_response(
            error="Job not found",
            message="The specified job does not exist",
            status_code=404
        )
    except Exception as e:
        return api_response(
            error=str(e),
            message="An error occurred while creating the task",
            status_code=500
        )


@csrf_exempt
@require_http_methods(["PUT", "PATCH"])
def api_update_task(request, job_id, task_id):
    """
    PUT/PATCH /api/jobs/{job_id}/tasks/{task_id}/
    Update an existing task

    Updatable fields:
    - title: string
    - description: string
    - hours: integer
    - money_for_task: integer
    - task_type: string (SIMPLE, PATPIS, MONTHLY)
    - deadline: string (YYYY-MM-DD format)
    - assigned_user_ids: array of user IDs
    - progress: integer (0-100)
    - feedback: string
    """
    try:
        # Verify job and task exist and are related
        job = get_object_or_404(Job, id=job_id)
        task = get_object_or_404(Task, id=task_id, job=job)

        # Parse JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return api_response(
                error="Invalid JSON",
                message="Request body must be valid JSON",
                status_code=400
            )

        # Track if hours changed for percentage recalculation
        hours_changed = False
        original_hours = task.hours

        # Update fields if provided and valid
        if 'title' in data:
            task.title = data['title']

        if 'description' in data:
            task.description = data['description']

        if 'hours' in data:
            try:
                hours = int(data['hours'])
                if hours <= 0:
                    return api_response(
                        error="Invalid hours",
                        message="Hours must be greater than 0",
                        status_code=400
                    )
                task.hours = hours
                if hours != original_hours:
                    hours_changed = True
            except ValueError:
                return api_response(
                    error="Invalid hours",
                    message="Hours must be an integer",
                    status_code=400
                )

        if 'money_for_task' in data:
            try:
                money_for_task = int(data['money_for_task'])
                if money_for_task < 0:
                    return api_response(
                        error="Invalid money_for_task",
                        message="Money for task must be 0 or greater",
                        status_code=400
                    )
                task.money_for_task = money_for_task
            except ValueError:
                return api_response(
                    error="Invalid money_for_task",
                    message="Money for task must be an integer",
                    status_code=400
                )

        if 'progress' in data:
            try:
                progress = int(data['progress'])
                if not (0 <= progress <= 100):
                    return api_response(
                        error="Invalid progress",
                        message="Progress must be between 0 and 100",
                        status_code=400
                    )
                task.progress = progress
            except ValueError:
                return api_response(
                    error="Invalid progress",
                    message="Progress must be an integer",
                    status_code=400
                )

        if 'task_type' in data:
            task_type = data['task_type']
            valid_task_types = ['SIMPLE', 'PATPIS', 'MONTHLY']
            if task_type not in valid_task_types:
                return api_response(
                    error="Invalid task_type",
                    message=f"Task type must be one of: {', '.join(valid_task_types)}",
                    status_code=400
                )
            task.task_type = task_type

        if 'deadline' in data:
            if data['deadline'] is None:
                task.deadline = None
            else:
                try:
                    deadline = parse_date(data['deadline'])
                    if not deadline:
                        raise ValueError
                    task.deadline = deadline
                except ValueError:
                    return api_response(
                        error="Invalid deadline format",
                        message="Deadline must be in YYYY-MM-DD format or null",
                        status_code=400
                    )

        if 'feedback' in data:
            task.feedback = data['feedback']

        # Handle assigned users
        if 'assigned_user_ids' in data:
            user_ids = data['assigned_user_ids']
            if not isinstance(user_ids, list):
                return api_response(
                    error="Invalid assigned_user_ids",
                    message="assigned_user_ids must be an array",
                    status_code=400
                )

            assigned_users = User.objects.filter(id__in=user_ids)
            if len(assigned_users) != len(user_ids):
                found_ids = [user.id for user in assigned_users]
                missing_ids = [uid for uid in user_ids if uid not in found_ids]
                return api_response(
                    error="Invalid user IDs",
                    message=f"User IDs not found: {missing_ids}",
                    status_code=400
                )

        # Save task and handle percentage recalculation
        with transaction.atomic():
            task.save()

            # Update assigned users if provided
            if 'assigned_user_ids' in data:
                task.assigned_users.set(assigned_users)

            # Recalculate percentages if hours changed
            if hours_changed:
                all_tasks = Task.objects.filter(job=job)
                total_hours = all_tasks.aggregate(Sum('hours'))['hours__sum'] or 1

                for task_obj in all_tasks:
                    task_obj.task_percentage = (task_obj.hours / total_hours) * 100
                    task_obj.save(update_fields=['task_percentage'])

        # Return updated task data
        assigned_users_data = [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
            for user in task.assigned_users.all()
        ]

        task_data = {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'hours': task.hours,
            'task_percentage': task.task_percentage,
            'progress': task.progress,
            'money_for_task': task.money_for_task,
            'paid': task.paid,
            'task_type': task.task_type,
            'confirmed': task.confirmed,
            'start_date': task.start_date.isoformat() if task.start_date else None,
            'deadline': task.deadline.isoformat() if task.deadline else None,
            'confirmation_date': task.confirmation_date.isoformat() if task.confirmation_date else None,
            'confirmed_by': task.confirmed_by.username if task.confirmed_by else None,
            'feedback': task.feedback,
            'assigned_users': assigned_users_data,
            'job_id': job.id
        }

        return api_response(
            data=task_data,
            message=f"Task '{task.title}' updated successfully"
        )

    except (Job.DoesNotExist, Task.DoesNotExist):
        return api_response(
            error="Task or Job not found",
            message="The specified task or job does not exist",
            status_code=404
        )
    except Exception as e:
        return api_response(
            error=str(e),
            message="An error occurred while updating the task",
            status_code=500
        )


@csrf_exempt
@require_http_methods(["DELETE"])
def api_delete_task(request, job_id, task_id):
    """
    DELETE /api/jobs/{job_id}/tasks/{task_id}/
    Delete a specific task
    """
    try:
        # Verify job and task exist and are related
        job = get_object_or_404(Job, id=job_id)
        task = get_object_or_404(Task, id=task_id, job=job)

        # Store task info for response
        task_title = task.title
        task_id_deleted = task.id

        # Delete task and recalculate percentages
        with transaction.atomic():
            task.delete()

            # Recalculate percentages for remaining tasks
            remaining_tasks = Task.objects.filter(job=job)
            total_hours = remaining_tasks.aggregate(Sum('hours'))['hours__sum']

            if total_hours and total_hours > 0:
                for remaining_task in remaining_tasks:
                    remaining_task.task_percentage = (remaining_task.hours / total_hours) * 100
                    remaining_task.save(update_fields=['task_percentage'])

        return api_response(
            data={
                'deleted_task_id': task_id_deleted,
                'deleted_task_title': task_title
            },
            message=f"Task '{task_title}' deleted successfully"
        )

    except (Job.DoesNotExist, Task.DoesNotExist):
        return api_response(
            error="Task or Job not found",
            message="The specified task or job does not exist",
            status_code=404
        )
    except Exception as e:
        return api_response(
            error=str(e),
            message="An error occurred while deleting the task",
            status_code=500
        )


@csrf_exempt
@require_http_methods(["GET"])
def api_get_task_statistics(request, job_id):
    """
    GET /api/jobs/{job_id}/tasks/statistics/
    Get task statistics for a specific job
    """
    try:
        # Verify job exists
        job = get_object_or_404(Job, id=job_id)

        # Get task statistics
        tasks = Task.objects.filter(job=job)

        # Count tasks by type
        simple_tasks = tasks.filter(task_type='SIMPLE').count()
        patpis_tasks = tasks.filter(task_type='PATPIS').count()
        monthly_tasks = tasks.filter(task_type='MONTHLY').count()

        # Count tasks by progress status
        completed_tasks = tasks.filter(progress=100).count()
        in_progress_tasks = tasks.filter(progress__gt=0, progress__lt=100).count()
        pending_tasks = tasks.filter(progress=0).count()

        # Count confirmed tasks
        confirmed_tasks = tasks.filter(confirmed=True).count()
        paid_tasks = tasks.filter(paid=True).count()

        # Calculate financial statistics
        total_task_money = tasks.aggregate(Sum('money_for_task'))['money_for_task__sum'] or 0
        paid_money = tasks.filter(paid=True).aggregate(Sum('money_for_task'))['money_for_task__sum'] or 0
        unpaid_money = total_task_money - paid_money

        # Calculate total hours
        total_hours = tasks.aggregate(Sum('hours'))['hours__sum'] or 0

        # Get job overall progress
        overall_progress = job.get_overall_progress() if hasattr(job, 'get_overall_progress') else 0

        statistics = {
            'job': {
                'id': job.id,
                'title': job.title,
                'overall_progress': overall_progress,
                'total_income': job.over_all_income
            },
            'task_counts': {
                'total_tasks': tasks.count(),
                'simple_tasks': simple_tasks,
                'patpis_tasks': patpis_tasks,
                'monthly_tasks': monthly_tasks
            },
            'progress_status': {
                'completed_tasks': completed_tasks,
                'in_progress_tasks': in_progress_tasks,
                'pending_tasks': pending_tasks
            },
            'confirmation_status': {
                'confirmed_tasks': confirmed_tasks,
                'paid_tasks': paid_tasks,
                'unconfirmed_tasks': tasks.count() - confirmed_tasks
            },
            'financial_summary': {
                'total_task_money': total_task_money,
                'paid_money': paid_money,
                'unpaid_money': unpaid_money,
                'remaining_job_budget': job.over_all_income - total_task_money
            },
            'hours_summary': {
                'total_hours': total_hours
            }
        }

        return api_response(
            data=statistics,
            message=f"Statistics retrieved for job '{job.title}'"
        )

    except Job.DoesNotExist:
        return api_response(
            error="Job not found",
            message="The specified job does not exist",
            status_code=404
        )
    except Exception as e:
        return api_response(
            error=str(e),
            message="An error occurred while retrieving statistics",
            status_code=500
        )
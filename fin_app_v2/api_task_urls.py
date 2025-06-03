from django.urls import path
from . import api_task_views

urlpatterns = [
    # Task CRUD API endpoints

    # GET all tasks for a job
    path('jobs/<int:job_id>/tasks/',
         api_task_views.api_get_all_tasks,
         name='api_get_all_tasks'),

    # GET specific task details
    path('jobs/<int:job_id>/tasks/<int:task_id>/',
         api_task_views.api_get_task_detail,
         name='api_get_task_detail'),

    # POST create new task
    path('jobs/<int:job_id>/tasks/create/',
         api_task_views.api_create_task,
         name='api_create_task'),

    # PUT/PATCH update task
    path('jobs/<int:job_id>/tasks/<int:task_id>/update/',
         api_task_views.api_update_task,
         name='api_update_task'),

    # DELETE task
    path('jobs/<int:job_id>/tasks/<int:task_id>/delete/',
         api_task_views.api_delete_task,
         name='api_delete_task'),

    # GET task statistics for a job
    path('jobs/<int:job_id>/tasks/statistics/',
         api_task_views.api_get_task_statistics,
         name='api_get_task_statistics'),
]
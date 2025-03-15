from django.urls import path

from . import views
from .views import (create_job, create_tasks, job_list, client_login, client_progress,developer_login,developer_tasks,admin_dashboard,
                    deduction_logs,all_deduction_logs,deduction_logs_admin,deduct_balance,login_view)

urlpatterns = [
    # Job creation (no developers assigned here)
    path('deduction_logs_admin/', views.deduction_logs_admin, name='deduction_logs_admin'),
    path('job_details/<int:job_id>/', views.job_details, name='job_details'),
    path('deduct/', views.deduction_page, name='deduction_page'),
    path('payment_history/', views.payment_history, name='payment_history'),  # New URL for Payment History
    path('overdue_tasks/', views.overdue_tasks, name='overdue_tasks'),
    path('job/<int:job_id>/update/', views.update_job, name='update_job'),

    path('job/<int:job_id>/add_task/', views.add_task_to_job, name='add_task_to_job'),
 # Add money URL


    # Task creation (developers assigned here)
    path('jobs/<int:job_id>/tasks/create/', create_tasks, name='task_create'),

    # View job list
    path('jobs/', job_list, name='job_list'),

    # Client login
    path('client/login/', client_login, name='client_login'),

    # Client progress (view tasks for a job)
    path('client/progress/', client_progress, name='client_progress'),

    path('developer/login/', developer_login, name='developer_login'),
    path('developer/tasks/', developer_tasks, name='developer_tasks'),
    path('deduction_logs/<int:developer_id>/', deduction_logs, name='deduction_logs'),

    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('deduct-balance/<int:developer_id>/', deduct_balance, name='deduct_balance'),
    path('job-list/', job_list, name='job_list'),
    path('', login_view, name='login'),

# Admin login URL
    path('login/', views.login_view, name='login'),

    path('task/<int:task_id>/delete/', views.delete_task, name='delete_task'),

    # Job creation URLs
    path('create_job/', views.create_job, name='create_job'),
    path('task_create/<int:job_id>/', views.create_tasks, name='task_create'),

    # Job list URL
    path('job_list/', views.job_list, name='job_list'),

    # Client URLs
    path('client_login/', views.client_login, name='client_login'),
    path('client_progress/', views.client_progress, name='client_progress'),
    path('client_progress_details/', views.client_progress_details, name='client_progress_details' ),

    # Developer URLs
    path('developer_login/', views.developer_login, name='developer_login'),
    path('developer_tasks/', views.developer_tasks, name='developer_tasks'),
    path('update_progress/', views.developer_tasks, name='update_progress'),  # For AJAX progress updates

    # Admin dashboard URL
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Deduct balance URL
    path('deduct_balance/<int:developer_id>/', views.deduct_balance, name='deduct_balance'),
    path('task/<int:task_id>/change-status/', views.change_task_status, name='change_task_status'),
    path('deduction-logs/', all_deduction_logs, name='all_deduction_logs'),
    #path('deduction_logs/<int:developer_id>/', deduction_logs, name='deduction_logs'),


    path('update_feedback/', views.update_feedback, name='update_feedback'),
    path('payment_load/', views.payment_load, name='payment_load'),
# Add this to your urls.py file
    path('task/<int:task_id>/edit/', views.edit_task, name='edit_task'),




# Add this to your urls.py patterns

    path('job-statistics/', views.job_statistics, name='job_statistics'),

    path('job/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    path('update-progress/', views.update_progress, name='update_progress'),

    path('admin/all-developer-tasks/', views.all_developer_tasks, name='all_developer_tasks'),


# Add this to your urls.py urlpatterns
   path('admin/tasks/', views.enhanced_tasks_view, name='enhanced_tasks'),




    path('dev_history/', views.developer_payment_sheet, name='dev_history'),
]

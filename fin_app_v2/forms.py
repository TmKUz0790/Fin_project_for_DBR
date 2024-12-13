# # from django import forms
# # from django.contrib.auth.models import User
# # from django.forms import inlineformset_factory
# #
# # from .models import Job, Task
# #
# # # Job form to create a job (without assigning developers)
# # class JobForm(forms.ModelForm):
# #     class Meta:
# #         model = Job
# #         fields = ['title', 'client_email', 'client_password']  # Only job details
# #
# # # Task form to assign developers by email during task creation
# # # class TaskForm(forms.ModelForm):
# # #     assigned_users = forms.ModelMultipleChoiceField(
# # #         queryset=User.objects.filter(is_staff=True),  # Filter for authorized developers
# # #         widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
# # #         label="Assign Developers (by Email)"
# # #     )
# # #
# # #     class Meta:
# # #         model = Task
# # #         fields = ['title', 'assigned_users', 'description']  # Task details and developers
# # #
# # #     # Overriding the label to display user emails instead of usernames
# # #     def __init__(self, *args, **kwargs):
# # #         super(TaskForm, self).__init__(*args, **kwargs)
# # #         self.fields['assigned_users'].queryset = User.objects.filter(is_staff=True)
# # #         self.fields['assigned_users'].label_from_instance = lambda obj: f"{obj.email}"  # Show email in the dropdown
# #
# #
# # from django import forms
# # from .models import Task
# # from django.contrib.auth.models import User
# #
# #
# # class TaskForm(forms.ModelForm):
# #     assigned_users = forms.ModelMultipleChoiceField(
# #         queryset=User.objects.filter(is_staff=True),
# #         widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
# #         label="Assign Developers (by Email)"
# #     )
# #     deadline = forms.DateField(
# #         widget=forms.TextInput(attrs={'type': 'date'}),  # Input for selecting a date
# #         required=False,
# #         label="Deadline"
# #     )
# #
# #     class Meta:
# #         model = Task
# #         fields = ['title', 'description', 'assigned_users', 'task_percentage', 'progress', 'deadline']
# #
# #     def __init__(self, *args, **kwargs):
# #         super(TaskForm, self).__init__(*args, **kwargs)
# #         self.fields['assigned_users'].queryset = User.objects.filter(is_staff=True)
# #         self.fields['assigned_users'].label_from_instance = lambda obj: f"{obj.email}"  # Show email instead of username
# #
# #
# # # Inline formset for multiple tasks
# # TaskFormSet = forms.inlineformset_factory(Job, Task, form=TaskForm, extra=1)
# #
# #
# # # Client login form definition
# # class ClientLoginForm(forms.Form):
# #     email = forms.EmailField()
# #     password = forms.CharField(widget=forms.PasswordInput)
#
#
# #version 2
#
#
# from django import forms
# from django.contrib.auth.models import User
# from django.forms import inlineformset_factory
#
# from .models import Job, Task
#
# # Job form to create a job (with over_all_income field)
# class JobForm(forms.ModelForm):
#     class Meta:
#         model = Job
#         fields = ['title', 'client_email', 'client_password', 'over_all_income']  # Added 'over_all_income'
#
#
#
#
# from django import forms
# from django.forms import inlineformset_factory
# from django.contrib.auth.models import User
# from .models import Task, Job
#
# class TaskForm(forms.ModelForm):
#     assigned_users = forms.ModelMultipleChoiceField(
#         queryset=User.objects.filter(is_staff=True),
#         widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
#         label="Assign Developers (by Email)"
#     )
#     deadline = forms.DateField(
#         widget=forms.TextInput(attrs={'type': 'date'}),
#         required=False,
#         label="Deadline"
#     )
#     hours = forms.IntegerField(
#         widget=forms.NumberInput(attrs={'class': 'form-control'}),
#         label="Hours",
#         min_value=1  # Ensure the hours are positive
#     )
#
#     class Meta:
#         model = Task
#         fields = ['title', 'description', 'assigned_users', 'hours', 'deadline', 'money_for_task']
#
#     def __init__(self, *args, **kwargs):
#         super(TaskForm, self).__init__(*args, **kwargs)
#         # Display emails of staff users in assigned_users field
#         self.fields['assigned_users'].queryset = User.objects.filter(is_staff=True)
#         self.fields['assigned_users'].label_from_instance = lambda obj: f"{obj.email}"
#
# # Inline formset for creating multiple Task forms associated with a Job
# TaskFormSet = inlineformset_factory(Job, Task, form=TaskForm, extra=1)
#
# # Client login form definition
# class ClientLoginForm(forms.Form):
#     email = forms.EmailField()
#     password = forms.CharField(widget=forms.PasswordInput)
from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from .models import Job, Task

# Job form to create or update a job
class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'client_email', 'client_password', 'over_all_income']  # Include all necessary fields

    def __init__(self, *args, **kwargs):
        super(JobForm, self).__init__(*args, **kwargs)
        # Customizing the widgets for better styling
        self.fields['client_password'].widget = forms.PasswordInput(attrs={'placeholder': 'Enter client password'})
        self.fields['title'].widget.attrs.update({'placeholder': 'Job Title', 'class': 'form-control'})
        self.fields['client_email'].widget.attrs.update({'placeholder': 'Client Email', 'class': 'form-control'})
        self.fields['over_all_income'].widget.attrs.update({'class': 'form-control'})


# Task form to create or update individual tasks
class TaskForm(forms.ModelForm):
    assigned_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_staff=True),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        label="Assign Developers (by Email)",
        required=False
    )
    deadline = forms.DateField(
        widget=forms.TextInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False,
        label="Deadline"
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control'}),
        required=False,
        label="Description"
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_users', 'hours', 'deadline', 'money_for_task']
    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        # Customizing fields for better user experience
        self.fields['title'].widget.attrs.update({'placeholder': 'Task Title', 'class': 'form-control'})
        self.fields['description'].widget.attrs.update({'placeholder': 'Task Description', 'class': 'form-control'})
        self.fields['money_for_task'].widget.attrs.update({'placeholder': 'Payment for this task', 'class': 'form-control'})
        self.fields['assigned_users'].label_from_instance = lambda obj: f"{obj.email}"  # Display emails for clarity


# Inline formset for associating multiple tasks with a job
TaskFormSet = inlineformset_factory(
    Job, Task,
    form=TaskForm,
    extra=1,  # Number of blank forms to display initially
    can_delete=True,  # Allow deletion of existing forms
)


# Client login form
class ClientLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email', 'class': 'form-control'}),
        label="Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password', 'class': 'form-control'}),
        label="Password"
    )


# Developer login form
class DeveloperLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email', 'class': 'form-control'}),
        label="Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password', 'class': 'form-control'}),
        label="Password"
    )

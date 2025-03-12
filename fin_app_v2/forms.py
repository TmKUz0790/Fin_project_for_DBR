


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
        widget=forms.TextInput(attrs={'type': 'date', 'class': 'form-control deadline-field'}),
        required=False,
        label="Deadline"
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control'}),
        required=False,
        label="Description"
    )
    task_type = forms.ChoiceField(
        choices=Task.TASK_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control task-type-select'}),
        label="Task Type",
        initial='SIMPLE'
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_users', 'hours', 'deadline', 'money_for_task', 'task_type']

    def __init__(self, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        # Customizing fields for better user experience
        self.fields['title'].widget.attrs.update({'placeholder': 'Task Title', 'class': 'form-control'})
        self.fields['description'].widget.attrs.update({'placeholder': 'Task Description', 'class': 'form-control'})
        self.fields['money_for_task'].widget.attrs.update(
            {'placeholder': 'Payment for this task', 'class': 'form-control'})
        self.fields['assigned_users'].label_from_instance = lambda obj: f"{obj.email}"  # Display emails for clarity
        self.fields['task_type'].widget.attrs.update({'class': 'form-control task-type-select'})
        self.fields[
            'task_type'].help_text = 'Simple - regular task, Monthly - monthly task, Follow Task - creates recurring tasks'


# Inline formset for associating multiple tasks with a job
TaskFormSet = inlineformset_factory(
    Job, Task,
    form=TaskForm,
    exclude=['start_date'],  # Exclude non-editable fields
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


# Add this class to your forms.py file

class EditTaskForm(TaskForm):
    """Extended TaskForm that includes progress field for editing existing tasks."""

    progress = forms.IntegerField(
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Progress (%)",
        help_text="Current completion percentage (0-100)"
    )

    class Meta(TaskForm.Meta):
        model = Task
        fields = TaskForm.Meta.fields + ['progress']
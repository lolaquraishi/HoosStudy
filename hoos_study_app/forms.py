from django import forms
from datetime import datetime, timedelta

from django.contrib.auth.forms import UserChangeForm
from allauth.socialaccount.forms import SignupForm
from django import forms as d_forms # need 'as d_forms' to prevent circular import error
from . import models
from .models import User, StudySessionLocation, StudySession, StudySessionAvailability, Course
from django.core.exceptions import ValidationError

class UserProfileForm(UserChangeForm):
    password = None  # Exclude the password field from the form

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'year']

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

class SelectDefaultPictureForm(forms.Form):
    selected_default_picture = forms.CharField(widget=forms.HiddenInput())

class CustomSocialSignupForm(SignupForm):

    first_name = d_forms.CharField(max_length=150, label='First Name', required=True)
    last_name = d_forms.CharField(max_length=150, label='Last Name', required=True)

    year = d_forms.ChoiceField(
        choices=models.User.YEAR_CHOICES + [('', 'Select your year')],
        label='Academic Year',
        required=True
    )

    def save(self, request):

        # Ensure save is called.
        # .save() returns a User object.
        user = super(CustomSocialSignupForm, self).save(request)

        # Add your own processing here before returning if needed.
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.year = self.cleaned_data['year']

        user.save()
        return user

# Creating Forms: https://docs.djangoproject.com/en/5.1/topics/forms/modelforms/
class UploadFileForm(d_forms.ModelForm):
    class Meta:
        model = models.Document
        fields = ["filename", "file", "course", "description", "keywords"]

        widgets = {
            'filename': d_forms.TextInput(attrs={'class': 'form-control'}),
            'file': d_forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'course': d_forms.Select(attrs={'class': 'form-control'}),
            'description': d_forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'keywords': d_forms.CheckboxSelectMultiple(),
        }

    # Validate filename length
    def clean_file(self):
        file = self.cleaned_data.get('file')

        if file:
            if len(file.name) > 100:
                raise d_forms.ValidationError('Filename cannot exceed 100 characters.')
        return file

    # Only show courses user is enrolled in
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['course'].queryset = Course.objects.filter(students=user)
            self.fields['course'].required = False

# FileFormset = forms.inlineformset_factory(models.Document, models.Course, form=UploadFileForm)


class LocationForm(forms.ModelForm):

    class Meta:
        model = StudySessionLocation
        fields = ('name', 'room_number', 'description')

#https://stackoverflow.com/questions/3367091/whats-the-cleanest-simplest-to-get-running-datepicker-in-django
class DateInput(forms.DateInput):
    input_type = 'date'

class StudySessionForm(forms.ModelForm):

    class Meta:
        model = StudySession
        fields = ('name','date', 'created_by', 'description', 'location_name', 'room_number', 'description_of_location')
        widgets= {
            'date': DateInput(attrs={'type':'date',"class":"form-control"}),
            # 'course_name': forms.Select(attrs={ "rows": 1, "cols":40, "class":"form-control"}),
            'name':forms.TextInput(attrs={'Placeholder': 'Study session name', "rows": 1, "cols":40, "class":"form-control"}),
            'description': forms.Textarea(attrs={'Placeholder': 'Give a brief description of your event', "rows": 2, "cols":40, "class":"form-control"}),
            'created_by': forms.TextInput(attrs={'Placeholder': 'Your name', "class":"form-control"}),
            'location_name': forms.TextInput(attrs={'Placeholder': 'Building name', "rows": 1, "cols":40, "class":"form-control"}),
            'room_number': forms.NumberInput(attrs={'Placeholder': 'Room number', "rows": 1, "cols":40, "class":"form-control"}),
            'description_of_location': forms.Textarea(attrs={'Placeholder': 'Any directions or extra location '
                                                                             'details? ',
                                                             "rows": 2, "cols":40, "class":"form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # self.fields['course_name'].queryset = Course.objects.filter(students=user)
            self.fields['created_by'].initial = f"{user.first_name} {user.last_name}"



class AvailabilityForm(forms.ModelForm):

    time_slots = forms.MultipleChoiceField(

        widget = forms.CheckboxSelectMultiple,
        label= "Select all time periods you are available for"

    )

    class Meta:
        model = StudySessionAvailability
        fields = ('user_name', 'time_slots')
        # widgets = {
        #
        #     'user_name': forms.TextInput(
        #         attrs={ "class": "form-control", "rows": 1, "cols":10,}),
        # }

    def clean_time_slots(self):
        time_slots = self.cleaned_data['time_slots']
        return ", ".join(time_slots)
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['user_name'].initial = f"{user.first_name} {user.last_name}"



import os, random, boto3
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib import admin
from django.core.exceptions import ValidationError


# imports for upload_file
# from django.http import HttpResponseRedirect
# from django.shortcuts import render
# from .forms import UploadFileForm
# from django.contrib import admin
from django.contrib.auth.models import AbstractUser, AnonymousUser, User

# Validators for profile picture upload
def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = ['.jpg', '.jpeg', '.png']
    if ext not in valid_extensions:
        raise ValidationError("Only JPG and PNG files are allowed.")
    
def validate_file_size(value):
    max_file_size = 2 * 1024 * 1024  # 2MB
    if value.size > max_file_size:
        raise ValidationError("File size should not exceed 2MB.")
    
def random_profile_picture():
    if settings.USE_S3:
        # Connect to S3
        s3 = boto3.resource('s3')
        # Access the bucket and get objects
        bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
        objects = bucket.objects.filter(Prefix=f'{settings.MEDIA_LOCATION}/profile_pictures/default_profile_pictures/')

        images = [os.path.basename(obj.key) for obj in objects if not obj.key.endswith('/')]
        return f"profile_pictures/default_profile_pictures/{random.choice(images)}"
    else:
        # Use local storage
        img_path = os.path.join(settings.MEDIA_ROOT, 'profile_pictures/default_profile_pictures/')
        images = os.listdir(img_path)
        return f"profile_pictures/default_profile_pictures/{random.choice(images)}"
    

# Creating User and Admin profiles: https://learndjango.com/tutorials/django-custom-user-model
class User(AbstractUser):
    YEAR_CHOICES = [
        ('1', 'First Year'),
        ('2', 'Second Year'),
        ('3', 'Third Year'),
        ('4', 'Fourth Year'),
    ]

    is_pma_admin = models.BooleanField(default=False)
    year = models.CharField(max_length=1, choices=YEAR_CHOICES,  null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', null=True, blank=True,
        validators=[validate_file_extension, validate_file_size],
        default=random_profile_picture
    )

    def __str__(self):
        return self.username

# class Anonymous(AnonymousUser):
#     pass

class Course(models.Model):
    mnemonic = models.CharField(max_length=4, default="GEN")
    number = models.IntegerField(default=1000)
    title = models.CharField(max_length=100, default="HOOS")
    students = models.ManyToManyField(User, related_name="courses", blank=True)
    semester = models.CharField(max_length=20, default="N/A")

    def save(self, *args, **kwargs):
        # Call the original save method to create the Course instance
        super().save(*args, **kwargs)
        # Check if the course has an associated message board
        if not hasattr(self, 'message_board'):
            MessageBoard.objects.create(course=self)

    def __str__(self):
        return f"{self.mnemonic} {self.number} {self.title}"

class Keyword(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

# Message Board Model
class MessageBoard(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='message_board')

    def __str__(self):
        return f"Message Board for: {self.course}"

# Message Model
class Message(models.Model):
    message_board = models.ForeignKey(MessageBoard, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_anonymous = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}"

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

class StudySessionAvailability(models.Model):
    session = models.ForeignKey('StudySession', on_delete=models.CASCADE)
    user_name = models.CharField('Your Name', max_length=200) #chnage to connect to user
    time_slots = models.TextField( default="")

class StudySessionLocation(models.Model):
    name = models.CharField('Study Session Location', max_length=200)
    room_number = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class StudySessionAttendee(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank = True)
    def __str__(self):
        return self.first_name + " " + self.last_name
    
class StudySession(models.Model): #what we need to keep track of in the tables
    name = models.CharField('Study Session Name', max_length=200)
    course_name = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateTimeField('Study Session Date')
    created_by = models.CharField(max_length=200)

    # fix this later - make null and blank FALSE
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_sessions", null=True, blank=True)
    description = models.CharField(max_length=400)
    # location = models.ForeignKey(StudySessionLocation, blank=True, null=True, on_delete=models.CASCADE) #now connected to location
    location_name = models.CharField('Study Session Location', max_length=200)
    room_number = models.CharField(max_length=50, null=True, blank = True, default="No room number provided")
    description_of_location = models.CharField(max_length=400 )
    attendees = models.ManyToManyField(User, related_name="study_session") # now allows users to sign up for many sessions

    def __str__(self): #use model in admin
        return self.name
    
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

class JoinRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="join_requests")
    study_session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name="join_requests")
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
    ], default='pending')

    def __str__(self):
        return f"{self.user.username} -> {self.study_session.name} ({self.status})"
    
def random_background_image():

    if settings.USE_S3:
        # Connect to S3
        s3 = boto3.resource('s3')
        # Access the bucket and get objects
        bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
        objects = bucket.objects.filter(Prefix=f'{settings.STATIC_LOCATION}/hoos_study_app/img/card_backgrounds/')

        images = [os.path.basename(obj.key) for obj in objects if not obj.key.endswith('/')]
        return random.choice(images)
    else:
        # Use local storage
        img_path = os.path.join(settings.STATICFILES_DIRS[0], 'hoos_study_app/img/card_backgrounds')
        images = os.listdir(img_path)
        return random.choice(images)
    
class UserCoursePreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    background_image = models.CharField(max_length=255, blank=True, null=True, default=random_background_image)  # Path to the selected image


class Document(models.Model):
    filename = models.CharField(max_length=50)
    file = models.FileField(upload_to='class_documents/')
    # To delete User without deleting their documents, use "on_delete=models.SET_NULL" with "null=True, blank=True"
    author = models.ForeignKey('User', on_delete=models.CASCADE, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    study_session = models.ForeignKey(StudySession, on_delete=models.CASCADE, null=True, blank=True)

    create_time = models.DateTimeField(default=timezone.now)
    description = models.CharField(max_length=500, default="No description provided.")
    keywords = models.ManyToManyField(Keyword, blank=True)

    def __str__(self):
        return self.filename

    def delete(self, *args, **kwargs):
        self.file.delete()
        super().delete(*args, **kwargs)


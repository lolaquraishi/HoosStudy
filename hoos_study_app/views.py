from django.db import transaction
from django.conf import settings
from django.shortcuts import redirect, render, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.db.models import Q
from collections import defaultdict

# imports for google authentication
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

# imports for creating user accounts
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView

# imports for upload_file
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect
from django.forms import HiddenInput
# # from django.shortcuts import render
from .forms import UploadFileForm, LocationForm, StudySessionForm, AvailabilityForm, UserProfileForm, ProfilePictureForm, SelectDefaultPictureForm
# , CreateUserForm
# from .models import User
from . import forms, models
from .models import JoinRequest, StudySession, StudySessionAvailability, Course, Message, MessageBoard, Document, UserCoursePreference
from datetime import datetime, timedelta
from collections import Counter
from django.views.decorators.cache import cache_control
import time, os, random, boto3
from django.utils.timezone import localdate
from django.contrib import messages
# imports for editing/deleting messages
from django.http import JsonResponse, HttpResponseRedirect , HttpResponseForbidden
from django.core.exceptions import PermissionDenied

# Class/Study group page
@login_required
def leave_course_group(request, course_id):
    # Fetch the course by ID
    course = get_object_or_404(Course, id=course_id)

    # Remove the current user from the course's student list if they are a member
    course.students.remove(request.user)
    # Delete the user's preferences for this course
    UserCoursePreference.objects.filter(user=request.user, course=course).delete()
    
    messages.success(request, f"You have successfully left {course.mnemonic} {course.number}.")

    # Redirect to the course group page
    return redirect('hoos_study_app:dashboard')

@login_required
def join_course_group(request, course_id):
    # Fetch the course by ID
    course = get_object_or_404(Course, id=course_id)

    # Add the current user to the course's student list
    course.students.add(request.user)
    UserCoursePreference.objects.get_or_create(user=request.user, course=course)
    course.save()
    
    messages.success(request, f"You have successfully joined {course.mnemonic} {course.number}.")

    return redirect('hoos_study_app:course_group', pk=course.id)

class CourseGroupView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = 'hoos_study_app/course_group.html'
    context_object_name = 'course'

    def get_object(self):
        # Fetch the course by its ID or slug from the URL
        course_id = self.kwargs.get("pk")
        return get_object_or_404(Course, pk=course_id)
    
    # Handle POST for message board    
    def post(self, request, *args, **kwargs):
        course = self.get_object()
        board = get_object_or_404(MessageBoard, course=course)
        content = request.POST.get('content', '')
        is_anonymous = request.POST.get("is_anonymous") == "on"
        # messages = board.messages.select_related('user').order_by('timestamp')


        if content:
            Message.objects.create(
                message_board=board,
                user=request.user,
                content=content,
                is_anonymous=is_anonymous,
            )
        
        # Redirect back to the same page after handling POST
        return redirect('hoos_study_app:course_group', pk=course.id)

    def get_context_data(self, **kwargs):
        # Get the base context from DetailView
        context = super().get_context_data(**kwargs)
        course = self.get_object()

        today = localdate()

        # Add additional data to the context
        context['documents'] = Document.objects.filter(course=course)
        context['message_board'] = course.message_board
        context['students'] = course.students.all()
        context['all_study_sessions'] = StudySession.objects.filter(course_name=course).order_by('date')
        context['upcoming_study_sessions'] = StudySession.objects.filter(course_name=course).filter(date__gte=today).order_by('date')
        context['past_study_sessions'] = StudySession.objects.filter(course_name=course).filter(date__lt=today).order_by('-date')
        context['background_image'] = UserCoursePreference.objects.get(user=self.request.user, course=course).background_image

        # Add message board data
        board = course.message_board
        messages = board.messages.select_related('user').order_by('-timestamp')
        context['board_messages'] = messages
        context['current_user'] = self.request.user

        context['submitted'] = 'submitted' in self.request.GET

        return context

class ClassesView(ListView):
    model = Course
    template_name = "hoos_study_app/classes.html"
    context_object_name = "class_list"

    def get_queryset(self):
        return Course.objects.order_by('mnemonic', 'number')

def home(request):
    if request.user.is_authenticated:
        # Redirect to the dashboard for logged-in users
        return redirect('hoos_study_app:dashboard')
    else:
        return render(request, template_name="hoos_study_app/index.html")

# Helper function
def get_profile_pictures():
    if settings.USE_S3:
        # Connect to S3
        s3 = boto3.resource('s3')
        # Access the bucket and get objects
        bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
        objects = bucket.objects.filter(Prefix=f'{settings.MEDIA_LOCATION}/profile_pictures/default_profile_pictures/')

        images = [os.path.basename(obj.key) for obj in objects if not obj.key.endswith('/')]
        return images
    else:
        # Use local storage
        img_path = os.path.join(settings.MEDIA_ROOT, 'profile_pictures/default_profile_pictures/')
        images = os.listdir(img_path)
        return images

@login_required
def profile(request):
    user = request.user

    images = get_profile_pictures()
    
    # Initialize forms
    account_details_form = UserProfileForm(instance=user)
    upload_picture_form = ProfilePictureForm(instance=user)
    default_picture_form = SelectDefaultPictureForm()

    if request.method == 'POST':
        if 'account_details_update' in request.POST:
            account_details_form = UserProfileForm(request.POST, instance=user)
            if account_details_form.is_valid():
                account_details_form.save()
                messages.success(request, "Your profile has been updated successfully.")
                return redirect('hoos_study_app:profile')
        elif 'upload_picture' in request.POST:
            upload_picture_form = ProfilePictureForm(request.POST, request.FILES, instance=user)

            if upload_picture_form.is_valid():
                upload_picture_form.save()
                messages.success(request, "Your profile picture has been updated successfully.")
                return redirect('hoos_study_app:profile')
            
        elif 'select_default' in request.POST:
            default_picture_form = SelectDefaultPictureForm(request.POST)

            if default_picture_form.is_valid():
                selected_picture = default_picture_form.cleaned_data['selected_default_picture']
                user.profile_picture = f'profile_pictures/default_profile_pictures/{selected_picture}'
                user.save()
                messages.success(request, "Your profile picture has been updated successfully.")
                return redirect('hoos_study_app:profile')
    
    # Render the template
    return render(request, 'hoos_study_app/profile.html', {
        'form': account_details_form,
        'upload_picture_form': upload_picture_form,
        'default_picture_form': default_picture_form,
        'default_pictures': images,
        'creation_date': user.date_joined,
    })

def logout_view(request):
    logout(request)
    messages.success(request, "Successfully logged out.")
    return redirect("hoos_study_app:home")

# Upload and display documents (video series): https://www.youtube.com/watch?v=Zx09vcYq1oc
class DocumentsListView(LoginRequiredMixin, ListView):
    model = models.Document
    template_name = "hoos_study_app/documents.html"
    context_object_name = "documents"

    def get_queryset(self):
        # # Only return documents that belong to the logged-in user
        # return models.Document.objects.filter(author=self.request.user)

        # Get the search query from the GET request
        query = self.request.GET.get('q')

        # Start with the base queryset (documents for the logged-in user)
        queryset = models.Document.objects.filter(author=self.request.user)

        # If there is a search query, filter the queryset across multiple fields
        if query:
            queryset = queryset.filter(
                Q(filename__icontains=query) |
                Q(description__icontains=query) |
                Q(course__mnemonic__icontains=query) |  # Searches Course mnemonic
                Q(course__number__icontains=query) |    # Searches Course number
                Q(course__title__icontains=query) |     # Searches Course title
                Q(keywords__name__icontains=query)      # Searches Keyword name
            ).distinct()
        return queryset



# @login_required(login_url='hoos_study_app:documents')
def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            document = form.save(commit=False)
            document.author = request.user
            document.save()
            form.save_m2m()
            return redirect("hoos_study_app:documents")
    else:
        # form = UploadFileForm()
        form = UploadFileForm(user=request.user)
    return render(request, 'hoos_study_app/upload.html', {'form': form})

def upload_file_study_session(request, course_id, session_id):
    # Get the StudySession instance
    course = get_object_or_404(Course, id=course_id)
    study_session = get_object_or_404(StudySession, id=session_id)

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            document = form.save(commit=False)
            document.author = request.user
            document.study_session = study_session  # Associate with the StudySession
            document.course = study_session.course_name  # Automatically set the course
            document.save()
            form.save_m2m()  # Save any ManyToMany fields
            return redirect("hoos_study_app:study_session_dashboard", course_id=course_id, session_id=study_session.id)
    else:
        form = UploadFileForm(user=request.user)

    return render(request, 'hoos_study_app/upload_to_study_session.html', {
        'form': form,
        'course': course,
        'study_session': study_session,
    })

# def study_session_dashboard(request, course_id, session_id):
#     course = get_object_or_404(Course, id=course_id)
#     study_session = get_object_or_404(StudySession, id=session_id, course_name=course)
#
#
#     return render(request, 'hoos_study_app/study_session_dashboard.html', {
#         'course': course,
#         'study_session': study_session,
#     })


def study_session_dashboard(request, course_id, session_id):
    #using give availabilty view
    course = get_object_or_404(Course, id=course_id)
    study_session = get_object_or_404(StudySession, id=session_id, course_name=course)

    # Only show pending requests if the user is the owner
    pending_requests = study_session.join_requests.filter(status='pending') if request.user == study_session.owner else None

    user_has_pending_request = study_session.join_requests.filter(user=request.user, status='pending').exists()



    time_slots = time_slot_list()
    availabilities = StudySessionAvailability.objects.filter(session=study_session)


    availability_data = defaultdict(list)
    for availability in availabilities:
        for time_slot in availability.time_slots.split(","):
            availability_data[time_slot.strip()].append(availability.user_name)


    data = {
        'availabilities': availabilities,
        'availability_data': availability_data,
    }


    form = AvailabilityForm(user=request.user)
    form.fields['time_slots'].choices = create_time_choices()

    if request.method == 'POST':
        form = AvailabilityForm(request.POST, user=request.user)
        form.fields['time_slots'].choices = create_time_choices()
        if form.is_valid():
            availability = form.save(commit=False)
            if isinstance(availability.time_slots, list):
                availability.time_slots = ", ".join(availability.time_slots)
            availability.session = study_session
            availability.save()



            if request.user not in study_session.attendees.all():
                study_session.attendees.add(request.user)
                study_session.save()


            return redirect('hoos_study_app:study_session_dashboard',course_id=study_session.course_name.id,session_id=study_session.id)

    return render(request, 'hoos_study_app/study_session_dashboard.html', {
        'course': course,
        'course_id': course_id,
        'session_id': session_id,
        'study_session': study_session,
        'time_slots': time_slots,
        'data': data,
        'form': form,
        'pending_requests': pending_requests,
        'user_has_pending_request': user_has_pending_request
    })


@login_required
def delete_study_session(request, session_id):
    # Retrieve the study session
    session = get_object_or_404(StudySession, id=session_id)

    # Ensure the current user is the owner of the session
    if session.owner != request.user and not request.user.is_pma_admin:
        return HttpResponseForbidden("You are not allowed to delete this study session.")

    # Handle the delete request
    if request.method == 'POST':
        session.delete()
        messages.success(request, f"You have successfully deleted the study session.")
        return redirect('hoos_study_app:course_group', session.course_name.id)  # Redirect to the profile or other relevant page

    return redirect('hoos_study_app:study_session_dashboard', session.course_name.id, session.id)

@login_required
def pma_delete_study_session(request, session_id):
    # Retrieve the study session
    session = get_object_or_404(StudySession, id=session_id)

    # Ensure the current user is the owner of the session
    if not request.user.is_pma_admin and session.owner != request.user:
        return HttpResponseForbidden("You are not allowed to delete this study session.")

    # Handle the delete request
    if request.method == 'POST':
        session.delete()
        messages.success(request, f"You have successfully deleted the study session.")
        return redirect('hoos_study_app:pma-manage-study-sessions')

    return redirect('hoos_study_app:pma-manage-study-sessions')

@login_required
def manage_join_request(request, request_id, action):
    join_request = get_object_or_404(JoinRequest, id=request_id)

    # Ensure only the owner of the study session can manage requests
    if join_request.study_session.owner != request.user:
        return HttpResponseForbidden("You are not allowed to perform this action.")

    if action == 'accept':
        join_request.status = 'accepted'
        join_request.study_session.attendees.add(join_request.user)
        join_request.save()
        messages.success(request, f"{join_request.user.username} has been added to the session.")
    elif action == 'reject':
        join_request.delete()
        messages.success(request, f"{join_request.user.username}'s request has been rejected.")
    else:
        messages.error(request, "Invalid action.")
    
    return redirect('hoos_study_app:study_session_dashboard', join_request.study_session.course_name.id, join_request.study_session.id)

@login_required
def join_study_session(request, session_id):
    session = get_object_or_404(StudySession, id=session_id)

    # Check if a join request already exists
    if not JoinRequest.objects.filter(user=request.user, study_session=session).exists():
        JoinRequest.objects.create(user=request.user, study_session=session)
        messages.success(request, "Join request sent successfully.")
    else:
        messages.info(request, "You have already sent a request for this session.")

    return redirect('hoos_study_app:study_session_dashboard', session.course_name.id, session.id)

@login_required
def leave_study_session(request, session_id):
    session = get_object_or_404(StudySession, id=session_id)

    if request.method == 'POST':
        session.attendees.remove(request.user)

        join_request = JoinRequest.objects.filter(user=request.user, study_session=session).first()
        if join_request:
            join_request.delete()

        return redirect('hoos_study_app:study_session_dashboard', session.course_name.id, session.id) 

    return redirect('hoos_study_app:study_session_dashboard', session.course_name.id, session.id)

@login_required
def delete_document(request, pk, course_id=-1, session_id=-1):
    if course_id != -1:
        course = get_object_or_404(Course, id=course_id)
        session = get_object_or_404(StudySession, id=session_id)
        if request.method == "POST":
            document = models.Document.objects.get(pk=pk)
            document.delete()
            return redirect("hoos_study_app:study_session_dashboard", course_id, session.id)

    elif request.method == "POST":
        document = models.Document.objects.get(pk=pk)
        document.delete()

        if 'from_pma' in request.GET and request.GET['from_pma'] == 'true':
            # Redirect back to the PMA manage view
            return redirect("hoos_study_app:pma-manage-study-sessions")

        return redirect("hoos_study_app:documents")

# Message Board View
def message_board_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    board = get_object_or_404(MessageBoard, course=course)
    messages = board.messages.select_related('user').order_by('-timestamp')

    if request.method == 'POST':
        content = request.POST.get('content', '')
        is_anonymous = request.POST.get("is_anonymous") == "on" 

        if content:
            Message.objects.create(
                message_board=board,
                user=request.user,
                content=content,
                is_anonymous=is_anonymous,
            )
        return redirect('hoos_study_app:message_board', course_id=course_id)

    return render(request, 'hoos_study_app/message_board.html', {
        'course': course,
        'board_messages': messages,
        'current_user': request.user,
    })

@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    if message.user != request.user:
        raise PermissionDenied("You cannot delete someone else's message.")
    
    if request.method == "POST":
        message.delete()
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Invalid request"}, status=400)

def all_study_sessions(request):
    study_session_list = StudySession.objects.all()
    session_data = []
    time_slots = time_slot_list()

    for session in study_session_list:
        availabilities = StudySessionAvailability.objects.filter(session=session)
        # print(availabilities)
        #
        # availability_count = Counter()
        # for availability in availabilities:
        #
        #     for time_slot in availability.time_slots.split(","):
        #         availability_count[time_slot.strip()] += 1
        #
        #     # print("Avail Count: " + str(availability_count))
        #     #not working right currently
        #
        #     print("Avilability Count: " + str(availability_count))
        #
        #     best_slot = None
        #     best_slot_count = 0
        #
        #     if availability_count:
        #         for slot, count in availability_count.items():
        #             if count > best_slot_count:
        #                 best_slot = slot
        #                 best_slot_count = count

        session_data.append({'session': session, 'availabilities': availabilities,
                             # 'best_slot': best_slot, 'best_slot_count':best_slot_count
                             })

    return render(request, 'hoos_study_app/study_session_list.html',
                  {'session_data': session_data, 'time_slots': time_slots})

@login_required
def my_study_sessions(request):
    study_sessions = request.user.study_session.all()
    return render(request, 'hoos_study_app/my_study_sessions.html', {'study_sessions':study_sessions})

def add_location(request):
    submitted = False
    if request.method == "POST":
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(f"{reverse('hoos_study_app:add-location')}?submitted=True")

    else:
        form = LocationForm()
        if 'submitted' in request.GET:
            submitted = True

    return render(request, 'hoos_study_app/add_location.html', {'form': form, 'submitted': submitted})

@login_required
def create_study_session(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if hasattr(request.user, 'is_pma_admin') and request.user.is_pma_admin:
        return redirect('hoos_study_app:home')

    submitted = False
    study_session = None
    if request.method == "POST":
        form = StudySessionForm(request.POST, user=request.user)
        if form.is_valid():
            study_session = form.save(commit=False)
            study_session.owner = request.user
            study_session.course_name = course
            study_session.save()

            # Redirect to the course dashboard with a success flag
            print(reverse('hoos_study_app:course_group', kwargs={'pk': course.id}))

            return redirect(f"{reverse('hoos_study_app:course_group', kwargs={'pk': course.id})}?submitted=True")

    else:
        form = StudySessionForm(user=request.user)

    return render(request, 'hoos_study_app/create_study_session.html', {'form': form, 'submitted': submitted, 'session': study_session, 'course': course})


def create_time_choices():
    choices = []
    cur_time = datetime.strptime("08:00", "%H:%M")
    end_time = datetime.strptime("23:30", "%H:%M")
    while cur_time <= end_time:
        next_time = cur_time + timedelta(minutes=30)
        format_time_range = (cur_time.strftime("%I:%M %p") + " - " + next_time.strftime("%I:%M %p"))
        choices.append((format_time_range, format_time_range))
        cur_time = next_time

    return choices


def time_slot_list():
    choices = []
    cur_time = datetime.strptime("08:00", "%H:%M")
    end_time = datetime.strptime("23:30", "%H:%M")
    while cur_time <= end_time:
        next_time = cur_time + timedelta(minutes=30)

        choices.append(cur_time.strftime("%I:%M %p") + " - " + next_time.strftime("%I:%M %p"))
        cur_time = next_time

    return choices

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def give_availability(request, session_id):
    submitted = False
    session = get_object_or_404(StudySession, pk=session_id)
    # availabilities = StudySessionAvailability.objects.filter(session=session)
    course_id = session.course_name.id

    if request.method == 'POST':
        form = AvailabilityForm(request.POST, user=request.user)
        form.fields['time_slots'].choices = create_time_choices()
        if form.is_valid():
            availability = form.save(commit=False)
            if isinstance(availability.time_slots, list):
                availability.time_slots = ", ".join(availability.time_slots)
            availability.session = session
            availability.save()
            time.sleep(0.1)

            if request.user not in session.attendees.all():
                session.attendees.add(request.user)
                session.save()
                print(f"Added {request.user.username} as an attendee to the session: {session.name}")

            print(f"Saved availability for {availability.user_name} with time slots {availability.time_slots}")
        else:
            print("Form validation errors:", form.errors)

        return redirect(
            f"{reverse('hoos_study_app:give-availability', kwargs={'session_id': session.id})}?submitted=True&course_id={course_id}&session_id={session.id}"
            )

    else:
        form = AvailabilityForm(user=request.user)
        form.fields['time_slots'].choices = create_time_choices()
        if 'submitted' in request.GET:
            submitted = True

    availabilities = StudySessionAvailability.objects.filter(session=session).all()

    return render(request, 'hoos_study_app/availability.html', {'session': session,
                                                                'availabilities': availabilities,
                                                                'form': form, 'submitted': submitted, 'course_id': course_id,
                                                                })

# Helper function
def get_background_images():
    if settings.USE_S3:
        # Connect to S3
        s3 = boto3.resource('s3')
        # Access the bucket and get objects
        bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
        objects = bucket.objects.filter(Prefix=f'{settings.STATIC_LOCATION}/hoos_study_app/img/card_backgrounds/')

        images = [os.path.basename(obj.key) for obj in objects if not obj.key.endswith('/')]
        return images
    else:
        # Use local storage
        img_path = os.path.join(settings.STATICFILES_DIRS[0], 'hoos_study_app/img/card_backgrounds')
        images = os.listdir(img_path)
        return images

@login_required
def dashboard(request):
    # Retrieve courses associated with the logged-in user
    user_courses = request.user.courses.all()  # Access the many-to-many relationship

    images = get_background_images()

    courses_with_data = []
    for course in user_courses:
        preference = UserCoursePreference.objects.get(user=request.user, course=course)
        other_students = course.students.exclude(id=request.user.id) # For profile pictures displayed on cards

        courses_with_data.append((course, preference.background_image, other_students))

    return render(request, 'hoos_study_app/dashboard.html', {
        'courses': courses_with_data,
        'images': images
    })

@login_required
def change_background(request):
    if request.method == "POST":
        course_id = request.POST.get("course_id")
        image = request.POST.get("background_image")

        course = request.user.courses.filter(id=course_id).first()
        if course and image:
            preference, created = UserCoursePreference.objects.get_or_create(user=request.user, course=course)
            preference.background_image = image
            preference.save()

    return redirect('hoos_study_app:dashboard')  # Redirect back to the dashboard

def anon_list_study_sessions(request):
    study_sessions = StudySession.objects.all()
    return render(request, 'hoos_study_app/anon_study_sessions_list.html', {'study_sessions': study_sessions})

def pma_manage_study_sessions(request):
    study_sessions = StudySession.objects.all()
    return render(request, 'hoos_study_app/pma_manage_study_sessions.html', {'study_sessions': study_sessions})

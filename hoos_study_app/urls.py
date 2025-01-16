from django.urls import path

from . import views

app_name = "hoos_study_app"

urlpatterns = [
    path("", views.home, name="home"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile, name="profile"),
    path("classes/", views.ClassesView.as_view(), name="class-list"),

    path("all-study-session-preview/", views.anon_list_study_sessions, name="all-study-sessions-preview"),

    path("pma-manage-study-sessions/", views.pma_manage_study_sessions, name="pma-manage-study-sessions"),
    path("pma-manage-study-sessions/<int:session_id>/delete", views.pma_delete_study_session, name='pma_delete_study_session'),

    path("documents/upload/", views.upload_file, name="upload"),
    path("documents/", views.DocumentsListView.as_view(), name="documents"),
    path("documents/<int:pk>", views.delete_document, name="delete_document"),
    path('course/<int:course_id>/<int:session_id>/upload/', views.upload_file_study_session, name='upload_file_study_session'),
    path("course/<int:course_id>/<int:session_id>", views.study_session_dashboard, name='study_session_dashboard'),
    path("course/<int:pk>/<int:course_id>/<int:session_id>", views.delete_document, name='delete_document'),
    path("study-session/<int:session_id>/delete/", views.delete_study_session, name='delete_study_session'),
    path("study-session/<int:session_id>/join/", views.join_study_session, name='join_study_session'),
    path("study-session/<int:session_id>/leave/", views.leave_study_session, name='leave_study_session'),

    path('course/<int:course_id>/create-study-session/', views.create_study_session, name='create-study-session'),
    path('join-study-session/<int:session_id>/', views.join_study_session, name='join_study_session'),
    path('manage-join-request/<int:request_id>/<str:action>/', views.manage_join_request, name='manage_join_request'),


    # path("course/<int:course_id>/message_board", views.message_board_view, name="course_group"),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('change-background/', views.change_background, name='change_background'),

    path("study-session/", views.all_study_sessions, name='all-study-sessions'),
    path('add-location/', views.add_location, name='add-location'),
    # path('create-study-session/', views.create_study_session, name='create-study-session'),
    path("availability/<int:session_id>", views.give_availability, name='give-availability'),
    path("my-study-sessions", views.my_study_sessions, name='my-study-sessions'),
    path('message/delete/<int:message_id>/', views.delete_message, name='delete_message'),

    path('course/<int:pk>/', views.CourseGroupView.as_view(), name='course_group'),
    path('course/<int:course_id>/join/', views.join_course_group, name='join_course_group'),
    path('course/<int:course_id>/leave/', views.leave_course_group, name='leave_course_group')
]
from django.urls import path
from . import views

urlpatterns = [
    # User
    path('users/me/', views.UserProfileView.as_view(), name='user-profile'),
    
    # Courses
    path('courses/', views.CourseListView.as_view(), name='course-list'),
    path('courses/<slug:slug>/', views.CourseDetailView.as_view(), name='course-detail'),
    path('courses/<slug:slug>/modules/', views.CourseModuleListView.as_view(), name='course-modules'),
    path('courses/<slug:slug>/enroll/', views.enroll_in_course, name='course-enroll'),
    
    # Modules
    path('modules/<int:module_id>/lessons/', views.ModuleLessonListView.as_view(), name='module-lessons'),
    
    # Enrollments
    path('enrollments/', views.EnrollmentListView.as_view(), name='enrollment-list'),
    path('enrollments/<int:enrollment_id>/progress/', views.EnrollmentProgressView.as_view(), name='enrollment-progress'),
    path('enrollments/<int:enrollment_id>/lessons/<int:lesson_id>/complete/', views.complete_lesson, name='complete-lesson'),
]
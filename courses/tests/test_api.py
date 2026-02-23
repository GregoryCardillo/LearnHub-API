import pytest
from django.urls import reverse
from rest_framework import status
from courses.models import Course, Enrollment, Progress
from .factories import (
    StudentFactory,
    InstructorFactory,
    CourseFactory,
    ModuleFactory,
    LessonFactory,
)


@pytest.mark.django_db
class TestAuthenticationAPI:
    """Tests for authentication endpoints."""
    
    def test_register_student(self, api_client):
        """Test user registration."""
        url = reverse('auth-register')
        data = {
            'email': 'newstudent@test.com',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'student'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'tokens' in response.data
        assert response.data['user']['email'] == 'newstudent@test.com'
    
    def test_login(self, api_client, student):
        """Test user login."""
        url = reverse('auth-login')
        data = {
            'email': student.email,
            'password': 'testpass123'  # From factory
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']
    
    def test_login_invalid_credentials(self, api_client):
        """Test login with invalid credentials."""
        url = reverse('auth-login')
        data = {
            'email': 'notexist@test.com',
            'password': 'wrongpass'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCourseAPI:
    """Tests for course endpoints."""
    
    def test_list_courses_unauthenticated(self, api_client):
        """Test listing courses without authentication."""
        CourseFactory.create_batch(3, status='published')
        
        url = reverse('course-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3
    
    def test_list_courses_filters_published_only(self, api_client):
        """Test that only published courses are returned."""
        CourseFactory(status='published')
        CourseFactory(status='draft')
        CourseFactory(status='archived')
        
        url = reverse('course-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
    
    def test_create_course_as_instructor(self, instructor_client):
        """Test creating a course as instructor."""
        url = reverse('course-list')
        data = {
            'title': 'New Django Course',
            'slug': 'new-django-course',
            'description': 'Learn Django',
            'level': 'beginner',
            'status': 'draft',
            'price': '49.99'
        }
        
        response = instructor_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Course.objects.filter(title='New Django Course').exists()
    
    def test_create_course_as_student_forbidden(self, authenticated_client):
        """Test that students cannot create courses."""
        url = reverse('course-list')
        data = {
            'title': 'Unauthorized Course',
            'slug': 'unauthorized-course',
            'description': 'Test',
            'level': 'beginner',
            'status': 'draft',
            'price': '50.00'
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_retrieve_course_detail(self, api_client, course):
        """Test retrieving course details."""
        url = reverse('course-detail', kwargs={'slug': course.slug})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == course.title
        assert 'modules' in response.data
        assert len(response.data['modules']) == 2
    
    def test_update_course_as_owner(self, instructor_client, instructor):
        """Test updating course as the owner."""
        course = CourseFactory(instructor=instructor)
        
        url = reverse('course-detail', kwargs={'slug': course.slug})
        data = {
            'title': 'Updated Title',
            'slug': course.slug,
            'description': course.description,
            'level': 'advanced',
            'status': 'published',
            'price': '99.99'
        }
        
        response = instructor_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        course.refresh_from_db()
        assert course.level == 'advanced'
    
    def test_update_course_as_non_owner_forbidden(self, instructor_client):
        """Test that non-owners cannot update courses."""
        other_instructor = InstructorFactory()
        course = CourseFactory(instructor=other_instructor)
        
        url = reverse('course-detail', kwargs={'slug': course.slug})
        data = {
            'title': 'Hacked Title',
            'slug': course.slug,
            'description': 'Test',
            'level': 'beginner',
            'status': 'published',
            'price': '50.00'
        }
        
        response = instructor_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_course_as_owner(self, instructor_client, instructor):
        """Test deleting course as the owner."""
        course = CourseFactory(instructor=instructor)
        
        url = reverse('course-detail', kwargs={'slug': course.slug})
        response = instructor_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Course.objects.filter(id=course.id).exists()


@pytest.mark.django_db
class TestEnrollmentAPI:
    """Tests for enrollment endpoints."""
    
    def test_enroll_in_course(self, authenticated_client, student, course):
        """Test enrolling in a course."""
        url = reverse('course-enroll', kwargs={'slug': course.slug})
        response = authenticated_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Enrollment.objects.filter(student=student, course=course).exists()
    
    def test_enroll_creates_progress_records(self, authenticated_client, student, course):
        """Test that enrolling creates progress records via signal."""
        url = reverse('course-enroll', kwargs={'slug': course.slug})
        response = authenticated_client.post(url, {}, format='json')
        
        enrollment = Enrollment.objects.get(student=student, course=course)
        progress_count = enrollment.progress_records.count()
        
        assert progress_count == course.total_lessons
    
    def test_enroll_twice_fails(self, authenticated_client, student, course):
        """Test that enrolling twice in same course fails."""
        url = reverse('course-enroll', kwargs={'slug': course.slug})
        
        # First enrollment
        authenticated_client.post(url, {}, format='json')
        
        # Second enrollment attempt
        response = authenticated_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_instructor_cannot_enroll(self, instructor_client, course):
        """Test that instructors cannot enroll in courses."""
        url = reverse('course-enroll', kwargs={'slug': course.slug})
        response = instructor_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_list_user_enrollments(self, authenticated_client, student):
        """Test listing user's enrollments."""
        course1 = CourseFactory()
        course2 = CourseFactory()
        
        enrollment1 = Enrollment.objects.create(student=student, course=course1)
        enrollment2 = Enrollment.objects.create(student=student, course=course2)
        
        url = reverse('enrollment-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2
    
    def test_student_dashboard(self, authenticated_client, student, course):
        """Test student dashboard endpoint."""
        # Create enrollment with some progress
        enrollment = Enrollment.objects.create(student=student, course=course)
        progress = enrollment.progress_records.first()
        progress.mark_complete()
        
        url = reverse('student-dashboard')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'stats' in response.data
        assert response.data['stats']['total_courses'] == 1
        assert response.data['stats']['total_lessons_completed'] == 1


@pytest.mark.django_db
class TestProgressAPI:
    """Tests for progress tracking endpoints."""
    
    def test_complete_lesson(self, authenticated_client, student, course):
        """Test completing a lesson."""
        enrollment = Enrollment.objects.create(student=student, course=course)
        lesson = course.modules.first().lessons.first()
        
        url = reverse('complete-lesson', kwargs={
            'enrollment_id': enrollment.id,
            'lesson_id': lesson.id
        })
        
        response = authenticated_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        progress = Progress.objects.get(enrollment=enrollment, lesson=lesson)
        assert progress.completed is True
    
    def test_complete_lesson_updates_percentage(self, authenticated_client, student, course):
        """Test that completing lesson updates progress percentage."""
        enrollment = Enrollment.objects.create(student=student, course=course)
        lesson = course.modules.first().lessons.first()
        
        url = reverse('complete-lesson', kwargs={
            'enrollment_id': enrollment.id,
            'lesson_id': lesson.id
        })
        
        response = authenticated_client.post(url, {}, format='json')
        
        enrollment.refresh_from_db()
        expected_percentage = round((1 / course.total_lessons) * 100, 2)
        assert enrollment.progress_percentage == expected_percentage
    
    def test_reset_lesson_progress(self, authenticated_client, student, course):
        """Test resetting lesson progress."""
        enrollment = Enrollment.objects.create(student=student, course=course)
        lesson = course.modules.first().lessons.first()
        
        # First complete the lesson
        progress = Progress.objects.get(enrollment=enrollment, lesson=lesson)
        progress.mark_complete()
        
        # Then reset it
        url = reverse('reset-lesson', kwargs={
            'enrollment_id': enrollment.id,
            'lesson_id': lesson.id
        })
        
        response = authenticated_client.post(url, {}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        progress.refresh_from_db()
        assert progress.completed is False
        assert progress.completed_at is None
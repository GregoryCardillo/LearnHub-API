from rest_framework import generics, status, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .filters import CourseFilter, EnrollmentFilter


from .models import Course, Module, Lesson, Enrollment, Progress
from .serializers import (
    CourseListSerializer,
    CourseDetailSerializer,
    CourseWriteSerializer,
    ModuleSerializer,
    LessonSerializer,
    EnrollmentSerializer,
    EnrollmentDetailSerializer,  
    ProgressSerializer,
    UserProfileSerializer,
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
)

from .permissions import (
    IsInstructor,
    IsStudent,
    IsOwnerOrReadOnly,
    IsCourseInstructor,
    IsEnrolled,
    IsEnrolledOrFree,
    IsEnrollmentOwner,
    CanCreateCourse,
)

# ============================================
# USER VIEWS
# ============================================

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/users/me/  → Get current user profile
    PUT  /api/users/me/  → Update current user profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Return the current authenticated user."""
        return self.request.user


# ============================================
# COURSE VIEWS
# ============================================

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .filters import CourseFilter, EnrollmentFilter

class CourseListView(generics.ListCreateAPIView):
    """
    GET  /api/courses/  → List all published courses
    POST /api/courses/  → Create a new course (instructors only)
    
    Supports:
    - Filtering: ?level=beginner&min_price=0&max_price=50&is_free=true
    - Search: ?search=python
    - Ordering: ?ordering=-created_at (newest first)
    """
    permission_classes = [CanCreateCourse]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CourseFilter
    search_fields = ['title', 'description', 'instructor__first_name', 'instructor__last_name']
    ordering_fields = ['created_at', 'price', 'title']
    ordering = ['-created_at']  # Default ordering
    
    def get_queryset(self):
        """Return published courses with optimized queries."""
        return Course.objects.filter(
            status='published'
        ).select_related(
            'instructor'
        ).prefetch_related(
            'modules__lessons',
            'enrollments'
        )
    
    def get_serializer_class(self):
        """Use different serializers for read and write operations."""
        if self.request.method == 'POST':
            return CourseWriteSerializer
        return CourseListSerializer


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/courses/{slug}/  → Get course details
    PUT    /api/courses/{slug}/  → Update course (owner only)
    DELETE /api/courses/{slug}/  → Delete course (owner only)
    """
    permission_classes = [IsAuthenticatedOrReadOnly, IsCourseInstructor]
    lookup_field = 'slug'
    
    def get_queryset(self):
        return Course.objects.select_related(
            'instructor'
        ).prefetch_related(
            'modules__lessons',
            'enrollments'
        )
    
    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return CourseWriteSerializer
        return CourseDetailSerializer
    
    def get_serializer_context(self):
        """Pass request to serializer for is_enrolled check."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


# ============================================
# MODULE VIEWS
# ============================================

class CourseModuleListView(generics.ListAPIView):
    """
    GET /api/courses/{slug}/modules/  → List all modules in a course
    """
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Get modules for a specific course."""
        course = get_object_or_404(Course, slug=self.kwargs['slug'])
        return Module.objects.filter(
            course=course
        ).prefetch_related('lessons')


# ============================================
# LESSON VIEWS
# ============================================

class ModuleLessonListView(generics.ListAPIView):
    """
    GET /api/modules/{module_id}/lessons/  → List all lessons in a module
    """
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        """Get lessons for a specific module."""
        module = get_object_or_404(Module, id=self.kwargs['module_id'])
        return Lesson.objects.filter(module=module)


# ============================================
# ENROLLMENT VIEWS
# ============================================

class EnrollmentListView(generics.ListAPIView):
    """
    GET /api/enrollments/  → List current user's enrollments
    
    Supports:
    - Filtering: ?is_completed=false&is_active=true&progress_min=50
    - Ordering: ?ordering=-enrolled_at
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, IsStudent]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = EnrollmentFilter
    ordering_fields = ['enrolled_at', 'completed_at']
    ordering = ['-enrolled_at']
    
    def get_queryset(self):
        """
        Return only the current user's enrollments.
        Optimized with select_related and prefetch_related.
        """
        from django.db.models import Count, Q, Case, When, FloatField, F, Value
        from django.db.models.functions import Cast
        
        return Enrollment.objects.filter(
            student=self.request.user,
            is_active=True
        ).select_related(
            'course__instructor'
        ).prefetch_related(
            'progress_records'
        ).annotate(
            # Pre-calculate progress for better performance
            total_progress=Count('progress_records', distinct=True),
            completed_progress=Count(
                'progress_records',
                filter=Q(progress_records__completed=True),
                distinct=True
            )
        )



@api_view(['POST'])
def enroll_in_course(request, slug):
    """
    POST /api/courses/{slug}/enroll/  → Enroll in a course
    """
    if not request.user.is_authenticated:
        return Response(
            {'error': 'Authentication required.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not request.user.is_student:
        return Response(
            {'error': 'Only students can enroll in courses.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    course = get_object_or_404(Course, slug=slug, status='published')
    
    # Check if already enrolled
    if Enrollment.objects.filter(student=request.user, course=course).exists():
        return Response(
            {'error': 'You are already enrolled in this course.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create enrollment (signal will create Progress records automatically)
    enrollment = Enrollment.objects.create(
        student=request.user,
        course=course
    )
    
    serializer = EnrollmentSerializer(enrollment)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


# ============================================
# PROGRESS VIEWS
# ============================================

class EnrollmentProgressView(generics.ListAPIView):
    """
    GET /api/enrollments/{enrollment_id}/progress/  → Get progress for an enrollment
    """
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated, IsEnrollmentOwner]
    
    def get_queryset(self):
        """Get progress records for a specific enrollment."""
        enrollment = get_object_or_404(
            Enrollment,
            id=self.kwargs['enrollment_id'],
            student=self.request.user  # Ensure ownership
        )
        return Progress.objects.filter(
            enrollment=enrollment
        ).select_related('lesson__module')


@api_view(['POST'])
def complete_lesson(request, enrollment_id, lesson_id):
    """
    POST /api/enrollments/{enrollment_id}/lessons/{lesson_id}/complete/
    → Mark a lesson as completed
    """
    enrollment = get_object_or_404(
        Enrollment,
        id=enrollment_id,
        student=request.user
    )
    
    progress = get_object_or_404(
        Progress,
        enrollment=enrollment,
        lesson_id=lesson_id
    )
    
    progress.mark_complete()
    
    serializer = ProgressSerializer(progress)
    return Response({
        'message': 'Lesson marked as completed!',
        'progress': serializer.data,
        'course_progress': f"{enrollment.progress_percentage}%"
    })

# ============================================
# AUTHENTICATION VIEWS
# ============================================

class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/  → Register a new user
    """
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens for the new user
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Registration successful!'
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """
    POST /api/auth/login/  → Login and get tokens
    """
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Login successful!'
        })


class LogoutView(generics.GenericAPIView):
    """
    POST /api/auth/logout/  → Logout (blacklist refresh token)
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'message': 'Logout successful!'
            }, status=status.HTTP_205_RESET_CONTENT)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ChangePasswordView(generics.UpdateAPIView):
    """
    PUT /api/auth/change-password/  → Change user password
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = self.get_object()
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': 'Password changed successfully!'
        })


@api_view(['GET'])
def verify_token(request):
    """
    GET /api/auth/verify/  → Verify if token is valid
    """
    if request.user.is_authenticated:
        return Response({
            'valid': True,
            'user': UserProfileSerializer(request.user).data
        })
    return Response({
        'valid': False,
        'error': 'Invalid or expired token.'
    }, status=status.HTTP_401_UNAUTHORIZED)


# ============================================
# INSTRUCTOR VIEWS
# ============================================

class InstructorCourseListView(generics.ListAPIView):
    """
    GET /api/instructor/courses/  → List courses created by the current instructor
    
    Supports:
    - Filtering: ?status=published
    - Ordering: ?ordering=-created_at
    """
    serializer_class = CourseListSerializer
    permission_classes = [IsAuthenticated, IsInstructor]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'level']
    ordering_fields = ['created_at', 'title', 'price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return only courses created by the current instructor."""
        return Course.objects.filter(
            instructor=self.request.user
        ).select_related(
            'instructor'
        ).prefetch_related(
            'modules__lessons',
            'enrollments'
        )


class CourseStudentsView(generics.ListAPIView):
    """
    GET /api/courses/{slug}/students/  → List students enrolled in a course (instructor only)
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, IsInstructor]
    
    def get_queryset(self):
        """Get students enrolled in the instructor's course."""
        from .models import Enrollment
        
        course = get_object_or_404(
            Course,
            slug=self.kwargs['slug'],
            instructor=self.request.user  # Ensure ownership
        )
        
        return Enrollment.objects.filter(
            course=course,
            is_active=True
        ).select_related(
            'student',
            'course'
        ).prefetch_related(
            'progress_records'
        )


class ModuleCreateView(generics.CreateAPIView):
    """
    POST /api/courses/{slug}/modules/create/  → Create a module in a course
    """
    from .serializers import ModuleSerializer
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated, IsInstructor]
    
    def perform_create(self, serializer):
        """Automatically assign course from URL."""
        course = get_object_or_404(
            Course,
            slug=self.kwargs['slug'],
            instructor=self.request.user  # Ensure ownership
        )
        serializer.save(course=course)


class LessonCreateView(generics.CreateAPIView):
    """
    POST /api/modules/{module_id}/lessons/create/  → Create a lesson in a module
    """
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsInstructor]
    
    def perform_create(self, serializer):
        """Automatically assign module from URL."""
        module = get_object_or_404(Module, id=self.kwargs['module_id'])
        
        # Check if user is the course instructor
        if module.course.instructor != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only add lessons to your own courses.")
        
        serializer.save(module=module)

# ============================================
# STUDENT DASHBOARD VIEWS
# ============================================

class StudentDashboardView(generics.GenericAPIView):
    """
    GET /api/student/dashboard/  → Get student dashboard with stats
    """
    permission_classes = [IsAuthenticated, IsStudent]
    
    def get(self, request):
        """Return student statistics and enrollments."""
        student = request.user
        
        # Get all enrollments
        enrollments = Enrollment.objects.filter(
            student=student,
            is_active=True
        ).select_related('course__instructor').prefetch_related('progress_records')
        
        # Separate active and completed
        active_enrollments = enrollments.filter(completed_at__isnull=True)
        completed_enrollments = enrollments.filter(completed_at__isnull=False)
        
        # Calculate overall stats
        total_courses = enrollments.count()
        completed_courses = completed_enrollments.count()
        total_lessons_completed = sum(
            e.get_completed_lessons_count() for e in enrollments
        )
        total_time_spent = sum(
            e.get_total_time_spent() for e in enrollments
        )
        
        # Serialize enrollments
        active_data = EnrollmentSerializer(active_enrollments, many=True).data
        completed_data = EnrollmentSerializer(completed_enrollments, many=True).data
        
        return Response({
            'stats': {
                'total_courses': total_courses,
                'active_courses': active_enrollments.count(),
                'completed_courses': completed_courses,
                'total_lessons_completed': total_lessons_completed,
                'total_time_spent_minutes': total_time_spent,
                'total_time_spent_hours': round(total_time_spent / 60, 1)
            },
            'active_enrollments': active_data,
            'completed_enrollments': completed_data
        })


class EnrollmentDetailView(generics.RetrieveAPIView):
    """
    GET /api/enrollments/{id}/  → Get detailed enrollment info
    """
    serializer_class = EnrollmentDetailSerializer
    permission_classes = [IsAuthenticated, IsEnrollmentOwner]
    
    def get_queryset(self):
        return Enrollment.objects.filter(
            student=self.request.user
        ).select_related(
            'course__instructor'
        ).prefetch_related(
            'course__modules__lessons',
            'progress_records__lesson__module'
        )


@api_view(['POST'])
def unenroll_from_course(request, enrollment_id):
    """
    POST /api/enrollments/{enrollment_id}/unenroll/  → Unenroll from a course
    """
    enrollment = get_object_or_404(
        Enrollment,
        id=enrollment_id,
        student=request.user,
        is_active=True
    )
    
    # Don't allow unenrollment if course is completed
    if enrollment.is_completed:
        return Response(
            {'error': 'Cannot unenroll from a completed course.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Deactivate enrollment instead of deleting (keep history)
    enrollment.is_active = False
    enrollment.save()
    
    return Response({
        'message': 'Successfully unenrolled from the course.',
        'enrollment_id': enrollment.id
    })


@api_view(['GET'])
def enrollment_certificate(request, enrollment_id):
    """
    GET /api/enrollments/{enrollment_id}/certificate/  → Get certificate info
    """
    enrollment = get_object_or_404(
        Enrollment,
        id=enrollment_id,
        student=request.user
    )
    
    if not enrollment.is_completed:
        return Response(
            {'error': 'Course must be completed to receive a certificate.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Generate certificate data
    certificate_data = {
        'student_name': request.user.get_full_name() or request.user.email,
        'course_title': enrollment.course.title,
        'instructor_name': enrollment.course.instructor.get_full_name(),
        'completion_date': enrollment.completed_at.strftime('%B %d, %Y'),
        'enrollment_id': enrollment.id,
        'certificate_number': f"CERT-{enrollment.id:06d}",
        'total_lessons': enrollment.course.total_lessons,
        'total_duration': enrollment.course.total_duration
    }
    
    return Response({
        'message': 'Certificate generated successfully!',
        'certificate': certificate_data
    })


# ============================================
# PROGRESS TRACKING VIEWS
# ============================================

@api_view(['POST'])
def reset_lesson_progress(request, enrollment_id, lesson_id):
    """
    POST /api/enrollments/{enrollment_id}/lessons/{lesson_id}/reset/
    → Reset a lesson to incomplete
    """
    enrollment = get_object_or_404(
        Enrollment,
        id=enrollment_id,
        student=request.user
    )
    
    progress = get_object_or_404(
        Progress,
        enrollment=enrollment,
        lesson_id=lesson_id
    )
    
    progress.completed = False
    progress.completed_at = None
    progress.save()
    
    # Update enrollment completion status if needed
    if enrollment.completed_at:
        enrollment.completed_at = None
        enrollment.save()
    
    return Response({
        'message': 'Lesson progress reset successfully!',
        'progress': ProgressSerializer(progress).data,
        'course_progress': f"{enrollment.progress_percentage}%"
    })


class CourseProgressSummaryView(generics.GenericAPIView):
    """
    GET /api/courses/{slug}/progress/  → Get progress summary for enrolled course
    """
    permission_classes = [IsAuthenticated, IsStudent]
    
    def get(self, request, slug):
        """Get detailed progress for a course."""
        course = get_object_or_404(Course, slug=slug)
        
        enrollment = get_object_or_404(
            Enrollment,
            student=request.user,
            course=course,
            is_active=True
        )
        
        # Get progress grouped by module
        modules_progress = []
        
        for module in course.modules.all().prefetch_related('lessons'):
            lessons_in_module = module.lessons.all()
            progress_records = Progress.objects.filter(
                enrollment=enrollment,
                lesson__in=lessons_in_module
            ).select_related('lesson')
            
            completed_count = progress_records.filter(completed=True).count()
            total_count = lessons_in_module.count()
            percentage = (completed_count / total_count * 100) if total_count > 0 else 0
            
            modules_progress.append({
                'module_id': module.id,
                'module_title': module.title,
                'total_lessons': total_count,
                'completed_lessons': completed_count,
                'progress_percentage': round(percentage, 2),
                'lessons': [{
                    'id': p.lesson.id,
                    'title': p.lesson.title,
                    'completed': p.completed,
                    'completed_at': p.completed_at.isoformat() if p.completed_at else None,
                    'order': p.lesson.order
                } for p in progress_records]
            })
        
        return Response({
            'enrollment': EnrollmentDetailSerializer(enrollment).data,
            'modules_progress': modules_progress
        })
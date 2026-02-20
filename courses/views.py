from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.shortcuts import get_object_or_404

from .models import Course, Module, Lesson, Enrollment, Progress
from .serializers import (
    CourseListSerializer,
    CourseDetailSerializer,
    CourseWriteSerializer,
    ModuleSerializer,
    LessonSerializer,
    EnrollmentSerializer,
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

class CourseListView(generics.ListCreateAPIView):
    """
    GET  /api/courses/  → List all published courses
    POST /api/courses/  → Create a new course (instructors only)
    """
    permission_classes = [CanCreateCourse]
    
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
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated, IsStudent]
    
    def get_queryset(self):
        """Return only the current user's enrollments."""
        return Enrollment.objects.filter(
            student=self.request.user,
            is_active=True
        ).select_related(
            'course__instructor'
        ).prefetch_related(
            'progress_records'
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


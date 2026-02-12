from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Course, Module, Lesson, Enrollment, Progress


# ============================================
# CUSTOM FILTERS
# ============================================

class EnrollmentStatusFilter(admin.SimpleListFilter):
    """Custom filter for enrollment completion status."""
    title = 'completion status'
    parameter_name = 'completion'
    
    def lookups(self, request, model_admin):
        return (
            ('completed', 'Completed'),
            ('in_progress', 'In Progress'),
            ('not_started', 'Not Started'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'completed':
            return queryset.filter(completed_at__isnull=False)
        if self.value() == 'in_progress':
            return queryset.filter(
                completed_at__isnull=True,
                progress_records__completed=True
            ).distinct()
        if self.value() == 'not_started':
            return queryset.exclude(
                progress_records__completed=True
            ).distinct()


# ============================================
# USER ADMIN
# ============================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for User model."""
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'role', 'bio', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_staff', 'is_active')}
        ),
    )


# ============================================
# INLINE ADMINS
# ============================================

class ModuleInline(admin.TabularInline):
    """Inline admin to manage modules directly from course page."""
    model = Module
    extra = 1
    fields = ('title', 'order', 'description')


class LessonInline(admin.TabularInline):
    """Inline admin to manage lessons directly from module page."""
    model = Lesson
    extra = 1
    fields = ('title', 'content_type', 'order', 'duration_minutes', 'is_free')


class ProgressInline(admin.TabularInline):
    """Inline to show progress records within enrollment."""
    model = Progress
    extra = 0
    readonly_fields = ('lesson', 'completed', 'completed_at', 'last_accessed')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


# ============================================
# COURSE ADMIN
# ============================================

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'instructor_name', 
        'level', 
        'status',
        'status_badge', 
        'price', 
        'total_enrollments',
        'created_at'
    )
    list_filter = ('level', 'status', 'created_at', 'instructor')
    search_fields = ('title', 'description', 'instructor__email', 'instructor__first_name', 'instructor__last_name')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at', 'total_enrollments', 'total_revenue')
    inlines = [ModuleInline]
    list_per_page = 20
    date_hierarchy = 'created_at'
    list_editable = ('status',)
    
    actions = ['make_published', 'make_draft', 'make_archived']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'instructor', 'thumbnail')
        }),
        ('Course Details', {
            'fields': ('level', 'status', 'price')
        }),
        ('Statistics', {
            'fields': ('total_enrollments', 'total_revenue'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related('instructor')
        qs = qs.prefetch_related('enrollments')
        return qs
    
    @admin.display(description='Instructor', ordering='instructor__email')
    def instructor_name(self, obj):
        full_name = obj.instructor.get_full_name()
        if full_name:
            return f"{full_name} ({obj.instructor.email})"
        return obj.instructor.email
    
    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'published': 'green',
            'archived': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="padding: 3px 10px; background-color: {}; color: white; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    
    @admin.display(description='Enrollments')
    def total_enrollments(self, obj):
        count = obj.enrollments.count()
        if count > 0:
            url = f"/admin/courses/enrollment/?course__id__exact={obj.id}"
            return format_html('<a href="{}">{} students</a>', url, count)
        return "0 students"
    
    @admin.display(description='Revenue')
    def total_revenue(self, obj):
        count = obj.enrollments.filter(is_active=True).count()
        revenue = count * obj.price
        return f"€{revenue:,.2f}"
    
    @admin.action(description='Mark selected courses as Published')
    def make_published(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} courses marked as published.')
    
    @admin.action(description='Mark selected courses as Draft')
    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} courses marked as draft.')
    
    @admin.action(description='Mark selected courses as Archived')
    def make_archived(self, request, queryset):
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} courses archived.')


# ============================================
# MODULE ADMIN
# ============================================

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'total_lessons', 'created_at')
    list_filter = ('course', 'created_at')
    search_fields = ('title', 'description', 'course__title')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [LessonInline]
    
    fieldsets = (
        (None, {
            'fields': ('course', 'title', 'description', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================
# LESSON ADMIN
# ============================================

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'content_type', 'duration_minutes', 'order', 'is_free')
    list_filter = ('content_type', 'is_free', 'created_at')
    search_fields = ('title', 'content', 'module__title')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('module', 'title', 'content_type', 'order')
        }),
        ('Content', {
            'fields': ('content', 'video_url', 'attachments', 'duration_minutes', 'is_free')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================
# ENROLLMENT ADMIN
# ============================================

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        'student_info',
        'course_title',
        'enrolled_at',
        'progress_bar',
        'completion_status',
        'is_active'
    )
    list_filter = ('is_active', EnrollmentStatusFilter, 'enrolled_at', 'completed_at', 'course__level')
    search_fields = (
        'student__email',
        'student__first_name',
        'student__last_name',
        'course__title'
    )
    readonly_fields = ('enrolled_at', 'progress_percentage', 'is_completed', 'progress_bar_detail')
    inlines = [ProgressInline]
    list_per_page = 25
    date_hierarchy = 'enrolled_at'
    
    actions = ['mark_as_completed', 'activate_enrollments', 'deactivate_enrollments']
    
    fieldsets = (
        ('Enrollment Details', {
            'fields': ('student', 'course', 'is_active')
        }),
        ('Progress Tracking', {
            'fields': ('enrolled_at', 'completed_at', 'progress_bar_detail')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('student', 'course').prefetch_related('progress_records')
    
    @admin.display(description='Student', ordering='student__email')
    def student_info(self, obj):
        full_name = obj.student.get_full_name()
        if full_name:
            return f"{full_name}"
        return obj.student.email
    
    @admin.display(description='Course', ordering='course__title')
    def course_title(self, obj):
        url = f"/admin/courses/course/{obj.course.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.course.title)
    
    @admin.display(description='Progress')
    def progress_bar(self, obj):
        percentage = obj.progress_percentage
        color = '#28a745' if percentage == 100 else '#007bff' if percentage >= 50 else '#ffc107'
        return format_html(
            '<div style="width:100px; background-color:#e9ecef; border-radius:3px;">'
            '<div style="width:{}%; background-color:{}; color:white; text-align:center; border-radius:3px; padding:2px 0;">'
            '{}%'
            '</div></div>',
            percentage, color, percentage
        )
    
    @admin.display(description='Detailed Progress')
    def progress_bar_detail(self, obj):
        percentage = obj.progress_percentage
        total = obj.course.total_lessons
        completed = obj.progress_records.filter(completed=True).count()
        
        color = '#28a745' if percentage == 100 else '#007bff' if percentage >= 50 else '#ffc107'
        return format_html(
            '<div style="margin: 10px 0;">'
            '<div style="width:300px; background-color:#e9ecef; border-radius:5px; overflow:hidden;">'
            '<div style="width:{}%; background-color:{}; color:white; text-align:center; padding:5px 0; transition: width 0.3s;">'
            '{}%'
            '</div></div>'
            '<small>{} of {} lessons completed</small>'
            '</div>',
            percentage, color, percentage, completed, total
        )
    
    @admin.display(description='Status', boolean=True)
    def completion_status(self, obj):
        return obj.is_completed
    
    @admin.action(description='Mark selected enrollments as completed')
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        count = 0
        for enrollment in queryset:
            enrollment.progress_records.update(
                completed=True,
                completed_at=timezone.now()
            )
            enrollment.completed_at = timezone.now()
            enrollment.save()
            count += 1
        self.message_user(request, f'{count} enrollments marked as completed.')
    
    @admin.action(description='Activate selected enrollments')
    def activate_enrollments(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} enrollments activated.')
    
    @admin.action(description='Deactivate selected enrollments')
    def deactivate_enrollments(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} enrollments deactivated.')


# ============================================
# PROGRESS ADMIN
# ============================================

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = (
        'student_name',
        'course_name',
        'lesson_title',
        'completion_icon',
        'completed_at',
        'last_accessed'
    )
    list_filter = ('completed', 'completed_at', 'enrollment__course')
    search_fields = (
        'enrollment__student__email',
        'enrollment__student__first_name',
        'enrollment__student__last_name',
        'lesson__title',
        'enrollment__course__title'
    )
    readonly_fields = ('completed_at', 'last_accessed')
    list_per_page = 50
    
    actions = ['mark_as_completed', 'mark_as_incomplete']
    
    fieldsets = (
        ('Progress Details', {
            'fields': ('enrollment', 'lesson', 'completed')
        }),
        ('Timestamps', {
            'fields': ('completed_at', 'last_accessed')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'enrollment__student',
            'enrollment__course',
            'lesson__module'
        )
    
    @admin.display(description='Student', ordering='enrollment__student__email')
    def student_name(self, obj):
        return obj.enrollment.student.get_full_name() or obj.enrollment.student.email
    
    @admin.display(description='Course', ordering='enrollment__course__title')
    def course_name(self, obj):
        return obj.enrollment.course.title
    
    @admin.display(description='Lesson', ordering='lesson__title')
    def lesson_title(self, obj):
        return f"{obj.lesson.module.title} → {obj.lesson.title}"
    
    @admin.display(description='Completed', boolean=True)
    def completion_icon(self, obj):
        return obj.completed
    
    @admin.action(description='Mark selected as completed')
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(completed=True, completed_at=timezone.now())
        self.message_user(request, f'{updated} lessons marked as completed.')
    
    @admin.action(description='Mark selected as incomplete')
    def mark_as_incomplete(self, request, queryset):
        updated = queryset.update(completed=False, completed_at=None)
        self.message_user(request, f'{updated} lessons marked as incomplete.')
from django.db.models import Count, Q, Case, When, FloatField, F
from django_filters import rest_framework as filters
from .models import Course, Enrollment


class CourseFilter(filters.FilterSet):
    """
    Filter for courses with advanced filtering options.
    """
    # Price filters
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_free = filters.BooleanFilter(method='filter_is_free')
    
    # Level filter
    level = filters.MultipleChoiceFilter(
        choices=Course.LEVEL_CHOICES,
        field_name='level',
        lookup_expr='exact'
    )
    
    # Instructor filter
    instructor_email = filters.CharFilter(
        field_name='instructor__email',
        lookup_expr='icontains'
    )
    
    # Date filters
    created_after = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Course
        fields = ['status', 'level', 'instructor']
    
    def filter_is_free(self, queryset, name, value):
        """Filter courses that are free (price = 0)."""
        if value:
            return queryset.filter(price=0)
        return queryset.exclude(price=0)


class EnrollmentFilter(filters.FilterSet):
    """
    Filter for enrollments with optimized queries using annotations.
    """
    is_completed = filters.BooleanFilter(method='filter_is_completed')
    progress_min = filters.NumberFilter(method='filter_progress_min')
    progress_max = filters.NumberFilter(method='filter_progress_max')
    
    class Meta:
        model = Enrollment
        fields = ['is_active', 'course']
    
    def filter_is_completed(self, queryset, name, value):
        """Filter completed/incomplete enrollments."""
        if value:
            return queryset.filter(completed_at__isnull=False)
        return queryset.filter(completed_at__isnull=True)
    
    def filter_progress_min(self, queryset, name, value):
        """
        Filter enrollments with progress >= value.
        Uses annotation to calculate progress percentage efficiently.
        """
        # Annotate queryset with progress percentage
        queryset = self._annotate_progress(queryset)
        return queryset.filter(progress_percentage__gte=value)
    
    def filter_progress_max(self, queryset, name, value):
        """
        Filter enrollments with progress <= value.
        Uses annotation to calculate progress percentage efficiently.
        """
        # Annotate queryset with progress percentage
        queryset = self._annotate_progress(queryset)
        return queryset.filter(progress_percentage__lte=value)
    
    def _annotate_progress(self, queryset):
        """
        Helper method to annotate enrollments with progress percentage.
        This calculates the percentage in a single database query.
        """
        from django.db.models import Count, F, Case, When, FloatField, Value
        from django.db.models.functions import Cast, Coalesce
        
        return queryset.annotate(
            # Count total progress records
            total_progress=Count('progress_records', distinct=True),
            # Count completed progress records
            completed_progress=Count(
                'progress_records',
                filter=Q(progress_records__completed=True),
                distinct=True
            ),
            # Calculate percentage (avoid division by zero)
            progress_percentage=Case(
                When(total_progress=0, then=Value(0.0)),
                default=Cast(F('completed_progress'), FloatField()) / Cast(F('total_progress'), FloatField()) * 100,
                output_field=FloatField()
            )
        )
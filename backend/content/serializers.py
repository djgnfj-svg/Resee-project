import logging
from rest_framework import serializers

from .models import Category, Content

logger = logging.getLogger(__name__)


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer"""
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'created_at', 'user')
        read_only_fields = ('id', 'slug', 'created_at', 'user')


class ContentSerializer(serializers.ModelSerializer):
    """Content serializer"""
    author = serializers.StringRelatedField(read_only=True)
    review_count = serializers.SerializerMethodField()
    next_review_date = serializers.SerializerMethodField()

    class Meta:
        model = Content
        fields = ('id', 'title', 'content', 'author', 'category',
                 'created_at', 'updated_at', 'review_count',
                 'next_review_date', 'review_mode', 'mc_choices',
                 'is_ai_validated', 'ai_validation_score',
                 'ai_validation_result', 'ai_validated_at')
        read_only_fields = ('id', 'author', 'created_at', 'updated_at',
                           'is_ai_validated', 'ai_validation_score',
                           'ai_validation_result', 'ai_validated_at', 'mc_choices')

    def to_representation(self, instance):
        """Custom representation for category"""
        data = super().to_representation(instance)
        # Use CategorySerializer for read operations
        if instance.category:
            data['category'] = CategorySerializer(instance.category).data
        else:
            data['category'] = None
        return data

    def validate_category(self, value):
        """Validate category belongs to user"""
        if value is None:
            return value

        # Handle integer ID or Category instance
        if isinstance(value, int):
            category_id = value
        elif hasattr(value, 'id'):
            category_id = value.id
        else:
            raise serializers.ValidationError("Invalid category value")

        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Authentication required")

        try:
            category = Category.objects.get(id=category_id, user=request.user)
            return category
        except Category.DoesNotExist:
            raise serializers.ValidationError("Category not found or doesn't belong to user")

    def create(self, validated_data):
        """Create content with category and generate MC options if needed"""
        category = validated_data.get('category')

        # Convert category ID to category instance if needed
        if isinstance(category, int):
            try:
                category = Category.objects.get(id=category, user=self.context['request'].user)
                validated_data['category'] = category
            except Category.DoesNotExist:
                raise serializers.ValidationError({"category": "Category not found or doesn't belong to user"})

        # Create content
        content = super().create(validated_data)

        # Generate multiple choice options for MC mode
        if content.review_mode == 'multiple_choice':
            from ai_services import generate_multiple_choice_options
            mc_options = generate_multiple_choice_options(content.title, content.content)
            if mc_options:
                content.mc_choices = mc_options
                content.save(update_fields=['mc_choices'])
            else:
                logger.warning(f"Failed to generate MC options for content {content.id}")

        return content

    def update(self, instance, validated_data):
        """Update content with category and regenerate MC options if needed"""
        category = validated_data.get('category')

        # Convert category ID to category instance if needed
        if isinstance(category, int):
            try:
                category = Category.objects.get(id=category, user=self.context['request'].user)
                validated_data['category'] = category
            except Category.DoesNotExist:
                raise serializers.ValidationError({"category": "Category not found or doesn't belong to user"})

        # Check if title or content changed
        title_changed = 'title' in validated_data and validated_data['title'] != instance.title
        content_changed = 'content' in validated_data and validated_data['content'] != instance.content

        # Update content
        content = super().update(instance, validated_data)

        # Regenerate MC options if content changed and mode is MC
        if content.review_mode == 'multiple_choice' and (title_changed or content_changed):
            from ai_services import generate_multiple_choice_options
            mc_options = generate_multiple_choice_options(content.title, content.content)
            if mc_options:
                content.mc_choices = mc_options
                content.save(update_fields=['mc_choices'])
            else:
                logger.warning(f"Failed to regenerate MC options for content {content.id}")

        return content
    
    def get_review_count(self, obj):
        """Get the number of completed reviews for this content"""
        # Use annotated value if available (from optimized queryset)
        if hasattr(obj, 'review_count_annotated'):
            return obj.review_count_annotated
        # Use prefetched value if available
        if hasattr(obj, 'user_review_history'):
            return len(obj.user_review_history)
        # Fallback to direct count (e.g., during tests or direct serialization)
        return obj.review_history.count()

    def get_next_review_date(self, obj):
        """Get next review date"""
        try:
            # Use prefetched value if available (from optimized queryset)
            if hasattr(obj, 'user_review_schedules'):
                schedules = obj.user_review_schedules
                return schedules[0].next_review_date if schedules else None

            # Fallback to query (e.g., during tests or direct serialization)
            schedule = obj.review_schedules.filter(user=self.context['request'].user).first()
            return schedule.next_review_date if schedule else None
        except (KeyError, AttributeError) as e:
            # KeyError: 'request' not in context (e.g., during tests)
            # AttributeError: request.user not available
            logger.warning(f"Failed to get next_review_date for content {obj.id}: {e}")
            return None
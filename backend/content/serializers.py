from rest_framework import serializers

from .models import Category, Content


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
                 'next_review_date')
        read_only_fields = ('id', 'author', 'created_at', 'updated_at')

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
        """Create content with category"""
        category = validated_data.get('category')

        # Convert category ID to category instance if needed
        if isinstance(category, int):
            try:
                category = Category.objects.get(id=category, user=self.context['request'].user)
                validated_data['category'] = category
            except Category.DoesNotExist:
                raise serializers.ValidationError({"category": "Category not found or doesn't belong to user"})

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update content with category"""
        category = validated_data.get('category')

        # Convert category ID to category instance if needed
        if isinstance(category, int):
            try:
                category = Category.objects.get(id=category, user=self.context['request'].user)
                validated_data['category'] = category
            except Category.DoesNotExist:
                raise serializers.ValidationError({"category": "Category not found or doesn't belong to user"})

        return super().update(instance, validated_data)
    
    def get_review_count(self, obj):
        """Get the number of completed reviews for this content"""
        return obj.review_history.count()
    
    def get_next_review_date(self, obj):
        """Get next review date"""
        try:
            schedule = obj.review_schedules.filter(user=self.context['request'].user).first()
            return schedule.next_review_date if schedule else None
        except:
            return None
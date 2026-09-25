# posts/serializers.py
from rest_framework import serializers
from .models import Post, Category, Tag, Author, PostMetaData, PostJsonLd

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'category']

class AuthorSummarySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    
    class Meta:
        model = Author
        fields = ['id', 'username', 'full_name', 'profile_picture']
    
    def get_full_name(self, obj):
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        return obj.user.username


class PostMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostMetaData
        fields = ['data', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class PostJsonLdSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostJsonLd
        fields = ['data', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class PostSerializer(serializers.ModelSerializer):
    author = AuthorSummarySerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    seo_metadata = PostMetaDataSerializer(read_only=True)
    json_ld_payload = PostJsonLdSerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'content', 'excerpt', 'is_html',
                  'graphical_content',
                  'cover_image', 'created_at', 'author', 'category', 'tags',
                  'seo_metadata', 'json_ld_payload', 'category_id', 'tag_ids', 'status']
        read_only_fields = ['slug', 'created_at', 'author']
    
    def create(self, validated_data):
        # Extract tag_ids and category_id
        tag_ids = validated_data.pop('tag_ids', [])
        category_id = validated_data.pop('category_id', None)
        
        # Set category if provided
        if category_id:
            validated_data['category_id'] = category_id
        
        # Create post
        post = Post.objects.create(**validated_data)
        
        # Add tags if provided
        if tag_ids:
            post.tags.set(tag_ids)
        
        return post


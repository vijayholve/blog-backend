from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Author


class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for the Author model"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    
    class Meta:
        model = Author
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'bio', 'profile_picture', 'website', 'twitter_handle']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    # Optional author fields
    bio = serializers.CharField(max_length=500, required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    twitter_handle = serializers.CharField(max_length=100, required=False, allow_blank=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 
                  'first_name', 'last_name', 'bio', 'website', 
                  'twitter_handle', 'profile_picture']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False}
        }
    
    def validate(self, data):
        """Validate password match and email uniqueness"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                "password": "Passwords do not match."
            })
        
        # Check if email already exists
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({
                "email": "A user with this email already exists."
            })
        
        return data
    
    def create(self, validated_data):
        """Create user and author profile"""
        # Remove password_confirm and author fields
        validated_data.pop('password_confirm')
        bio = validated_data.pop('bio', '')
        website = validated_data.pop('website', '')
        twitter_handle = validated_data.pop('twitter_handle', '')
        profile_picture = validated_data.pop('profile_picture', None)
        
        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        
        # Create author profile (in case signal doesn't fire)
        Author.objects.get_or_create(
            user=user,
            defaults={
                'bio': bio,
                'website': website,
                'twitter_handle': twitter_handle,
                'profile_picture': profile_picture
            }
        )
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        """Authenticate user"""
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError(
                    "Unable to login with provided credentials."
                )
            if not user.is_active:
                raise serializers.ValidationError(
                    "User account is disabled."
                )
            data['user'] = user
        else:
            raise serializers.ValidationError(
                "Must include 'username' and 'password'."
            )
        
        return data


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details with author profile"""
    author_profile = AuthorSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'author_profile']
        read_only_fields = ['id', 'username']


class AuthorProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating author profile"""
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    
    class Meta:
        model = Author
        fields = ['bio', 'profile_picture', 'website', 'twitter_handle', 
                  'first_name', 'last_name']
    
    def update(self, instance, validated_data):
        # Update user fields if provided
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.save()
        
        # Update author fields
        instance.bio = validated_data.get('bio', instance.bio)
        instance.website = validated_data.get('website', instance.website)
        instance.twitter_handle = validated_data.get('twitter_handle', instance.twitter_handle)
        
        if 'profile_picture' in validated_data:
            instance.profile_picture = validated_data['profile_picture']
        
        instance.save()
        return instance

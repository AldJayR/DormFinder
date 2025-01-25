from rest_framework import serializers
from .models import Post, Comment
from core.serializers.user_serializers import UserProfileSerializer
from core.serializers.dorm_serializers import DormSerializer

class PostSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True)
    dorm = DormSerializer(read_only=True)
    comment_count = serializers.IntegerField(source='comments.count', read_only=True)
    total_likes = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'dorm', 'author', 
                 'created_at', 'updated_at', 'is_pinned', 'comment_count',
                 'total_likes', 'has_liked']
        read_only_fields = ['author', 'dorm', 'created_at', 'updated_at']

    def get_total_likes(self, obj):
        return obj.likes.count()

    def get_has_liked(self, obj):
        request = self.context.get('request')
        return request.user in obj.likes.all() if request else False

class CommentSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True)
    total_likes = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'content', 'author', 'created_at', 'total_likes', 'has_liked']
        read_only_fields = ['author', 'created_at']

    def get_total_likes(self, obj):
        return obj.likes.count()

    def get_has_liked(self, obj):
        request = self.context.get('request')
        return request.user in obj.likes.all() if request else False

from django.db import models
from core.models.user import User
from core.models.dorm import Dorm
from django.core.validators import MinLengthValidator
from django.db import models
from core.models.user import User
from core.models.dorm import Dorm

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    dorm = models.ForeignKey(Dorm, on_delete=models.CASCADE, related_name='forum_posts')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['dorm', 'created_at']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['is_pinned', '-created_at']),
        ]
    def __str__(self):
        return f"{self.title} - {self.dorm.name}"

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True)

    class Meta:
        ordering = ['created_at']
        
    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"

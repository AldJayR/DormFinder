from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Post, Comment
from .serializers import PostSerializer, CommentSerializer
from core.permissions import IsOwnerOrReadOnly

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related('author', 'dorm').prefetch_related('likes', 'comments')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'], url_path='like')
    def like_post(self, request, pk=None):
        post = self.get_object()
        user = request.user
        
        if request.method == 'POST':
            post.likes.add(user)
            return Response({'status': 'liked'}, status=status.HTTP_201_CREATED)
        
        if request.method == 'DELETE':
            post.likes.remove(user)
            return Response({'status': 'unliked'}, status=status.HTTP_204_NO_CONTENT)
        
        return Response(status=status.HTTP_400_BAD_REQUEST)

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        return Comment.objects.filter(post_id=self.kwargs['post_pk'])

    def perform_create(self, serializer):
        post = Post.objects.get(pk=self.kwargs['post_pk'])
        serializer.save(author=self.request.user, post=post)

    @action(detail=True, methods=['post', 'delete'], url_path='like')
    def like_comment(self, request, pk=None):
        comment = self.get_object()
        user = request.user
        
        if request.method == 'POST':
            comment.likes.add(user)
            return Response({'status': 'liked'}, status=status.HTTP_201_CREATED)
        
        if request.method == 'DELETE':
            comment.likes.remove(user)
            return Response({'status': 'unliked'}, status=status.HTTP_204_NO_CONTENT)
        
        return Response(status=status.HTTP_400_BAD_REQUEST)

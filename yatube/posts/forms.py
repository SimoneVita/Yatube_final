from django.forms import ModelForm, Textarea

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image',)

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',) 

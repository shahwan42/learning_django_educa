from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from .fields import OrderField


class Subject(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class Course(models.Model):
    owner = models.ForeignKey(User, related_name='courses_created', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, related_name='courses', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    overview = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    students = models.ManyToManyField(User, related_name='courses_joined', blank=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.title


class Module(models.Model):
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = OrderField(blank=True, for_fields=['course'])  # order calculated respect to 'course' field

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.order}. {self.title}'


class Content(models.Model):
    # the module contains multiple contents (with different content types: images, videos, text, etc)
    # so we need to setup a generic relation using the ContentTypes framework
    module = models.ForeignKey(Module, related_name='contents', on_delete=models.CASCADE)
    # setting up the generic relation requires 3 steps
    # 1. a ForeingKey to the ContentType model
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, limit_choices_to={'model__in': ('text', 'video', 'image', 'file')})
    # 2. field to store the primary key of the related object
    object_id = models.PositiveIntegerField()
    # 3. a GenericForeignKey to the related object by combining the two previous fields
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(blank=True, for_fields=['module'])

    class Meta:
        ordering = ['order']


class ItemBase(models.Model):
    """Abstract model for common fields in each content item"""
    owner = models.ForeignKey(User, related_name='%(class)s_related', on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def render(self):
        """render different templates according to the content model_name"""
        return render_to_string(f'courses/content/{self._meta.model_name}.html', {'item': self})

    class Meta:
        abstract = True

    def __str__(self):
        return self.title


class Text(ItemBase):
    """Text items"""
    content = models.TextField()


class File(ItemBase):
    """File items"""
    file = models.FileField(upload_to='files')


class Image(ItemBase):
    """Image items"""
    file = models.FileField(upload_to='images')


class Video (ItemBase):
    """Video items"""
    url = models.URLField()

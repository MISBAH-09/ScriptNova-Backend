from django.db import models

class User(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=20)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    token = models.CharField(max_length=200, null=True, blank=True)
    profile = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



class Blog(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blogs')
    title = models.CharField(max_length=500)
    content = models.TextField()
    keywords = models.CharField(max_length=1000, blank=True, default='')
    tone = models.CharField(max_length=100, blank=True, default='')
    length_preference = models.CharField(max_length=100, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    word_count = models.PositiveIntegerField(default=0)
    slug = models.SlugField(max_length=600, blank=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} [{self.status}] — {self.user.username}"

    def save(self, *args, **kwargs):
        # Auto-calculate word count if not provided
        if self.content and not self.word_count:
            self.word_count = len(self.content.split())

        # Auto-generate slug if not set
        if not self.slug:
            from django.utils.text import slugify
            import uuid
            base_slug = slugify(self.title)[:550]
            self.slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"

        super().save(*args, **kwargs)
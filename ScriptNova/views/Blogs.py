from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ScriptNova.middleware.auth import require_token
from ScriptNova.models import Blog
import os
import requests

# ── Environment ───────────────────────────────────────────────────────────────
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

nvidia_headers = {
    "Authorization": f"Bearer {NVIDIA_API_KEY}",
    "Content-Type": "application/json"
}

LENGTH_MAP = {
    "Short (500-800 words)":    {"min": 500,  "max": 800,  "max_tokens": 1200},
    "Medium (1000-1500 words)": {"min": 1000, "max": 1500, "max_tokens": 2200},
    "Long (2000+ words)":       {"min": 2000, "max": 2500, "max_tokens": 3800},
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def blog_to_dict(blog, include_content=True):
    """Convert a Blog instance to a plain dict — no serializer needed."""
    d = {
        "id":                blog.id,
        "title":             blog.title,
        "keywords":          blog.keywords,
        "tone":              blog.tone,
        "length_preference": blog.length_preference,
        "status":            blog.status,
        "word_count":        blog.word_count,
        "slug":              blog.slug,
        "created_at":        blog.created_at.isoformat() if blog.created_at else None,
        "updated_at":        blog.updated_at.isoformat() if blog.updated_at else None,
    }
    if include_content:
        d["content"] = blog.content
    return d


def generate_keywords(title):
    prompt = f"""Generate 8 SEO-friendly keywords for a blog titled: "{title}"
Return only a comma-separated list."""
    payload = {
        "model": "qwen/qwen3.5-122b-a10b",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.5
    }
    response = requests.post(INVOKE_URL, headers=nvidia_headers, json=payload, timeout=30)
    response.raise_for_status()
    keywords = response.json()["choices"][0]["message"]["content"]
    return [k.strip() for k in keywords.split(",") if k.strip()]


def generate_blog_content(title, keywords, tone, length):
    keywords_str = ", ".join(keywords) if isinstance(keywords, list) else keywords
    cfg = LENGTH_MAP.get(length, LENGTH_MAP["Medium (1000-1500 words)"])

    prompt = f"""You are an expert SEO blog writer.

Write a blog post with EXACTLY between {cfg['min']} and {cfg['max']} words.

Title: {title}
Keywords: {keywords_str}
Tone: {tone}

STRUCTURE:
- Introduction (no heading)
- 3 to 4 sections each with a ## heading
- Conclusion section with ## Conclusion heading

FORMATTING RULES:
- Use ## for section headings
- Put a blank line before and after every ## heading
- Use **bold** for important terms
- Use bullet points with "- " where appropriate
- Separate paragraphs with a blank line

OUTPUT: blog content only, no extra commentary."""

    payload = {
        "model": "qwen/qwen3.5-122b-a10b",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": cfg["max_tokens"],
        "temperature": 0.6
    }
    response = requests.post(INVOKE_URL, headers=nvidia_headers, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


# ── AI Views ──────────────────────────────────────────────────────────────────

class GenerateKeywords(APIView):
    @require_token
    def post(self, request):
        title = request.data.get("title")
        if not title:
            return Response({"success": False, "message": "Title is required"}, status=400)
        try:
            keywords = generate_keywords(title)
            return Response({"success": True, "data": keywords})
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=500)


class GenerateBlog(APIView):
    @require_token
    def post(self, request):
        title    = request.data.get("title")
        keywords = request.data.get("keywords")
        tone     = request.data.get("tone")
        length   = request.data.get("length")

        if not title or not tone or not length:
            return Response(
                {"success": False, "message": "Title, tone, and length are required"},
                status=400
            )
        try:
            if not keywords:
                keywords = generate_keywords(title)
            content = generate_blog_content(title, keywords, tone, length)
            return Response({
                "success": True,
                "data": {"title": title, "keywords": keywords, "content": content}
            })
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=500)


# ── Blog CRUD — pure ORM, no serializers ──────────────────────────────────────

class BlogListCreateView(APIView):
    """
    GET  /blogs/  → list user's blogs (no content field, fast)
    POST /blogs/  → create/save a blog
    """

    @require_token
    def get(self, request):
        user=request.auth_user  # request.user is set by @require_token to your custom User instance
        qs = Blog.objects.filter(user=user)
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        blogs = [blog_to_dict(b, include_content=False) for b in qs]
        return Response({"success": True, "data": blogs})

    @require_token
    def post(self, request):
        user=request.auth_user  # request.user is set by @require_token to your custom User instance
        print(f"Creating blog for user: {user.username} (ID: {user.id})")  # Debug log
        title             = request.data.get("title", "").strip()
        content           = request.data.get("content", "").strip()
        keywords          = request.data.get("keywords", "")
        tone              = request.data.get("tone", "")
        length_preference = request.data.get("length_preference", "")
        blog_status       = request.data.get("status", "draft")
        word_count        = request.data.get("word_count", 0)
        print(f"Received data: title='{title}', content length={len(content)}, keywords='{keywords}', tone='{tone}', length_preference='{length_preference}', status='{blog_status}', word_count={word_count}")  # Debug log

        if not title :
            return Response(
                {"success": False, "message": "Title is required"},
                status=400
            )

        # Auto word count if frontend didn't send it
        if not word_count and content:
            word_count = len(content.split())

        # keywords can arrive as a list from frontend — store as comma string
        if isinstance(keywords, list):
            keywords = ", ".join(keywords)

        blog = Blog.objects.create(
            user=user,          # request.user = custom User set by @require_token
            title=title,
            content=content,
            keywords=keywords,
            tone=tone,
            length_preference=length_preference,
            status=blog_status,
            word_count=word_count,
        )

        return Response({"success": True, "data": blog_to_dict(blog)}, status=201)


class BlogDetailView(APIView):
    """
    GET    /blogs/<id>/  → full blog including content
    PATCH  /blogs/<id>/  → update any fields
    DELETE /blogs/<id>/  → delete
    """
    @require_token
    def _get_blog(self, request, pk):
        try:
            blog = Blog.objects.get(pk=pk, user=request.auth_user)
            return blog
        except Blog.DoesNotExist:
            return None

    @require_token
    def get(self, request, pk):
        blog = self._get_blog(request, pk)
        if not blog:
            return Response({"success": False, "message": "Blog not found"}, status=404)
        return Response({"success": True, "data": blog_to_dict(blog)})

    @require_token
    def patch(self, request, pk):
        blog = self._get_blog(request, pk)
        if not blog:
            return Response({"success": False, "message": "Blog not found"}, status=404)

        # Only update fields that were actually sent
        updatable = ["title", "content", "keywords", "tone",
                     "length_preference", "status", "word_count"]
        for field in updatable:
            if field in request.data:
                val = request.data[field]
                if field == "keywords" and isinstance(val, list):
                    val = ", ".join(val)
                setattr(blog, field, val)

        # Recalculate word count if content changed
        if "content" in request.data and not request.data.get("word_count"):
            blog.word_count = len(blog.content.split())

        blog.save()
        return Response({"success": True, "data": blog_to_dict(blog)})

    @require_token
    def delete(self, request, pk):
        blog = self._get_blog(request, pk)
        if not blog:
            return Response({"success": False, "message": "Blog not found"}, status=404)
        blog.delete()
        return Response({"success": True, "message": "Deleted"}, status=204)


class BlogPublishView(APIView):
    """POST /blogs/<id>/publish/  → toggle draft ↔ published"""

    @require_token
    def post(self, request, pk):
        try:
            blog = Blog.objects.get(pk=pk, user=request.user)
        except Blog.DoesNotExist:
            return Response({"success": False, "message": "Blog not found"}, status=404)

        blog.status = "draft" if blog.status == "published" else "published"
        blog.save(update_fields=["status", "updated_at"])
        return Response({"success": True, "id": blog.id, "status": blog.status})


class BlogStatsView(APIView):
    """GET /blogs/stats/  → counts for dashboard"""

    @require_token
    def get(self, request):
        qs = Blog.objects.filter(user=request.user)
        total_words = sum(qs.values_list("word_count", flat=True))
        return Response({
            "success": True,
            "data": {
                "total":       qs.count(),
                "published":   qs.filter(status="published").count(),
                "drafts":      qs.filter(status="draft").count(),
                "total_words": total_words,
            }
        })
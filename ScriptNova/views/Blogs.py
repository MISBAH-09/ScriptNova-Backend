# from rest_framework.views import APIView
# from rest_framework.response import Response
# from ScriptNova.middleware.auth import require_token
# from ScriptNova.models import Blog
# import os
# import time
# import requests

# # ── Environment ───────────────────────────────────────────────────────────────
# NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
# INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

# nvidia_headers = {
#     "Authorization": f"Bearer {NVIDIA_API_KEY}",
#     "Content-Type": "application/json",
# }

# # ── Model selection ───────────────────────────────────────────────────────────
# # Fast small model — for short tasks (keywords, title suggestion)
# FAST_MODEL = "meta/llama-3.1-8b-instruct"
# # Quality model — for full blog, rephrase, rearrange
# QUALITY_MODEL = "meta/llama-3.3-70b-instruct"

# LENGTH_MAP = {
#     "Short (500-800 words)":    {"min": 500,  "max": 800,  "max_tokens": 1200},
#     "Medium (1000-1500 words)": {"min": 1000, "max": 1500, "max_tokens": 2200},
#     "Long (2000+ words)":       {"min": 2000, "max": 2500, "max_tokens": 3800},
# }


# # ── Core API helper with retries ──────────────────────────────────────────────

# def _nvidia_chat(prompt_text, model=QUALITY_MODEL, max_tokens=300, temperature=0.6, timeout=300):
#     """
#     Call the NVIDIA NIM chat completions endpoint with automatic retries.
#     - Uses stream=False explicitly to avoid streaming ambiguity.
#     - Retries up to 3 times with exponential backoff on timeout/connection errors.
#     """
#     payload = {
#         "model": model,
#         "messages": [{"role": "user", "content": prompt_text}],
#         "max_tokens": max_tokens,
#         "temperature": temperature,
#         "stream": False,
#     }

#     last_error = None
#     for attempt in range(3):
#         try:
#             response = requests.post(
#                 INVOKE_URL,
#                 headers=nvidia_headers,
#                 json=payload,
#                 timeout=timeout,
#             )
#             response.raise_for_status()
#             return response.json()["choices"][0]["message"]["content"]
#         except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
#             last_error = e
#             if attempt < 2:
#                 wait = 3 * (attempt + 1)   # 3s, 6s
#                 print(f"[NVIDIA] Attempt {attempt + 1} failed ({type(e).__name__}), retrying in {wait}s...")
#                 time.sleep(wait)
#             else:
#                 print(f"[NVIDIA] All 3 attempts failed.")
#         except requests.exceptions.HTTPError as e:
#             # Don't retry on HTTP errors (4xx/5xx) — retrying won't help
#             raise

#     raise last_error


# # ── Helpers ───────────────────────────────────────────────────────────────────

# def blog_to_dict(blog, include_content=True):
#     d = {
#         "id":                blog.id,
#         "prompt":            blog.prompt,
#         "title":             blog.title,
#         "keywords":          blog.keywords,
#         "tone":              blog.tone,
#         "length_preference": blog.length_preference,
#         "status":            blog.status,
#         "word_count":        blog.word_count,
#         "slug":              blog.slug,
#         "created_at":        blog.created_at.isoformat() if blog.created_at else None,
#         "updated_at":        blog.updated_at.isoformat() if blog.updated_at else None,
#     }
#     if include_content:
#         d["content"] = blog.content
#     return d


# def generate_keywords(topic):
#     prompt = (
#         f'Generate 8 SEO-friendly keywords for a blog about: "{topic}"\n'
#         f'Return ONLY a comma-separated list. No explanation, no numbering, no extra text.'
#     )
#     # Fast model, small output — timeout 180s is plenty
#     raw = _nvidia_chat(prompt, model=FAST_MODEL, max_tokens=150, temperature=0.4, timeout=180)
#     return [k.strip() for k in raw.split(",") if k.strip()]


# def suggest_title(topic, keywords=None):
#     keywords_hint = f"\nKeywords: {', '.join(keywords)}" if keywords else ""
#     prompt = (
#         f"Suggest ONE catchy, SEO-friendly blog post title for this topic:\n"
#         f"Topic: {topic}{keywords_hint}\n\n"
#         f"Rules:\n"
#         f"- Return ONLY the title text. No quotes, no explanation, no numbering.\n"
#         f"- Make it engaging and click-worthy.\n"
#         f"- Between 6 and 12 words."
#     )
#     raw = _nvidia_chat(prompt, model=FAST_MODEL, max_tokens=60, temperature=0.7, timeout=180)
#     return raw.strip().strip('"').strip("'")


# def generate_blog_content(title, keywords, tone, length):
#     keywords_str = ", ".join(keywords) if isinstance(keywords, list) else keywords
#     cfg = LENGTH_MAP.get(length, LENGTH_MAP["Medium (1000-1500 words)"])

#     prompt = (
#         f"You are an expert SEO blog writer.\n\n"
#         f"Write a blog post with EXACTLY between {cfg['min']} and {cfg['max']} words.\n\n"
#         f"Title: {title}\n"
#         f"Keywords: {keywords_str}\n"
#         f"Tone: {tone}\n\n"
#         f"STRUCTURE:\n"
#         f"- Introduction (no heading)\n"
#         f"- 3 to 4 sections each with a ## heading\n"
#         f"- Conclusion section with ## Conclusion heading\n\n"
#         f"FORMATTING RULES:\n"
#         f"- Use ## for section headings\n"
#         f"- Put a blank line before and after every ## heading\n"
#         f"- Use **bold** for important terms\n"
#         f'- Use bullet points with "- " where appropriate\n'
#         f"- Separate paragraphs with a blank line\n\n"
#         f"OUTPUT: blog content only, no extra commentary."
#     )

#     # Quality model, long output — timeout 360s for cold starts + generation
#     return _nvidia_chat(
#         prompt,
#         model=QUALITY_MODEL,
#         max_tokens=cfg["max_tokens"],
#         temperature=0.6,
#         timeout=360,
#     )


# # ── AI Views ──────────────────────────────────────────────────────────────────

# class GenerateKeywords(APIView):
#     @require_token
#     def post(self, request):
#         title = request.data.get("title", "").strip()
#         if not title:
#             return Response({"success": False, "message": "Title is required"}, status=400)
#         try:
#             keywords = generate_keywords(title)
#             return Response({"success": True, "data": keywords})
#         except Exception as e:
#             return Response({"success": False, "message": str(e)}, status=500)


# class GenerateBlog(APIView):
#     """
#     POST /generate-blog/
#     Body: { prompt, keywords?, tone, length }
#     Returns: { prompt, suggested_title, keywords, content }

#     The model suggests the title from the user's topic/prompt.
#     """
#     @require_token
#     def post(self, request):
#         prompt   = request.data.get("prompt", "").strip()
#         keywords = request.data.get("keywords")
#         tone     = request.data.get("tone", "").strip()
#         length   = request.data.get("length", "").strip()

#         if not prompt or not tone or not length:
#             return Response(
#                 {"success": False, "message": "prompt, tone, and length are required"},
#                 status=400,
#             )
#         try:
#             # 1. Generate keywords if not supplied
#             if not keywords:
#                 keywords = generate_keywords(prompt)

#             # 2. Model suggests a title from the prompt
#             suggested_title = suggest_title(prompt, keywords)

#             # 3. Generate the full article using the suggested title
#             content = generate_blog_content(suggested_title, keywords, tone, length)

#             return Response({
#                 "success": True,
#                 "data": {
#                     "prompt":          prompt,
#                     "suggested_title": suggested_title,
#                     "keywords":        keywords,
#                     "content":         content,
#                 },
#             })
#         except Exception as e:
#             return Response({"success": False, "message": str(e)}, status=500)


# class RegenerateTitle(APIView):
#     """
#     POST /generate-title/
#     Body: { prompt, article_content, keywords? }
#     Returns: { suggested_title }
#     """
#     @require_token
#     def post(self, request):
#         prompt          = request.data.get("prompt", "").strip()
#         article_content = request.data.get("article_content", "").strip()
#         keywords        = request.data.get("keywords")

#         if not prompt and not article_content:
#             return Response(
#                 {"success": False, "message": "Either prompt or article_content is required"},
#                 status=400,
#             )
#         try:
#             hint_topic = prompt
#             if article_content:
#                 snippet = article_content[:400].replace("\n", " ")
#                 hint_topic = f"{prompt}\n\nArticle excerpt: {snippet}" if prompt else snippet

#             suggested_title = suggest_title(hint_topic, keywords)
#             return Response({"success": True, "data": {"suggested_title": suggested_title}})
#         except Exception as e:
#             return Response({"success": False, "message": str(e)}, status=500)


# class RephraseBlog(APIView):
#     """
#     POST /rephrase-blog/
#     Body: { article_content, mode }
#         mode: "rephrase" | "rearrange" | "regenerate"
#         For "regenerate": also pass { prompt, keywords, tone, length }
#     Returns: { content }
#     """
#     @require_token
#     def post(self, request):
#         article_content = request.data.get("article_content", "").strip()
#         mode            = request.data.get("mode", "rephrase")

#         if not article_content and mode != "regenerate":
#             return Response({"success": False, "message": "article_content is required"}, status=400)

#         try:
#             if mode == "rephrase":
#                 prompt_text = (
#                     f"Rephrase the following blog article. Keep the same structure and all the main points, "
#                     f"but use completely different wording throughout. Maintain the same tone and length.\n\n"
#                     f"ARTICLE:\n{article_content}\n\n"
#                     f"OUTPUT: rephrased article only, same markdown formatting."
#                 )
#                 cfg = LENGTH_MAP["Medium (1000-1500 words)"]
#                 content = _nvidia_chat(prompt_text, model=QUALITY_MODEL, max_tokens=cfg["max_tokens"], temperature=0.65, timeout=360)

#             elif mode == "rearrange":
#                 prompt_text = (
#                     f"Rearrange and restructure the following blog article. Keep all the same information "
#                     f"and facts, but reorganise the sections into a better logical flow. You may rename "
#                     f"section headings if it improves clarity.\n\n"
#                     f"ARTICLE:\n{article_content}\n\n"
#                     f"OUTPUT: rearranged article only, same markdown formatting."
#                 )
#                 cfg = LENGTH_MAP["Medium (1000-1500 words)"]
#                 content = _nvidia_chat(prompt_text, model=QUALITY_MODEL, max_tokens=cfg["max_tokens"], temperature=0.65, timeout=360)

#             elif mode == "regenerate":
#                 prompt_val = request.data.get("prompt", "").strip()
#                 keywords   = request.data.get("keywords", [])
#                 tone       = request.data.get("tone", "Informative & Friendly")
#                 length     = request.data.get("length", "Medium (1000-1500 words)")

#                 if not prompt_val:
#                     return Response(
#                         {"success": False, "message": "prompt is required for regenerate mode"},
#                         status=400,
#                     )
#                 content = generate_blog_content(prompt_val, keywords, tone, length)
#             else:
#                 return Response(
#                     {"success": False, "message": "mode must be rephrase, rearrange, or regenerate"},
#                     status=400,
#                 )

#             return Response({"success": True, "data": {"content": content}})

#         except Exception as e:
#             return Response({"success": False, "message": str(e)}, status=500)


# # ── Blog CRUD ──────────────────────────────────────────────────────────────────

# class BlogListCreateView(APIView):
#     """
#     GET  /blogs/?limit=N&status=X  → list user's blogs (no content, fast)
#     POST /blogs/                   → create/save a blog
#     """

#     @require_token
#     def get(self, request):
#         user = request.auth_user
#         qs = Blog.objects.filter(user=user)

#         status_filter = request.query_params.get("status")
#         if status_filter:
#             qs = qs.filter(status=status_filter)

#         limit = request.query_params.get("limit")
#         if limit:
#             try:
#                 qs = qs[:int(limit)]
#             except (ValueError, TypeError):
#                 pass

#         blogs = [blog_to_dict(b, include_content=False) for b in qs]
#         return Response({"success": True, "data": blogs})

#     @require_token
#     def post(self, request):
#         user = request.auth_user
#         title             = request.data.get("title", "").strip()
#         prompt_val        = request.data.get("prompt", "").strip()
#         content           = request.data.get("content", "").strip()
#         keywords          = request.data.get("keywords", "")
#         tone              = request.data.get("tone", "")
#         length_preference = request.data.get("length_preference", "")
#         blog_status       = request.data.get("status", "draft")
#         word_count        = request.data.get("word_count", 0)

#         if not title:
#             return Response({"success": False, "message": "Title is required"}, status=400)

#         if not word_count and content:
#             word_count = len(content.split())

#         if isinstance(keywords, list):
#             keywords = ", ".join(keywords)

#         blog = Blog.objects.create(
#             user=user,
#             prompt=prompt_val,
#             title=title,
#             content=content,
#             keywords=keywords,
#             tone=tone,
#             length_preference=length_preference,
#             status=blog_status,
#             word_count=word_count,
#         )

#         return Response({"success": True, "data": blog_to_dict(blog)}, status=201)


# class BlogDetailView(APIView):
#     """
#     GET    /blogs/<id>/  → full blog including content
#     PATCH  /blogs/<id>/  → update any fields
#     DELETE /blogs/<id>/  → delete
#     """

#     def _get_blog(self, request, pk):
#         try:
#             return Blog.objects.get(pk=pk, user=request.auth_user)
#         except Blog.DoesNotExist:
#             return None

#     @require_token
#     def get(self, request, pk):
#         blog = self._get_blog(request, pk)
#         if not blog:
#             return Response({"success": False, "message": "Blog not found"}, status=404)
#         return Response({"success": True, "data": blog_to_dict(blog)})

#     @require_token
#     def patch(self, request, pk):
#         blog = self._get_blog(request, pk)
#         if not blog:
#             return Response({"success": False, "message": "Blog not found"}, status=404)

#         updatable = ["prompt", "title", "content", "keywords", "tone",
#                      "length_preference", "status", "word_count"]
#         for field in updatable:
#             if field in request.data:
#                 val = request.data[field]
#                 if field == "keywords" and isinstance(val, list):
#                     val = ", ".join(val)
#                 setattr(blog, field, val)

#         if "content" in request.data and not request.data.get("word_count"):
#             blog.word_count = len(blog.content.split())

#         blog.save()
#         return Response({"success": True, "data": blog_to_dict(blog)})

#     @require_token
#     def delete(self, request, pk):
#         blog = self._get_blog(request, pk)
#         if not blog:
#             return Response({"success": False, "message": "Blog not found"}, status=404)
#         blog.delete()
#         return Response({"success": True, "message": "Deleted"}, status=204)


# class BlogPublishView(APIView):
#     """POST /blogs/<id>/publish/  → toggle draft ↔ published"""

#     @require_token
#     def post(self, request, pk):
#         try:
#             blog = Blog.objects.get(pk=pk, user=request.auth_user)
#         except Blog.DoesNotExist:
#             return Response({"success": False, "message": "Blog not found"}, status=404)

#         blog.status = "draft" if blog.status == "published" else "published"
#         blog.save(update_fields=["status", "updated_at"])
#         return Response({"success": True, "id": blog.id, "status": blog.status})


# class BlogStatsView(APIView):
#     """GET /blogs/stats/  → counts for dashboard"""

#     @require_token
#     def get(self, request):
#         qs = Blog.objects.filter(user=request.auth_user)
#         total_words = sum(qs.values_list("word_count", flat=True))
#         return Response({
#             "success": True,
#             "data": {
#                 "total":       qs.count(),
#                 "published":   qs.filter(status="published").count(),
#                 "drafts":      qs.filter(status="draft").count(),
#                 "total_words": total_words,
#             },
#         })




from rest_framework.views import APIView
from rest_framework.response import Response
from ScriptNova.middleware.auth import require_token
from ScriptNova.models import Blog
import os
import time
import requests

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
INVOKE_URL     = "https://integrate.api.nvidia.com/v1/chat/completions"
nvidia_headers = {"Authorization": f"Bearer {NVIDIA_API_KEY}", "Content-Type": "application/json"}

FAST_MODEL    = "meta/llama-3.1-8b-instruct"
QUALITY_MODEL = "meta/llama-3.3-70b-instruct"

LENGTH_MAP = {
    "Short (500-800 words)":    {"min": 500,  "max": 800,  "max_tokens": 1200},
    "Medium (1000-1500 words)": {"min": 1000, "max": 1500, "max_tokens": 2200},
    "Long (2000+ words)":       {"min": 2000, "max": 2500, "max_tokens": 3800},
}


def _nvidia_chat(prompt_text, model=QUALITY_MODEL, max_tokens=300, temperature=0.6, timeout=300):
    payload = {"model": model, "messages": [{"role": "user", "content": prompt_text}],
               "max_tokens": max_tokens, "temperature": temperature, "stream": False}
    last_error = None
    for attempt in range(3):
        try:
            r = requests.post(INVOKE_URL, headers=nvidia_headers, json=payload, timeout=timeout)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_error = e
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
        except requests.exceptions.HTTPError:
            raise
    raise last_error


def blog_to_dict(blog, include_content=True):
    d = {
        "id":                blog.id,
        "prompt":            blog.prompt,
        "title":             blog.title,
        "keywords":          blog.keywords,
        "tone":              blog.tone,
        "length_preference": blog.length_preference,
        "word_count":        blog.word_count,
        "slug":              blog.slug,
        "favourite":         blog.favourite,          # "normal" | "favourite"
        "is_favourite":      blog.favourite == "favourite",  # bool helper for frontend
        "created_at":        blog.created_at.isoformat() if blog.created_at else None,
        "updated_at":        blog.updated_at.isoformat() if blog.updated_at else None,
    }
    if include_content:
        d["content"] = blog.content
    return d


def generate_keywords(topic):
    raw = _nvidia_chat(
        f'Generate 8 SEO-friendly keywords for a blog about: "{topic}"\n'
        f'Return ONLY a comma-separated list. No explanation, no numbering.',
        model=FAST_MODEL, max_tokens=150, temperature=0.4, timeout=180
    )
    return [k.strip() for k in raw.split(",") if k.strip()]


def suggest_title(topic, keywords=None):
    kw = f"\nKeywords: {', '.join(keywords)}" if keywords else ""
    raw = _nvidia_chat(
        f"Suggest ONE catchy, SEO-friendly blog post title for this topic:\n"
        f"Topic: {topic}{kw}\n\n"
        f"Rules:\n- Return ONLY the title text. No quotes, no explanation, no numbering.\n"
        f"- Make it engaging and click-worthy.\n- Between 6 and 12 words.",
        model=FAST_MODEL, max_tokens=60, temperature=0.7, timeout=180
    )
    return raw.strip().strip('"').strip("'")


def generate_blog_content(title, keywords, tone, length):
    kw_str = ", ".join(keywords) if isinstance(keywords, list) else keywords
    cfg    = LENGTH_MAP.get(length, LENGTH_MAP["Medium (1000-1500 words)"])
    return _nvidia_chat(
        f"You are an expert SEO blog writer.\n\n"
        f"Write a blog post with EXACTLY between {cfg['min']} and {cfg['max']} words.\n\n"
        f"Title: {title}\nKeywords: {kw_str}\nTone: {tone}\n\n"
        f"STRUCTURE:\n- Introduction (no heading)\n- 3 to 4 sections each with a ## heading\n"
        f"- Conclusion section with ## Conclusion heading\n\n"
        f"FORMATTING RULES:\n- Use ## for section headings\n"
        f"- Put a blank line before and after every ## heading\n"
        f"- Use **bold** for important terms\n- Use bullet points with \"- \" where appropriate\n"
        f"- Separate paragraphs with a blank line\n\nOUTPUT: blog content only, no extra commentary.",
        model=QUALITY_MODEL, max_tokens=cfg["max_tokens"], temperature=0.6, timeout=360
    )


# ── AI Views ──────────────────────────────────────────────────────────────────

class GenerateKeywords(APIView):
    @require_token
    def post(self, request):
        title = request.data.get("title", "").strip()
        if not title:
            return Response({"success": False, "message": "Title is required"}, status=400)
        try:
            return Response({"success": True, "data": generate_keywords(title)})
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=500)


class GenerateBlog(APIView):
    @require_token
    def post(self, request):
        prompt   = request.data.get("prompt", "").strip()
        keywords = request.data.get("keywords")
        tone     = request.data.get("tone", "").strip()
        length   = request.data.get("length", "").strip()
        if not prompt or not tone or not length:
            return Response({"success": False, "message": "prompt, tone, and length are required"}, status=400)
        try:
            if not keywords:
                keywords = generate_keywords(prompt)
            suggested_title = suggest_title(prompt, keywords)
            content         = generate_blog_content(suggested_title, keywords, tone, length)
            return Response({"success": True, "data": {
                "prompt": prompt, "suggested_title": suggested_title,
                "keywords": keywords, "content": content,
            }})
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=500)


class RegenerateTitle(APIView):
    @require_token
    def post(self, request):
        prompt          = request.data.get("prompt", "").strip()
        article_content = request.data.get("article_content", "").strip()
        keywords        = request.data.get("keywords")
        if not prompt and not article_content:
            return Response({"success": False, "message": "Either prompt or article_content is required"}, status=400)
        try:
            hint = prompt
            if article_content:
                snippet = article_content[:400].replace("\n", " ")
                hint    = f"{prompt}\n\nArticle excerpt: {snippet}" if prompt else snippet
            return Response({"success": True, "data": {"suggested_title": suggest_title(hint, keywords)}})
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=500)


class RephraseBlog(APIView):
    @require_token
    def post(self, request):
        article_content = request.data.get("article_content", "").strip()
        mode            = request.data.get("mode", "rephrase")
        if not article_content and mode != "regenerate":
            return Response({"success": False, "message": "article_content is required"}, status=400)
        try:
            cfg = LENGTH_MAP["Medium (1000-1500 words)"]
            if mode == "rephrase":
                content = _nvidia_chat(
                    f"Rephrase the following blog article. Keep the same structure and all the main points, "
                    f"but use completely different wording. Maintain the same tone and length.\n\n"
                    f"ARTICLE:\n{article_content}\n\nOUTPUT: rephrased article only, same markdown formatting.",
                    model=QUALITY_MODEL, max_tokens=cfg["max_tokens"], temperature=0.65, timeout=360)
            elif mode == "rearrange":
                content = _nvidia_chat(
                    f"Rearrange and restructure the following blog article. Keep all the same information "
                    f"but reorganise sections into a better logical flow. Rename headings if it improves clarity.\n\n"
                    f"ARTICLE:\n{article_content}\n\nOUTPUT: rearranged article only, same markdown formatting.",
                    model=QUALITY_MODEL, max_tokens=cfg["max_tokens"], temperature=0.65, timeout=360)
            elif mode == "regenerate":
                prompt_val = request.data.get("prompt", "").strip()
                keywords   = request.data.get("keywords", [])
                tone       = request.data.get("tone", "Informative & Friendly")
                length     = request.data.get("length", "Medium (1000-1500 words)")
                if not prompt_val:
                    return Response({"success": False, "message": "prompt is required for regenerate mode"}, status=400)
                content = generate_blog_content(prompt_val, keywords, tone, length)
            else:
                return Response({"success": False, "message": "mode must be rephrase, rearrange, or regenerate"}, status=400)
            return Response({"success": True, "data": {"content": content}})
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=500)


# ── Blog CRUD ──────────────────────────────────────────────────────────────────

class BlogListCreateView(APIView):
    @require_token
    def get(self, request):
        user = request.auth_user
        qs   = Blog.objects.filter(user=user)

        # Filter by favourite="favourite"
        fav = request.query_params.get("favourite")
        if fav == "true":
            qs = qs.filter(favourite="favourite")

        limit = request.query_params.get("limit")
        if limit:
            try: qs = qs[:int(limit)]
            except (ValueError, TypeError): pass

        return Response({"success": True, "data": [blog_to_dict(b, include_content=False) for b in qs]})

    @require_token
    def post(self, request):
        user              = request.auth_user
        title             = request.data.get("title", "").strip()
        prompt_val        = request.data.get("prompt", "").strip()
        content           = request.data.get("content", "").strip()
        keywords          = request.data.get("keywords", "")
        tone              = request.data.get("tone", "")
        length_preference = request.data.get("length_preference", "")
        word_count        = request.data.get("word_count", 0)

        if not title:
            return Response({"success": False, "message": "Title is required"}, status=400)
        if not word_count and content:
            word_count = len(content.split())
        if isinstance(keywords, list):
            keywords = ", ".join(keywords)

        blog = Blog.objects.create(
            user=user, prompt=prompt_val, title=title, content=content,
            keywords=keywords, tone=tone, length_preference=length_preference,
            word_count=word_count,
        )
        return Response({"success": True, "data": blog_to_dict(blog)}, status=201)


class BlogDetailView(APIView):
    def _get_blog(self, request, pk):
        try:    return Blog.objects.get(pk=pk, user=request.auth_user)
        except: return None

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

        updatable = ["prompt", "title", "content", "keywords", "tone",
                     "length_preference", "word_count", "favourite"]
        for field in updatable:
            if field in request.data:
                val = request.data[field]
                if field == "keywords" and isinstance(val, list):
                    val = ", ".join(val)
                setattr(blog, field, val)

        if "content" in request.data and not request.data.get("word_count"):
            blog.word_count = len(blog.content.split())

        # Regenerate slug when title changes
        if "title" in request.data:
            blog.slug = ""

        blog.save()
        return Response({"success": True, "data": blog_to_dict(blog)})

    @require_token
    def delete(self, request, pk):
        blog = self._get_blog(request, pk)
        if not blog:
            return Response({"success": False, "message": "Blog not found"}, status=404)
        blog.delete()
        return Response({"success": True, "message": "Deleted"}, status=204)


class BlogBySlugView(APIView):
    """GET /blogs/slug/<slug>/  — fetch a blog by its slug"""
    @require_token
    def get(self, request, slug):
        try:
            blog = Blog.objects.get(slug=slug, user=request.auth_user)
            return Response({"success": True, "data": blog_to_dict(blog)})
        except Blog.DoesNotExist:
            return Response({"success": False, "message": "Blog not found"}, status=404)


class BlogFavouriteView(APIView):
    """
    POST /blogs/<id>/favourite/
    Toggles favourite field between 'normal' and 'favourite'
    — same pattern as the old publish toggle
    """
    @require_token
    def post(self, request, pk):
        try:
            blog = Blog.objects.get(pk=pk, user=request.auth_user)
        except Blog.DoesNotExist:
            return Response({"success": False, "message": "Blog not found"}, status=404)

        blog.favourite = "normal" if blog.favourite == "favourite" else "favourite"
        blog.save(update_fields=["favourite", "updated_at"])
        return Response({
            "success":      True,
            "id":           blog.id,
            "favourite":    blog.favourite,
            "is_favourite": blog.favourite == "favourite",
        })


class BlogStatsView(APIView):
    @require_token
    def get(self, request):
        qs          = Blog.objects.filter(user=request.auth_user)
        total_words = sum(qs.values_list("word_count", flat=True))
        return Response({"success": True, "data": {
            "total":       qs.count(),
            "favourites":  qs.filter(favourite="favourite").count(),
            "total_words": total_words,
        }})
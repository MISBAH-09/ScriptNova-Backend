from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ScriptNova.middleware.auth import require_token
import os
import requests

# 🔐 Environment Variables
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {NVIDIA_API_KEY}",
    "Content-Type": "application/json"
}

# Word count ranges per length option
LENGTH_MAP = {
    "Short (500-800 words)":    {"min": 500,  "max": 800,  "max_tokens": 1200},
    "Medium (1000-1500 words)": {"min": 1000, "max": 1500, "max_tokens": 2200},
    "Long (2000+ words)":       {"min": 2000, "max": 2500, "max_tokens": 3800},
}


# =========================
# 🔹 KEYWORD GENERATOR
# =========================
def generate_keywords(title):
    prompt = f"""
Generate 8 SEO-friendly keywords for a blog titled:
"{title}"
Return only a comma-separated list.
"""
    payload = {
        "model": "qwen/qwen3.5-122b-a10b",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.5
    }
    response = requests.post(INVOKE_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    keywords = data["choices"][0]["message"]["content"]
    return [k.strip() for k in keywords.split(",") if k.strip()]


# =========================
# 🔹 BLOG GENERATOR
# =========================
def generate_blog_content(title, keywords, tone, length):
    keywords_str = ", ".join(keywords) if isinstance(keywords, list) else keywords

    # Get word count targets for the selected length
    length_config = LENGTH_MAP.get(length, LENGTH_MAP["Medium (1000-1500 words)"])
    min_words = length_config["min"]
    max_words = length_config["max"]
    max_tokens = length_config["max_tokens"]

    prompt = f"""You are an expert SEO blog writer.

Write a blog post with EXACTLY between {min_words} and {max_words} words. This word count range is strict — do not write fewer than {min_words} words or more than {max_words} words.

Title: {title}
Keywords: {keywords_str}
Tone: {tone}

STRUCTURE:
- Introduction (no heading)
- 3 to 4 sections each with a ## heading
- Conclusion section with ## Conclusion heading

FORMATTING RULES:
- Use ## for section headings (two hash symbols, no space between them)
- Put a blank line before and after every ## heading
- Use **bold** for important terms
- Use bullet points with "- " where appropriate
- Separate paragraphs with a blank line

OUTPUT: blog content only, no extra commentary."""

    payload = {
        "model": "qwen/qwen3.5-122b-a10b",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.6
    }

    response = requests.post(INVOKE_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


# =========================
# 🔹 API: GENERATE KEYWORDS
# =========================
class GenerateKeywords(APIView):
    @require_token
    def post(self, request):
        title = request.data.get("title")
        if not title:
            return Response(
                {"success": False, "message": "Title is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            keywords = generate_keywords(title)
            return Response({"success": True, "data": keywords}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================
# 🔹 API: GENERATE BLOG
# =========================
class GenerateBlog(APIView):
    @require_token
    def post(self, request):
        title    = request.data.get('title')
        keywords = request.data.get('keywords')
        tone     = request.data.get('tone')
        length   = request.data.get('length')

        if not title or not tone or not length:
            return Response(
                {"success": False, "message": "Title, tone, and length are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            if not keywords:
                keywords = generate_keywords(title)

            blog_content = generate_blog_content(title, keywords, tone, length)

            return Response({
                "success": True,
                "data": {"title": title, "keywords": keywords, "content": blog_content}
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
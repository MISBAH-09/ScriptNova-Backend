from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ScriptNova.middleware.auth import require_token
import os
import requests

# 🔐 Environment Variables
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

# 🔐 Common Headers
headers = {
    "Authorization": f"Bearer {NVIDIA_API_KEY}",
    "Content-Type": "application/json"
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

    prompt = f"""
    You are an expert SEO blog writer.
    Write a {length} blog post.
    Title: {title}
    Keywords: {keywords_str}
    Tone: {tone}

    STRUCTURE:
    - Title
    - Introduction
    - 2 to 3 headings (##)
    - Detailed paragraphs under each heading
    - Conclusion

    SEO RULES:
    - Use keywords naturally
    - Avoid keyword stuffing
    - Make it engaging and readable

    Output only blog content.
    """

    payload = {
        "model": "qwen/qwen3.5-122b-a10b",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 2000,
        "temperature": 0.6
    }

    response = requests.post(INVOKE_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


# =========================
# 🔹 API: GENERATE KEYWORDS
# =========================
class GenerateKeywords(APIView):
    @require_token
    def post(self, request):
        print("Received request for keyword generation")  # Debugging log
        title = request.data.get("title")
        print(f"Received title for keyword generation: {title}")  # Debugging log
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
        title = request.data.get('title')
        keywords = request.data.get('keywords')
        tone = request.data.get('tone')
        length = request.data.get('length')

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
        

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from ScriptNova.middleware.auth import require_token
# import os
# import re
# from django.core.files import File
# import requests
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from ScriptNova.middleware.auth import require_token

# import requests
# import os

# # 🔐 Environment Variables
# NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
# INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

# # 🔐 Common Headers
# headers = {
#     "Authorization": f"Bearer {NVIDIA_API_KEY}",
#     "Content-Type": "application/json"
# }


# # =========================
# # 🔹 KEYWORD GENERATOR
# # =========================
# def generate_keywords(title):
#     prompt = f"""
#     Generate 8 SEO-friendly keywords for a blog titled:
#     "{title}"

#     Return only a comma-separated list.
#     """

#     payload = {
#         "model": "qwen/qwen3.5-122b-a10b",
#         "messages": [{"role": "user", "content": prompt}],
#         "max_tokens": 200,
#         "temperature": 0.5
#     }

#     response = requests.post(INVOKE_URL, headers=headers, json=payload, timeout=30)
#     response.raise_for_status()
#     data = response.json()

#     keywords = data["choices"][0]["message"]["content"]

#     # Convert string → list
#     return [k.strip() for k in keywords.split(",") if k.strip()]


# # =========================
# # 🔹 BLOG GENERATOR
# # =========================
# def generate_blog_content(title, keywords, tone, length):

#     keywords_str = ", ".join(keywords) if isinstance(keywords, list) else keywords

#     prompt = f"""
#     You are an expert SEO blog writer.

#     Write a {length} blog post.

#     Title: {title}
#     Keywords: {keywords_str}
#     Tone: {tone}

#     STRUCTURE:
#     - Title
#     - Introduction
#     - 2 to 3 headings (##)
#     - Detailed paragraphs under each heading
#     - Conclusion

#     SEO RULES:
#     - Use keywords naturally
#     - Avoid keyword stuffing
#     - Make it engaging and readable

#     Output only blog content.
#     """

#     payload = {
#         "model": "qwen/qwen3.5-122b-a10b",
#         "messages": [{"role": "user", "content": prompt}],
#         "max_tokens": 2000,
#         "temperature": 0.6
#     }

#     response = requests.post(INVOKE_URL, headers=headers, json=payload, timeout=30)
#     response.raise_for_status()
#     data = response.json()

#     return data["choices"][0]["message"]["content"]


# # =========================
# # 🔹 API: GENERATE KEYWORDS
# # =========================
# class GenerateKeywords(APIView):
#     @require_token
#     def post(self, request):
        
#         title = request.data.get("title")

#         if not title:
#             return Response(
#                 {"success": False, "message": "Title is required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             keywords = generate_keywords(title)

#             return Response({
#                 "success": True,
#                 "data": keywords
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response(
#                 {"success": False, "message": str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


# # =========================
# # 🔹 API: GENERATE BLOG
# # =========================
# class GenerateBlog(APIView):
#     @require_token
#     def post(self, request):

#         title = request.data.get('title')
#         keywords = request.data.get('keywords')
#         tone = request.data.get('tone')
#         length = request.data.get('length')

#         if not title or not tone or not length:
#             return Response(
#                 {"success": False, "message": "Title, tone, and length are required"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )

#         try:
#             # ✅ Auto-generate keywords if not provided
#             if not keywords:
#                 keywords = generate_keywords(title)

#             blog_content = generate_blog_content(title, keywords, tone, length)

#             return Response({
#                 "success": True,
#                 "data": {
#                     "title": title,
#                     "keywords": keywords,
#                     "content": blog_content
#                 }
#             }, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response(
#                 {"success": False, "message": str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
import markdown
import json
import hashlib
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.dateparse import parse_datetime
from django.contrib.auth.models import User
from django.contrib.auth import login
from .models import Note, Comment, LikeRecord
import re

MAX_CONTENT_LENGTH = 200000
MAX_COMMENT_LENGTH = 10000  # 评论内容最大长度
MAX_CONTEXT_TEXT_LENGTH = 100  # 上下文指纹最大长度
MAX_ID_LENGTH = 100  # ID字段最大长度
MAX_PARA_INDEX = 100000  # 段落索引最大值（防止DoS）

def constant_time_compare(val1, val2):
    """Constant-time string comparison to prevent timing attacks."""
    if len(val1) != len(val2):
        return False
    result = 0
    for x, y in zip(val1, val2):
        result |= ord(x) ^ ord(y)
    return result == 0

def validate_id_field(value, field_name, max_length=MAX_ID_LENGTH):
    """Validate ID field format and length."""
    if not value or not isinstance(value, str):
        return False
    if len(value) > max_length:
        return False
    # Allow alphanumeric, dash, underscore, and dot
    if not re.match(r'^[a-zA-Z0-9._-]+$', value):
        return False
    return True

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@csrf_exempt
def api_comments(request):
    if request.method == 'GET':
        site_id = request.GET.get('siteId')
        work_id = request.GET.get('workId')
        chapter_id = request.GET.get('chapterId')
        
        if not all([site_id, work_id, chapter_id]):
            return JsonResponse({'error': 'missing_params'}, status=400)
        
        # Validate ID fields
        if not validate_id_field(site_id, 'siteId') or \
           not validate_id_field(work_id, 'workId') or \
           not validate_id_field(chapter_id, 'chapterId'):
            return JsonResponse({'error': 'invalid_id_format'}, status=400)
            
        comments = Comment.objects.filter(site_id=site_id, work_id=work_id, chapter_id=chapter_id).order_by('created_at')
        
        # Determine current user identity for "liked" status
        current_user_id = None
        ip = get_client_ip(request)
        if ip:
             # Same logic as creation
             ip_hash = hashlib.md5((ip + site_id).encode()).hexdigest()
             current_user_id = f"ip_{ip_hash}"

        # Get set of comment IDs liked by this user
        liked_comment_ids = set()
        if current_user_id:
            liked_comment_ids = set(
                LikeRecord.objects.filter(user_id=current_user_id, comment__in=comments)
                .values_list('comment_id', flat=True)
            )
        
        # Group by para_index
        comments_by_para = {}
        for c in comments:
            idx = str(c.para_index)
            if idx not in comments_by_para:
                comments_by_para[idx] = []
            
            comments_by_para[idx].append({
                'id': c.id,
                'paraIndex': c.para_index,
                'content': c.content,
                'userName': c.user_name,
                'userId': c.user_id,
                'userAvatar': c.user_avatar,
                'createdAt': c.created_at.isoformat(),
                'likes': c.likes,
                'contextText': c.context_text,
                'isLiked': c.id in liked_comment_ids
            })
            
        return JsonResponse({'commentsByPara': comments_by_para})

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            site_id = data.get('siteId')
            work_id = data.get('workId')
            chapter_id = data.get('chapterId')
            para_index = data.get('paraIndex')
            content = data.get('content')
            context_text = data.get('contextText')
            
            # Input validation
            if not all([site_id, work_id, chapter_id]) or para_index is None or not content:
                return JsonResponse({'error': 'missing_fields'}, status=400)
            
            # Validate ID fields
            if not validate_id_field(site_id, 'siteId') or \
               not validate_id_field(work_id, 'workId') or \
               not validate_id_field(chapter_id, 'chapterId'):
                return JsonResponse({'error': 'invalid_id_format'}, status=400)
            
            # Validate para_index
            if not isinstance(para_index, int) or para_index < 0 or para_index > MAX_PARA_INDEX:
                return JsonResponse({'error': 'invalid_para_index'}, status=400)
            
            # Validate content length
            if not isinstance(content, str) or len(content.strip()) == 0:
                return JsonResponse({'error': 'empty_content'}, status=400)
            if len(content) > MAX_COMMENT_LENGTH:
                return JsonResponse({'error': 'content_too_long'}, status=400)
            
            # Validate context_text if provided
            if context_text and (not isinstance(context_text, str) or len(context_text) > MAX_CONTEXT_TEXT_LENGTH):
                return JsonResponse({'error': 'invalid_context_text'}, status=400)
            
            # Sanitize content (strip whitespace)
            content = content.strip()
            if context_text:
                context_text = context_text.strip()
                
            # Identity logic
            DEFAULT_ANONYMOUS_NAME = "匿名"
            GUEST_NAME_PREFIX = "访客-"
            
            user_name = DEFAULT_ANONYMOUS_NAME
            user_id = None
            ip = get_client_ip(request)
            
            if ip:
                ip_hash = hashlib.md5((ip + site_id).encode()).hexdigest()
                user_id = f"ip_{ip_hash}"
                user_name = f"{GUEST_NAME_PREFIX}{ip_hash[:6]}"
            
            comment = Comment.objects.create(
                site_id=site_id,
                work_id=work_id,
                chapter_id=chapter_id,
                para_index=para_index,
                content=content,
                user_name=user_name,
                user_id=user_id,
                context_text=context_text,
                ip=ip
            )
            
            return JsonResponse({
                'id': comment.id,
                'paraIndex': comment.para_index,
                'content': comment.content,
                'userName': comment.user_name,
                'userId': comment.user_id,
                'createdAt': comment.created_at.isoformat(),
                'likes': comment.likes
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'invalid_json'}, status=400)
        except Exception as e:
            # Don't expose internal error details
            return JsonResponse({'error': 'internal_error'}, status=500)

    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            comment_id = data.get('commentId')
            work_id = data.get('workId')  # work_id is the note hashcode
            site_id = data.get('siteId')
            chapter_id = data.get('chapterId')
            
            if not comment_id:
                return JsonResponse({'error': 'missing_fields'}, status=400)
            
            # Validate comment_id is numeric
            try:
                comment_id = int(comment_id)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'invalid_comment_id'}, status=400)
            
            comment = get_object_or_404(Comment, id=comment_id)
            
            # Verify comment belongs to the requested work/chapter if provided
            if work_id and comment.work_id != work_id:
                return JsonResponse({'error': 'comment_mismatch'}, status=400)
            if site_id and comment.site_id != site_id:
                return JsonResponse({'error': 'comment_mismatch'}, status=400)
            if chapter_id and comment.chapter_id != chapter_id:
                return JsonResponse({'error': 'comment_mismatch'}, status=400)
            
            # Check if user is admin
            is_admin = request.user.is_staff
            
            # Check if user is the note author (using constant-time comparison)
            is_author = False
            if work_id and validate_id_field(work_id, 'workId', max_length=32):
                try:
                    note = Note.objects.get(hashcode=work_id)
                    # Check edit token from cookie or request (constant-time comparison)
                    edit_token = request.COOKIES.get(f'edit_token_{work_id}') or data.get('editToken')
                    if edit_token and constant_time_compare(str(edit_token), str(note.edit_token)):
                        is_author = True
                except Note.DoesNotExist:
                    pass
            
            # Allow deletion if user is admin or author
            if not (is_admin or is_author):
                return JsonResponse({'error': 'permission_denied'}, status=403)
            
            Comment.objects.filter(id=comment_id).delete()
            return JsonResponse({'success': True})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'invalid_json'}, status=400)
        except Exception as e:
            # Don't expose internal error details
            return JsonResponse({'error': 'internal_error'}, status=500)
    
    return JsonResponse({'error': 'method not allowed'}, status=405)

@csrf_exempt
def api_like_comment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            comment_id = data.get('commentId')
            site_id = data.get('siteId')
            
            if not comment_id or not site_id:
                 return JsonResponse({'error': 'missing_fields'}, status=400)
            
            # Validate site_id format
            if not validate_id_field(site_id, 'siteId'):
                return JsonResponse({'error': 'invalid_id_format'}, status=400)
            
            # Validate comment_id is numeric
            try:
                comment_id = int(comment_id)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'invalid_comment_id'}, status=400)

            comment = get_object_or_404(Comment, id=comment_id)
            
            # Verify comment belongs to the requested site
            if comment.site_id != site_id:
                return JsonResponse({'error': 'comment_mismatch'}, status=400)
            
            # Identity logic
            ip = get_client_ip(request)
            user_id = None
            
            if ip:
                ip_hash = hashlib.md5((ip + site_id).encode()).hexdigest()
                user_id = f"ip_{ip_hash}"
            
            if not user_id:
                 return JsonResponse({'error': 'cannot_identify_user'}, status=400)

            # Check if already liked
            if LikeRecord.objects.filter(comment=comment, user_id=user_id).exists():
                return JsonResponse({'error': 'already_liked', 'likes': comment.likes}, status=400)
            
            # Create record and increment
            try:
                LikeRecord.objects.create(comment=comment, user_id=user_id, ip=ip)
                comment.likes += 1
                comment.save()
            except Exception as e:
                # Handle race condition or unique constraint violation
                return JsonResponse({'error': 'already_liked', 'likes': comment.likes}, status=400)
            
            return JsonResponse({'likes': comment.likes})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'invalid_json'}, status=400)
        except Exception as e:
            # Don't expose internal error details
            return JsonResponse({'error': 'internal_error'}, status=500)
    return JsonResponse({'error': 'method_not_allowed'}, status=405)

def apply_strikethrough(md_text):
    # Replace ~~something~~ with <del>something</del>
    pattern = re.compile(r'~~(.*?)~~', re.DOTALL)
    return pattern.sub(r'<del>\1</del>', md_text)

def process_markdown_links(html_content, target="_blank"):
    # Keep existing link processing
    pattern = r'<a(.*?)href="(.*?)"(.*?)>'
    replacement = f'<a\\1href="\\2"\\3 target="{target}" rel="noopener noreferrer">'
    html_content = re.sub(pattern, replacement, html_content)

    # Existing anchor-based YouTube embed:
    anchor_yt_pattern = r'<p><a href="https?://(?:www\.)?youtu\.be/([^"]+)".*?>.*?</a></p>'
    anchor_yt_replacement = (
        r'<iframe width="560" height="315" '
        r'src="https://www.youtube.com/embed/\1" '
        r'frameborder="0" allowfullscreen></iframe>'
    )
    html_content = re.sub(anchor_yt_pattern, anchor_yt_replacement, html_content)

    # **Added** plain-text YouTube embed (no anchor tag):
    plain_yt_pattern = r'<p>https?://(?:www\.)?youtu\.be/([^<]+)</p>'
    plain_yt_replacement = (
        r'<iframe width="560" height="315" '
        r'src="https://www.youtube.com/embed/\1" '
        r'frameborder="0" allowfullscreen></iframe>'
    )
    html_content = re.sub(plain_yt_pattern, plain_yt_replacement, html_content)

    return html_content

def home(request):
    # If no users exist, redirect to setup page
    if not User.objects.exists():
        return redirect('setup_admin')
    return render(request, 'tapnote/editor.html')

@csrf_exempt
def setup_admin(request):
    # Security check: only allow if no users exist
    if User.objects.exists():
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email', '')
        
        if username and password:
            user = User.objects.create_superuser(username=username, email=email, password=password)
            login(request, user)
            return redirect('home')
            
    return render(request, 'tapnote/setup.html')

@csrf_exempt
def publish(request):
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        title = request.POST.get('title', '').strip()
        author = request.POST.get('author', '').strip()
        link_target = request.POST.get('link_target', '_blank')
        
        if len(content) > MAX_CONTENT_LENGTH:
            return render(request, 'tapnote/editor.html', {
                'error': f'Content exceeds the limit of {MAX_CONTENT_LENGTH} characters.',
                'note': {'content': content, 'title': title, 'author': author, 'link_target': link_target}
            })
        if content:
            note = Note.objects.create(content=content, title=title, author=author, link_target=link_target)
            response = redirect('view_note', hashcode=note.hashcode)
            # Set cookie with SameSite=Lax for robustness
            response.set_cookie(f'edit_token_{note.hashcode}', note.edit_token, max_age=31536000, samesite='Lax')
            return response
    return redirect('home')

def view_note(request, hashcode):
    # Validate hashcode format (allow 8-32 chars, alphanumeric)
    if not re.match(r'^[a-zA-Z0-9]{8,32}$', hashcode):
        raise Http404()
    
    note = get_object_or_404(Note, hashcode=hashcode)
    
    # FIRST apply strikethrough by regex
    raw_with_del = apply_strikethrough(note.content)

    # THEN convert with standard Markdown (no strikethrough extension)
    md = markdown.Markdown(extensions=['fenced_code', 'tables', 'footnotes'])
    html_content = md.convert(raw_with_del)
    html_content = process_markdown_links(html_content, target=note.link_target)
    
    # Use constant-time comparison for edit token
    cookie_token = request.COOKIES.get(f'edit_token_{note.hashcode}')
    url_token = request.GET.get('token')
    
    token_is_valid = False
    if url_token and constant_time_compare(str(url_token), str(note.edit_token)):
        token_is_valid = True
    elif cookie_token and constant_time_compare(str(cookie_token), str(note.edit_token)):
        token_is_valid = True
        
    can_edit = token_is_valid
    
    # Extract title and description for meta tags
    lines = note.content.strip().split('\n')
    full_text = note.content.strip()
    meta_title = "TapNote"
    meta_description = "A simple markdown note."

    # Determine Title
    if note.title:
        meta_title = note.title
    elif lines:
        # First line as title, clean up markdown headers
        candidate_title = re.sub(r'^#+\s*', '', lines[0]).strip()
        if candidate_title:
            meta_title = candidate_title[:60]

    # Determine Description
    if lines:
        if note.title:
            # If we have an explicit title, the description starts from the beginning of content
            meta_description = full_text[:200]
        elif len(lines) > 1:
            # If title was inferred from first line, skip it in description
            meta_description = full_text[len(lines[0]):].strip()[:200]
        else:
            meta_description = full_text[:200]
    
    if note.author:
        meta_description = f"By {note.author}. {meta_description}"

    # Try to find an image for social preview
    meta_image = None
    # Match markdown image ![alt](url) or HTML <img src="url">
    img_match = re.search(r'!\[.*?\]\((.*?)\)|<img.*?src=["\'](.*?)["\']', full_text)
    if img_match:
        # img_match.group(1) is markdown url, group(2) is html src
        meta_image = img_match.group(1) or img_match.group(2)

    response = render(request, 'tapnote/view_note.html', {
        'note': note,
        'content': html_content,
        'can_edit': can_edit,
        'meta_title': meta_title,
        'meta_description': meta_description,
        'meta_image': meta_image,
    })
    
    # Auto-refresh/set cookie if valid URL token is provided
    # This ensures robustness: if user visits with token link, browser remembers permission
    if url_token and token_is_valid:
        response.set_cookie(f'edit_token_{note.hashcode}', note.edit_token, max_age=31536000, samesite='Lax')
        
    return response

@csrf_exempt
def edit_note(request, hashcode):
    # Validate hashcode format (allow 8-32 chars, alphanumeric)
    if not re.match(r'^[a-zA-Z0-9]{8,32}$', hashcode):
        raise Http404()
    
    note = get_object_or_404(Note, hashcode=hashcode)
    edit_token = request.COOKIES.get(f'edit_token_{note.hashcode}')
    url_token = request.GET.get('token')
    
    # Use constant-time comparison
    if not ((edit_token and constant_time_compare(str(edit_token), str(note.edit_token))) or
            (url_token and constant_time_compare(str(url_token), str(note.edit_token)))):
        raise Http404()
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        title = request.POST.get('title', '').strip()
        author = request.POST.get('author', '').strip()
        link_target = request.POST.get('link_target', '_blank')
        
        if len(content) > MAX_CONTENT_LENGTH:
            return render(request, 'tapnote/editor.html', {
                'note': note,
                'error': f'Content exceeds the limit of {MAX_CONTENT_LENGTH} characters.'
            })
            
        if content:
            note.content = content
            note.title = title
            note.author = author
            note.link_target = link_target
            note.save()
            response = redirect('view_note', hashcode=note.hashcode)
            # Refresh cookie on edit
            response.set_cookie(f'edit_token_{note.hashcode}', note.edit_token, max_age=31536000, samesite='Lax')
            return response
    
    return render(request, 'tapnote/editor.html', {'note': note})

def handler404(request, exception):
    return render(request, 'tapnote/404.html', status=404)

@staff_member_required
def migration(request):
    return render(request, 'tapnote/migration.html')

@staff_member_required
def export_data(request):
    notes = Note.objects.all()
    data = []
    for note in notes:
        data.append({
            'hashcode': note.hashcode,
            'content': note.content,
            'title': note.title,
            'author': note.author,
            'link_target': note.link_target,
            'edit_token': note.edit_token,
            'created_at': note.created_at.isoformat(),
            'updated_at': note.updated_at.isoformat(),
        })
    
    response = HttpResponse(
        json.dumps(data, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = 'attachment; filename="tapnote_backup.json"'
    return response

@csrf_exempt
@staff_member_required
def import_data(request):
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            json_file = request.FILES['file']
            data = json.load(json_file)
            
            count = 0
            for item in data:
                defaults = {
                    'content': item['content'],
                    'edit_token': item['edit_token'],
                }
                if 'link_target' in item:
                    defaults['link_target'] = item['link_target']
                if 'created_at' in item:
                    defaults['created_at'] = parse_datetime(item['created_at'])
                
                note, created = Note.objects.update_or_create(
                    hashcode=item['hashcode'],
                    defaults=defaults
                )
                
                # Force update updated_at if present
                if 'updated_at' in item:
                    updated_at = parse_datetime(item['updated_at'])
                    Note.objects.filter(pk=note.pk).update(updated_at=updated_at)
                
                count += 1
                
            return render(request, 'tapnote/migration.html', {'success': f'Successfully imported {count} notes.'})
        except Exception as e:
            return render(request, 'tapnote/migration.html', {'error': f'Error importing file: {str(e)}'})
            
    return redirect('migration')

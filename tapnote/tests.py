from django.test import TestCase, Client
from django.urls import reverse
from django.http import Http404
from .models import Note
from .views import apply_strikethrough, process_markdown_links
import uuid


class NoteModelTests(TestCase):
    """Test cases for the Note model"""

    def test_note_creation(self):
        """Test that a note is created successfully"""
        note = Note.objects.create(content="Test content")
        self.assertIsNotNone(note.hashcode)
        self.assertIsNotNone(note.edit_token)
        self.assertEqual(note.content, "Test content")
        self.assertEqual(len(note.hashcode), 32)
        self.assertEqual(len(note.edit_token), 32)

    def test_note_hashcode_uniqueness(self):
        """Test that each note gets a unique hashcode"""
        note1 = Note.objects.create(content="Content 1")
        note2 = Note.objects.create(content="Content 2")
        self.assertNotEqual(note1.hashcode, note2.hashcode)
        self.assertNotEqual(note1.edit_token, note2.edit_token)

    def test_note_str_representation(self):
        """Test the string representation of a note"""
        note = Note.objects.create(content="Test")
        expected = f"Note {note.hashcode}"
        self.assertEqual(str(note), expected)

    def test_note_auto_timestamps(self):
        """Test that timestamps are automatically set"""
        note = Note.objects.create(content="Test")
        self.assertIsNotNone(note.created_at)
        self.assertIsNotNone(note.updated_at)

    def test_note_update_timestamp(self):
        """Test that updated_at changes on save"""
        note = Note.objects.create(content="Original")
        original_updated = note.updated_at
        note.content = "Updated"
        note.save()
        self.assertGreater(note.updated_at, original_updated)

    def test_custom_hashcode_preserved(self):
        """Test that custom hashcode is preserved if provided"""
        custom_hash = "custom123456789012345678901234"
        note = Note(content="Test", hashcode=custom_hash)
        note.save()
        self.assertEqual(note.hashcode, custom_hash)

    def test_custom_edit_token_preserved(self):
        """Test that custom edit token is preserved if provided"""
        custom_token = "token1234567890123456789012345678901234567890123456789012"
        note = Note(content="Test", edit_token=custom_token)
        note.save()
        self.assertEqual(note.edit_token, custom_token)


class HelperFunctionsTests(TestCase):
    """Test cases for helper functions"""

    def test_apply_strikethrough_basic(self):
        """Test basic strikethrough conversion"""
        text = "This is ~~deleted~~ text"
        result = apply_strikethrough(text)
        self.assertEqual(result, "This is <del>deleted</del> text")

    def test_apply_strikethrough_multiple(self):
        """Test multiple strikethroughs in one text"""
        text = "~~First~~ and ~~Second~~"
        result = apply_strikethrough(text)
        self.assertEqual(result, "<del>First</del> and <del>Second</del>")

    def test_apply_strikethrough_multiline(self):
        """Test strikethrough across multiple lines"""
        text = "~~Line one\nLine two~~"
        result = apply_strikethrough(text)
        self.assertEqual(result, "<del>Line one\nLine two</del>")

    def test_apply_strikethrough_no_match(self):
        """Test text without strikethrough remains unchanged"""
        text = "Normal text without strikethrough"
        result = apply_strikethrough(text)
        self.assertEqual(result, text)

    def test_process_markdown_links_target_blank(self):
        """Test that links get target blank added"""
        html = '<a href="http://example.com">Link</a>'
        result = process_markdown_links(html)
        self.assertIn('target="_blank"', result)
        self.assertIn('rel="noopener noreferrer"', result)

    def test_process_markdown_links_youtube_short(self):
        """Test YouTube short URL conversion to embed"""
        html = '<p><a href="https://youtu.be/dQw4w9WgXcQ">Video</a></p>'
        result = process_markdown_links(html)
        self.assertIn('<iframe', result)
        self.assertIn('youtube.com/embed/dQw4w9WgXcQ', result)
        self.assertIn('width="560"', result)
        self.assertIn('height="315"', result)

    def test_process_markdown_links_youtube_plain(self):
        """Test plain YouTube URL conversion to embed"""
        html = '<p>https://youtu.be/dQw4w9WgXcQ</p>'
        result = process_markdown_links(html)
        self.assertIn('<iframe', result)
        self.assertIn('youtube.com/embed/dQw4w9WgXcQ', result)

    def test_process_markdown_links_youtube_www(self):
        """Test www.youtu.be URL handling"""
        html = '<p><a href="https://www.youtu.be/abc123">Video</a></p>'
        result = process_markdown_links(html)
        self.assertIn('youtube.com/embed/abc123', result)

    def test_process_markdown_links_no_youtube(self):
        """Test regular links are not converted to iframe"""
        html = '<a href="http://example.com">Regular Link</a>'
        result = process_markdown_links(html)
        self.assertNotIn('<iframe', result)
        self.assertIn('example.com', result)


class ViewsTests(TestCase):
    """Test cases for views"""

    def setUp(self):
        """Set up test client and sample note"""
        self.client = Client()
        self.note = Note.objects.create(content="# Test Note\n\nThis is test content.")

    def test_home_view(self):
        """Test home view returns correct template"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tapnote/editor.html')

    def test_publish_view_get_redirects(self):
        """Test GET request to publish redirects to home"""
        response = self.client.get(reverse('publish'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))

    def test_publish_view_post_creates_note(self):
        """Test POST to publish creates a new note"""
        initial_count = Note.objects.count()
        response = self.client.post(reverse('publish'), {'content': 'New note content'})
        self.assertEqual(Note.objects.count(), initial_count + 1)
        self.assertEqual(response.status_code, 302)
        
        new_note = Note.objects.latest('created_at')
        self.assertEqual(new_note.content, 'New note content')
        self.assertRedirects(response, reverse('view_note', args=[new_note.hashcode]))

    def test_publish_view_post_sets_cookie(self):
        """Test that publish sets edit token cookie"""
        response = self.client.post(reverse('publish'), {'content': 'Test content'})
        note = Note.objects.latest('created_at')
        cookie_name = f'edit_token_{note.hashcode}'
        self.assertIn(cookie_name, response.cookies)
        self.assertEqual(response.cookies[cookie_name].value, note.edit_token)

    def test_publish_view_empty_content_redirects(self):
        """Test publishing empty content redirects to home"""
        response = self.client.post(reverse('publish'), {'content': ''})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))

    def test_view_note_success(self):
        """Test viewing a note works correctly"""
        response = self.client.get(reverse('view_note', args=[self.note.hashcode]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tapnote/view_note.html')
        self.assertIn('note', response.context)
        self.assertIn('content', response.context)
        self.assertEqual(response.context['note'], self.note)

    def test_view_note_invalid_hashcode_404(self):
        """Test viewing non-existent note returns 404"""
        response = self.client.get(reverse('view_note', args=['invalidhash']))
        self.assertEqual(response.status_code, 404)

    def test_view_note_markdown_rendering(self):
        """Test that markdown is properly rendered in view"""
        response = self.client.get(reverse('view_note', args=[self.note.hashcode]))
        html_content = response.context['content']
        self.assertIn('<h1>Test Note</h1>', html_content)
        self.assertIn('<p>This is test content.</p>', html_content)

    def test_view_note_can_edit_with_cookie(self):
        """Test can_edit flag is True with correct cookie"""
        self.client.cookies[f'edit_token_{self.note.hashcode}'] = self.note.edit_token
        response = self.client.get(reverse('view_note', args=[self.note.hashcode]))
        self.assertTrue(response.context['can_edit'])

    def test_view_note_can_edit_with_token_param(self):
        """Test can_edit flag is True with token parameter"""
        url = reverse('view_note', args=[self.note.hashcode]) + f'?token={self.note.edit_token}'
        response = self.client.get(url)
        self.assertTrue(response.context['can_edit'])

    def test_view_note_cannot_edit_without_token(self):
        """Test can_edit flag is False without token"""
        response = self.client.get(reverse('view_note', args=[self.note.hashcode]))
        self.assertFalse(response.context['can_edit'])

    def test_view_note_strikethrough(self):
        """Test strikethrough rendering in view"""
        note = Note.objects.create(content="~~Deleted text~~")
        response = self.client.get(reverse('view_note', args=[note.hashcode]))
        self.assertIn('<del>Deleted text</del>', response.context['content'])

    def test_view_note_footnotes(self):
        """Test footnote rendering in view"""
        content = "Here is a footnote reference[^1]\n\n[^1]: Here is the footnote."
        note = Note.objects.create(content=content)
        response = self.client.get(reverse('view_note', args=[note.hashcode]))
        html = response.context['content']
        
        # Check for footnote reference link
        self.assertIn('sup id="fnref:1"', html)
        self.assertIn('href="#fn:1"', html)
        
        # Check for footnote definition at the bottom
        self.assertIn('div class="footnote"', html)
        self.assertIn('id="fn:1"', html)
        self.assertIn('Here is the footnote', html)

    def test_edit_note_get_with_valid_cookie(self):
        """Test GET request to edit with valid cookie"""
        self.client.cookies[f'edit_token_{self.note.hashcode}'] = self.note.edit_token
        response = self.client.get(reverse('edit_note', args=[self.note.hashcode]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tapnote/editor.html')
        self.assertEqual(response.context['note'], self.note)

    def test_edit_note_get_with_url_token(self):
        """Test GET request to edit with URL token"""
        url = reverse('edit_note', args=[self.note.hashcode]) + f'?token={self.note.edit_token}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tapnote/editor.html')

    def test_edit_note_get_without_token_404(self):
        """Test GET request to edit without token returns 404"""
        response = self.client.get(reverse('edit_note', args=[self.note.hashcode]))
        self.assertEqual(response.status_code, 404)

    def test_edit_note_get_with_wrong_token_404(self):
        """Test GET request to edit with wrong token returns 404"""
        self.client.cookies[f'edit_token_{self.note.hashcode}'] = 'wrongtoken'
        response = self.client.get(reverse('edit_note', args=[self.note.hashcode]))
        self.assertEqual(response.status_code, 404)

    def test_edit_note_post_updates_content(self):
        """Test POST request updates note content"""
        self.client.cookies[f'edit_token_{self.note.hashcode}'] = self.note.edit_token
        new_content = "Updated content"
        response = self.client.post(
            reverse('edit_note', args=[self.note.hashcode]),
            {'content': new_content}
        )
        self.note.refresh_from_db()
        self.assertEqual(self.note.content, new_content)
        self.assertRedirects(response, reverse('view_note', args=[self.note.hashcode]))

    def test_edit_note_post_empty_content_no_update(self):
        """Test POST with empty content doesn't update"""
        self.client.cookies[f'edit_token_{self.note.hashcode}'] = self.note.edit_token
        original_content = self.note.content
        response = self.client.post(
            reverse('edit_note', args=[self.note.hashcode]),
            {'content': ''}
        )
        self.note.refresh_from_db()
        self.assertEqual(self.note.content, original_content)

    def test_edit_note_invalid_hashcode_404(self):
        """Test editing non-existent note returns 404"""
        response = self.client.get(reverse('edit_note', args=['invalidhash']))
        self.assertEqual(response.status_code, 404)

    def test_handler404(self):
        """Test custom 404 handler"""
        from .views import handler404
        response = self.client.get('/nonexistent-url/')
        self.assertEqual(response.status_code, 404)


class IntegrationTests(TestCase):
    """Integration tests for complete workflows"""

    def setUp(self):
        """Set up test client"""
        self.client = Client()

    def test_complete_note_lifecycle(self):
        """Test creating, viewing, and editing a note"""
        # Create note
        create_response = self.client.post(reverse('publish'), {'content': 'Initial content'})
        self.assertEqual(create_response.status_code, 302)
        
        # Get the created note
        note = Note.objects.latest('created_at')
        
        # View note
        view_response = self.client.get(reverse('view_note', args=[note.hashcode]))
        self.assertEqual(view_response.status_code, 200)
        
        # Edit note with cookie set from creation
        edit_response = self.client.post(
            reverse('edit_note', args=[note.hashcode]),
            {'content': 'Updated content'}
        )
        self.assertEqual(edit_response.status_code, 302)
        
        # Verify update
        note.refresh_from_db()
        self.assertEqual(note.content, 'Updated content')

    def test_markdown_features_integration(self):
        """Test various markdown features work together"""
        content = """# Heading
        
**Bold** and *italic*

- List item 1
- List item 2

~~Strikethrough~~

```python
def hello():
    print("Hello")
```

[Link](http://example.com)

https://youtu.be/test123
"""
        note = Note.objects.create(content=content)
        response = self.client.get(reverse('view_note', args=[note.hashcode]))
        html = response.context['content']
        
        # Check various elements are rendered
        self.assertIn('<h1>Heading</h1>', html)
        self.assertIn('<strong>Bold</strong>', html)
        self.assertIn('<em>italic</em>', html)
        self.assertIn('<li>List item', html)
        self.assertIn('<del>Strikethrough</del>', html)
        self.assertIn('<code', html)
        self.assertIn('target="_blank"', html)
        self.assertIn('youtube.com/embed/test123', html)

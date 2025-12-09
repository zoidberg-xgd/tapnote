from django.test import TestCase, Client, override_settings
from django.urls import reverse
from .models import Note

class CommentConfigTests(TestCase):
    """Test cases for enabling/disabling comments"""

    def setUp(self):
        self.client = Client()
        self.note = Note.objects.create(content="Test content")

    @override_settings(ENABLE_COMMENTS=True)
    def test_comments_enabled(self):
        """Test behavior when comments are enabled"""
        # View note should include script
        response = self.client.get(reverse('view_note', args=[self.note.hashcode]))
        self.assertContains(response, 'paranote.js')
        
        # API should work (returns 400 for missing params instead of 403)
        response = self.client.get(reverse('api_comments'))
        self.assertNotEqual(response.status_code, 403)

    @override_settings(ENABLE_COMMENTS=False)
    def test_comments_disabled(self):
        """Test behavior when comments are disabled"""
        # View note should NOT include script
        response = self.client.get(reverse('view_note', args=[self.note.hashcode]))
        self.assertNotContains(response, 'paranote.js')
        
        # API should return 403 Forbidden
        response = self.client.get(reverse('api_comments'))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'Comments are disabled')

        # Like API should also be disabled
        response = self.client.post(reverse('api_like_comment'))
        self.assertEqual(response.status_code, 403)

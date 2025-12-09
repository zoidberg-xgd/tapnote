from django.test import TestCase, Client
from django.urls import reverse
from .models import Note
from .telegraph import nodes_to_markdown, markdown_to_nodes
import json

class TelegraphHelperTests(TestCase):
    """Test cases for Telegraph Node <-> Markdown conversion helpers"""

    def test_markdown_to_nodes_simple(self):
        md = "Hello world"
        nodes = markdown_to_nodes(md)
        # Expected: [{"tag": "p", "children": ["Hello world"]}] or similar depending on markdown implementation
        self.assertTrue(isinstance(nodes, list))
        # Verify structure roughly
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0]['tag'], 'p')
        self.assertEqual(nodes[0]['children'][0], 'Hello world')

    def test_markdown_to_nodes_complex(self):
        md = "# Title\n\nParagraph with **bold**."
        nodes = markdown_to_nodes(md)
        # Verify we get headers and paragraphs
        # Filter out string nodes (text/newlines) before checking tags
        tags = [n.get('tag') for n in nodes if isinstance(n, dict)]
        self.assertIn('h1', tags)
        self.assertIn('p', tags)
        
    def test_nodes_to_markdown_simple(self):
        nodes = [{'tag': 'p', 'children': ['Hello world']}]
        md = nodes_to_markdown(nodes)
        self.assertIn("Hello world", md)

    def test_nodes_to_markdown_formatting(self):
        nodes = [
            {'tag': 'p', 'children': [
                'Normal ',
                {'tag': 'b', 'children': ['Bold']},
                ' ',
                {'tag': 'i', 'children': ['Italic']}
            ]}
        ]
        md = nodes_to_markdown(nodes)
        self.assertIn("**Bold**", md)
        self.assertIn("*Italic*", md)

    def test_nodes_to_markdown_link(self):
        nodes = [
            {'tag': 'a', 'attrs': {'href': 'https://example.com'}, 'children': ['Link']}
        ]
        md = nodes_to_markdown(nodes)
        self.assertEqual(md, "[Link](https://example.com)")


class TelegraphAPITests(TestCase):
    """Test cases for Telegraph compatible API"""

    def setUp(self):
        self.client = Client()

    def test_create_page_success_json(self):
        """Test creating a page with JSON body"""
        content = [{'tag': 'p', 'children': ['Hello World']}]
        data = {
            'title': 'Test Page',
            'author_name': 'Tester',
            'content': json.dumps(content),
            'return_content': True
        }
        response = self.client.post(
            reverse('api_create_page'),
            data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result['ok'])
        self.assertEqual(result['result']['title'], 'Test Page')
        self.assertEqual(result['result']['author_name'], 'Tester')
        self.assertIn('path', result['result'])
        self.assertEqual(result['result']['content'], content)

        # Verify DB
        note = Note.objects.get(hashcode=result['result']['path'])
        self.assertEqual(note.title, 'Test Page')
        self.assertIn('Hello World', note.content)

    def test_create_page_missing_title(self):
        """Test creating page without title fails"""
        data = {
            'content': json.dumps([{'tag': 'p', 'children': ['Content']}])
        }
        response = self.client.post(
            reverse('api_create_page'),
            data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['ok'])

    def test_create_page_missing_content(self):
        """Test creating page without content fails"""
        data = {
            'title': 'Test'
        }
        response = self.client.post(
            reverse('api_create_page'),
            data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_get_page_success(self):
        """Test retrieving a page"""
        note = Note.objects.create(
            title="My Note",
            content="Some content",
            author="Me"
        )
        response = self.client.get(
            reverse('api_get_page_with_path', kwargs={'path': note.hashcode})
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result['ok'])
        self.assertEqual(result['result']['title'], "My Note")
        self.assertEqual(result['result']['author_name'], "Me")
        # By default content is not returned
        self.assertNotIn('content', result['result'])

    def test_get_page_with_content(self):
        """Test retrieving a page with content"""
        note = Note.objects.create(
            title="My Note",
            content="Some content"
        )
        # Using query parameter
        url = reverse('api_get_page_with_path', kwargs={'path': note.hashcode}) + "?return_content=true"
        response = self.client.get(url)
        
        result = response.json()
        self.assertTrue(result['ok'])
        self.assertIn('content', result['result'])
        self.assertTrue(isinstance(result['result']['content'], list))

    def test_get_page_via_post(self):
        """Test retrieving a page via POST (Telegraph style)"""
        note = Note.objects.create(title="Post Note", content="Content")
        # This one uses the base URL without path param
        response = self.client.post(
            reverse('api_get_page'),
            {'path': note.hashcode, 'return_content': 'true'}
        )
        result = response.json()
        self.assertTrue(result['ok'])
        self.assertEqual(result['result']['title'], "Post Note")
        self.assertIn('content', result['result'])

class TelegraphAccountTests(TestCase):
    """Test cases for Telegraph Account and related features"""

    def setUp(self):
        self.client = Client()

    def test_create_account(self):
        """Test creating a new account"""
        response = self.client.post(
            reverse('api_create_account'),
            {
                'short_name': 'test_user',
                'author_name': 'Test Author'
            },
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result['ok'])
        self.assertEqual(result['result']['short_name'], 'test_user')
        self.assertEqual(result['result']['author_name'], 'Test Author')
        self.assertIn('access_token', result['result'])
        self.assertTrue(len(result['result']['access_token']) > 0)

    def test_get_account_info(self):
        """Test retrieving account info"""
        # Create account first
        create_res = self.client.post(
            reverse('api_create_account'),
            {'short_name': 'test'}
        ).json()
        token = create_res['result']['access_token']

        # Get info
        response = self.client.post(
            reverse('api_get_account_info'),
            {'access_token': token, 'fields': json.dumps(['short_name', 'page_count'])},
            content_type='application/json'
        )
        result = response.json()
        self.assertTrue(result['ok'])
        self.assertEqual(result['result']['short_name'], 'test')
        self.assertEqual(result['result']['page_count'], 0)

    def test_revoke_access_token(self):
        """Test revoking access token"""
        create_res = self.client.post(
            reverse('api_create_account'),
            {'short_name': 'test'}
        ).json()
        old_token = create_res['result']['access_token']

        response = self.client.post(
            reverse('api_revoke_access_token'),
            {'access_token': old_token}
        )
        result = response.json()
        self.assertTrue(result['ok'])
        new_token = result['result']['access_token']
        self.assertNotEqual(old_token, new_token)

        # Verify old token no longer works
        info_res = self.client.post(
            reverse('api_get_account_info'),
            {'access_token': old_token}
        )
        self.assertFalse(info_res.json()['ok'])

    def test_create_page_with_account(self):
        """Test creating a page associated with an account"""
        # Create account
        create_res = self.client.post(
            reverse('api_create_account'),
            {'short_name': 'test', 'author_name': 'My Author'}
        ).json()
        token = create_res['result']['access_token']

        # Create page
        response = self.client.post(
            reverse('api_create_page'),
            {
                'access_token': token,
                'title': 'Account Page',
                'content': json.dumps([{'tag': 'p', 'children': ['Content']}])
            }
        )
        result = response.json()
        self.assertTrue(result['ok'])
        path = result['result']['path']

        # Verify DB association
        note = Note.objects.get(hashcode=path)
        self.assertIsNotNone(note.account)
        self.assertEqual(note.account.short_name, 'test')
        # Should inherit author name if not provided
        self.assertEqual(note.author, 'My Author')

    def test_edit_page(self):
        """Test editing a page with access token"""
        # Create account and page
        create_res = self.client.post(
            reverse('api_create_account'),
            {'short_name': 'test'}
        ).json()
        token = create_res['result']['access_token']

        page_res = self.client.post(
            reverse('api_create_page'),
            {
                'access_token': token,
                'title': 'Original Title',
                'content': json.dumps([{'tag': 'p', 'children': ['Original']}])
            }
        ).json()
        path = page_res['result']['path']

        # Edit page
        response = self.client.post(
            reverse('api_edit_page_with_path', kwargs={'path': path}),
            {
                'access_token': token,
                'title': 'Updated Title',
                'content': json.dumps([{'tag': 'p', 'children': ['Updated']}]),
                'return_content': True
            }
        )
        result = response.json()
        self.assertTrue(result['ok'])
        self.assertEqual(result['result']['title'], 'Updated Title')
        
        # Verify content updated
        note = Note.objects.get(hashcode=path)
        self.assertEqual(note.title, 'Updated Title')
        self.assertIn('Updated', note.content)

    def test_edit_page_permission_denied(self):
        """Test editing a page with wrong access token"""
        # Account 1
        acc1 = self.client.post(reverse('api_create_account'), {'short_name': '1'}).json()
        token1 = acc1['result']['access_token']
        
        # Account 2
        acc2 = self.client.post(reverse('api_create_account'), {'short_name': '2'}).json()
        token2 = acc2['result']['access_token']

        # Page created by Account 1
        page_res = self.client.post(
            reverse('api_create_page'),
            {
                'access_token': token1,
                'title': 'Page 1',
                'content': json.dumps([{'tag': 'p', 'children': ['Content']}])
            }
        ).json()
        path = page_res['result']['path']

        # Try to edit with Token 2
        response = self.client.post(
            reverse('api_edit_page_with_path', kwargs={'path': path}),
            {
                'access_token': token2,
                'title': 'Hacked',
                'content': json.dumps([{'tag': 'p', 'children': ['Hacked']}])
            }
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['ok'])

    def test_get_page_list(self):
        """Test getting page list for account"""
        # Create account
        acc = self.client.post(reverse('api_create_account'), {'short_name': 'test'}).json()
        token = acc['result']['access_token']

        # Create 2 pages
        self.client.post(
            reverse('api_create_page'),
            {'access_token': token, 'title': 'P1', 'content': json.dumps([])}
        )
        self.client.post(
            reverse('api_create_page'),
            {'access_token': token, 'title': 'P2', 'content': json.dumps([])}
        )

        # Get list
        response = self.client.post(
            reverse('api_get_page_list'),
            {'access_token': token}
        )
        result = response.json()
        self.assertTrue(result['ok'])
        self.assertEqual(result['result']['total_count'], 2)
        self.assertEqual(len(result['result']['pages']), 2)
        self.assertEqual(result['result']['pages'][0]['title'], 'P2') # Latest first

    def test_get_views(self):
        """Test view counting"""
        # Create page
        page_res = self.client.post(
            reverse('api_create_page'),
            {'title': 'View Test', 'content': json.dumps([])}
        ).json()
        path = page_res['result']['path']

        # Initial views 0
        response = self.client.post(
            reverse('api_get_views_with_path', kwargs={'path': path})
        )
        self.assertEqual(response.json()['result']['views'], 0)

        # Visit page (simulates view)
        self.client.get(reverse('view_note', kwargs={'hashcode': path}))

        # Check views incremented
        response = self.client.post(
            reverse('api_get_views_with_path', kwargs={'path': path})
        )
        self.assertEqual(response.json()['result']['views'], 1)


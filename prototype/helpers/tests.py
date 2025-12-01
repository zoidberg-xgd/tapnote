from django.test import TestCase, override_settings
from unittest.mock import patch, MagicMock
from .openai_helper import send_prompt_to_openai, parse_json_response
import json


class OpenAIHelperTests(TestCase):
    """Test cases for OpenAI helper functions"""

    @override_settings(OPENAI_API_KEY="test-api-key")
    @patch('prototype.helpers.openai_helper.OpenAI')
    def test_send_prompt_success(self, mock_openai_class):
        """Test successful API call to OpenAI"""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Test response"
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Call function
        result = send_prompt_to_openai(
            system_content="You are a helpful assistant",
            user_prompt="Hello"
        )
        
        # Assertions
        self.assertEqual(result, "Test response")
        mock_openai_class.assert_called_once_with(api_key="test-api-key")
        mock_client.chat.completions.create.assert_called_once()
        
        # Check call arguments
        call_args = mock_client.chat.completions.create.call_args
        self.assertEqual(call_args[1]['model'], 'gpt-4o-mini')
        self.assertEqual(len(call_args[1]['messages']), 2)
        self.assertEqual(call_args[1]['messages'][0]['role'], 'system')
        self.assertEqual(call_args[1]['messages'][1]['role'], 'user')

    @override_settings(OPENAI_API_KEY="test-api-key")
    @patch('prototype.helpers.openai_helper.OpenAI')
    def test_send_prompt_custom_parameters(self, mock_openai_class):
        """Test API call with custom parameters"""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Custom response"
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Call with custom parameters
        result = send_prompt_to_openai(
            system_content="System",
            user_prompt="User",
            model="gpt-4",
            max_tokens=2000,
            temperature=0.5
        )
        
        # Check custom parameters were used
        call_args = mock_client.chat.completions.create.call_args
        self.assertEqual(call_args[1]['model'], 'gpt-4')
        self.assertEqual(call_args[1]['max_tokens'], 2000)
        self.assertEqual(call_args[1]['temperature'], 0.5)

    @override_settings(OPENAI_API_KEY="test-api-key")
    @patch('prototype.helpers.openai_helper.OpenAI')
    def test_send_prompt_no_choices(self, mock_openai_class):
        """Test handling when API returns no choices"""
        # Setup mock with empty choices
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_completion = MagicMock()
        mock_completion.choices = []
        
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Call function
        result = send_prompt_to_openai(
            system_content="System",
            user_prompt="User"
        )
        
        # Should return None
        self.assertIsNone(result)

    @override_settings(OPENAI_API_KEY="test-api-key")
    @patch('prototype.helpers.openai_helper.OpenAI')
    def test_send_prompt_api_error(self, mock_openai_class):
        """Test handling of API errors"""
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        # Call function
        result = send_prompt_to_openai(
            system_content="System",
            user_prompt="User"
        )
        
        # Should return None on error
        self.assertIsNone(result)

    @override_settings(OPENAI_API_KEY="test-api-key")
    @patch('prototype.helpers.openai_helper.OpenAI')
    def test_send_prompt_strips_whitespace(self, mock_openai_class):
        """Test that response content is stripped of whitespace"""
        # Setup mock with whitespace in response
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "  Response with whitespace  \n"
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Call function
        result = send_prompt_to_openai(
            system_content="System",
            user_prompt="User"
        )
        
        # Should be stripped
        self.assertEqual(result, "Response with whitespace")

    def test_parse_json_response_valid(self):
        """Test parsing valid JSON response"""
        json_str = '{"key": "value", "number": 42}'
        result = parse_json_response(json_str)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['key'], 'value')
        self.assertEqual(result['number'], 42)

    def test_parse_json_response_with_markdown(self):
        """Test parsing JSON wrapped in markdown code block"""
        json_str = '```json\n{"key": "value"}\n```'
        result = parse_json_response(json_str)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['key'], 'value')

    def test_parse_json_response_complex(self):
        """Test parsing complex JSON structure"""
        json_str = '''
        {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25}
            ],
            "total": 2
        }
        '''
        result = parse_json_response(json_str)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['total'], 2)
        self.assertEqual(len(result['users']), 2)
        self.assertEqual(result['users'][0]['name'], 'Alice')

    def test_parse_json_response_invalid(self):
        """Test handling invalid JSON"""
        invalid_json = "This is not JSON"
        result = parse_json_response(invalid_json)
        
        self.assertIsNone(result)

    def test_parse_json_response_empty(self):
        """Test handling empty string"""
        result = parse_json_response("")
        
        self.assertIsNone(result)

    def test_parse_json_response_malformed(self):
        """Test handling malformed JSON"""
        malformed = '{"key": "value", "broken": }'
        result = parse_json_response(malformed)
        
        self.assertIsNone(result)

    def test_parse_json_response_nested_arrays(self):
        """Test parsing nested arrays and objects"""
        json_str = '''
        {
            "matrix": [[1, 2], [3, 4]],
            "nested": {
                "deep": {
                    "value": "found"
                }
            }
        }
        '''
        result = parse_json_response(json_str)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['matrix'][0][1], 2)
        self.assertEqual(result['nested']['deep']['value'], 'found')

    def test_parse_json_response_special_characters(self):
        """Test parsing JSON with special characters"""
        json_str = r'{"text": "Line1\nLine2\tTabbed", "emoji": "😀"}'
        result = parse_json_response(json_str)
        
        self.assertIsNotNone(result)
        self.assertIn('\n', result['text'])
        self.assertIn('\t', result['text'])
        self.assertEqual(result['emoji'], '😀')

    def test_parse_json_response_unicode(self):
        """Test parsing JSON with unicode characters"""
        json_str = '{"chinese": "你好", "japanese": "こんにちは"}'
        result = parse_json_response(json_str)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['chinese'], '你好')
        self.assertEqual(result['japanese'], 'こんにちは')


class OpenAIIntegrationTests(TestCase):
    """Integration tests for OpenAI helper workflow"""

    @override_settings(OPENAI_API_KEY="test-api-key")
    @patch('prototype.helpers.openai_helper.OpenAI')
    def test_complete_workflow_with_json(self, mock_openai_class):
        """Test complete workflow: API call and JSON parsing"""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = '```json\n{"result": "success", "data": [1, 2, 3]}\n```'
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Call API
        response = send_prompt_to_openai(
            system_content="Return JSON",
            user_prompt="Give me data"
        )
        
        # Parse response
        parsed = parse_json_response(response)
        
        # Verify complete workflow
        self.assertIsNotNone(response)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['result'], 'success')
        self.assertEqual(parsed['data'], [1, 2, 3])

    @override_settings(OPENAI_API_KEY="test-api-key")
    @patch('prototype.helpers.openai_helper.OpenAI')
    def test_workflow_api_error_handling(self, mock_openai_class):
        """Test workflow when API call fails"""
        # Setup mock to fail
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Network error")
        
        # Call API
        response = send_prompt_to_openai(
            system_content="System",
            user_prompt="User"
        )
        
        # Should get None
        self.assertIsNone(response)
        
        # Attempting to parse None should handle gracefully
        # (In real code, you'd check for None before parsing)
        if response:
            parsed = parse_json_response(response)
        else:
            parsed = None
        
        self.assertIsNone(parsed)

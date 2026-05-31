import pytest
from unittest.mock import patch, MagicMock
from tools.web_search import _web_search_impl as web_search


class TestWebSearch:
    """Test suite for web_search tool."""

    @patch('tools.web_search.DDGS')
    @patch('tools.web_search.span')
    def test_web_search_success(self, mock_span, mock_ddgs_class):
        """Test successful web search with results."""
        # Setup mocks
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)
        
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = [
            {
                'title': 'Test Title 1',
                'body': 'Test description 1',
                'href': 'https://example.com/1'
            },
            {
                'title': 'Test Title 2',
                'body': 'Test description 2',
                'href': 'https://example.com/2'
            }
        ]
        mock_ddgs_class.return_value = mock_ddgs

        result = web_search("test query")

        assert "Test Title 1" in result
        assert "Test description 1" in result
        assert "https://example.com/1" in result
        assert "Test Title 2" in result
        mock_ddgs.text.assert_called_once_with("test query", max_results=10)

    @patch('tools.web_search.DDGS')
    @patch('tools.web_search.span')
    @patch('tools.web_search.time.sleep')
    def test_web_search_no_results_retries(self, mock_sleep, mock_span, mock_ddgs_class):
        """Test web search with no results and retries."""
        # Setup mocks
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)
        
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        # Return empty results for all attempts
        mock_ddgs.text.return_value = []
        mock_ddgs_class.return_value = mock_ddgs

        result = web_search("test query")

        assert "No search results found" in result
        # Should have retried 3 times
        assert mock_ddgs.text.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep between retries

    @patch('tools.web_search.DDGS')
    @patch('tools.web_search.span')
    @patch('tools.web_search.time.sleep')
    def test_web_search_succeeds_on_retry(self, mock_sleep, mock_span, mock_ddgs_class):
        """Test web search that succeeds on second attempt."""
        # Setup mocks
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)
        
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        # First call returns empty, second call returns results
        mock_ddgs.text.side_effect = [
            [],
            [
                {
                    'title': 'Success Title',
                    'body': 'Success description',
                    'href': 'https://example.com/success'
                }
            ]
        ]
        mock_ddgs_class.return_value = mock_ddgs

        result = web_search("test query")

        assert "Success Title" in result
        assert "Success description" in result
        assert mock_ddgs.text.call_count == 2
        assert mock_sleep.call_count == 1  # One sleep between attempts

    @patch('tools.web_search.DDGS')
    @patch('tools.web_search.span')
    @patch('tools.web_search.time.sleep')
    def test_web_search_exception_handling(self, mock_sleep, mock_span, mock_ddgs_class):
        """Test web search exception handling with retries."""
        # Setup mocks
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)
        
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        # Raise exception on all attempts
        mock_ddgs.text.side_effect = Exception("Network error")
        mock_ddgs_class.return_value = mock_ddgs

        result = web_search("test query")

        assert "An error occurred while searching" in result
        assert "Network error" in result
        assert mock_ddgs.text.call_count == 3
        assert mock_sleep.call_count == 2

    @patch('tools.web_search.DDGS')
    @patch('tools.web_search.span')
    def test_web_search_results_with_missing_fields(self, mock_span, mock_ddgs_class):
        """Test web search with results that have missing optional fields."""
        # Setup mocks
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)
        
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = [
            {
                'title': 'Has Title',
                'body': 'No description',
                'href': 'https://example.com/1'
            },
            {
                'title': 'No title',
                'body': 'Has Body',
                'href': 'No URL'
            }
        ]
        mock_ddgs_class.return_value = mock_ddgs

        result = web_search("test query")

        # Should include results that have at least title or body
        assert "Has Title" in result
        assert "Has Body" in result

    @patch('tools.web_search.DDGS')
    @patch('tools.web_search.span')
    def test_web_search_no_valid_results(self, mock_span, mock_ddgs_class):
        """Test web search with results that have no valid data."""
        # Setup mocks
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)
        
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        # Results with no title and no body
        mock_ddgs.text.return_value = [
            {
                'title': 'No title',
                'body': 'No description',
                'href': 'https://example.com/1'
            }
        ]
        mock_ddgs_class.return_value = mock_ddgs

        result = web_search("test query")

        assert "Search completed but no usable results were found" in result

    @patch('tools.web_search.DDGS')
    @patch('tools.web_search.span')
    def test_web_search_calls_span(self, mock_span, mock_ddgs_class):
        """Test that the span context manager is called with correct parameters."""
        # Setup mocks
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)
        
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = [
            {
                'title': 'Test Title',
                'body': 'Test description',
                'href': 'https://example.com'
            }
        ]
        mock_ddgs_class.return_value = mock_ddgs

        web_search("test query")

        # Verify span was called with correct parameters
        mock_span.assert_called_once_with("web_search", "Searching the web for: test query")


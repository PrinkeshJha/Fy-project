import pytest
import os
from unittest.mock import patch, AsyncMock
from app.services.screenshot_service import capture_screenshot, InvalidURLError, WebsiteUnreachableError

@pytest.mark.asyncio
async def test_capture_invalid_url():
    with pytest.raises(InvalidURLError):
        await capture_screenshot("")

@pytest.mark.asyncio
@patch("app.services.screenshot_service.async_playwright")
async def test_capture_screenshot_success(mock_playwright):
    # Setup mock playwright
    mock_p = AsyncMock()
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    
    mock_playwright.return_value.__aenter__.return_value = mock_p
    mock_p.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    
    # Run
    path = await capture_screenshot("https://example.com")
    
    # Assertions
    assert "example.com" in path
    mock_page.goto.assert_called_once()
    mock_page.screenshot.assert_called_once()
    mock_browser.close.assert_called_once()

@pytest.mark.asyncio
@patch("app.services.screenshot_service.async_playwright")
async def test_capture_screenshot_unreachable(mock_playwright):
    mock_p = AsyncMock()
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    
    mock_playwright.return_value.__aenter__.return_value = mock_p
    mock_p.chromium.launch.return_value = mock_browser
    mock_browser.new_context.return_value = mock_context
    mock_context.new_page.return_value = mock_page
    
    # Simulate a network error
    mock_page.goto.side_effect = Exception("net::ERR_NAME_NOT_RESOLVED")
    
    with pytest.raises(WebsiteUnreachableError):
        await capture_screenshot("https://nonexistent12345.com")
        
    mock_browser.close.assert_called_once()

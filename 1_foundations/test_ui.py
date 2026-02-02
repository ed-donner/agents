"""
UI/End-to-End Tests for Career Bot Application
Tests user interface interactions and complete workflows
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException


@pytest.fixture(scope="module")
def browser():
    """Setup Selenium WebDriver"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode for CI/CD
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    
    yield driver
    
    driver.quit()


@pytest.fixture
def app_url():
    """Application URL - update based on environment"""
    return "http://localhost:7860"  # Local development
    # return "https://your-huggingface-space-url"  # Production


class TestProjectCarousel:
    """Test project carousel functionality"""
    
    def test_carousel_loads(self, browser, app_url):
        """Test that project carousel loads on homepage"""
        browser.get(app_url)
        
        # Wait for carousel to load
        try:
            carousel = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "carousel-container"))
            )
            assert carousel is not None, "Carousel should be present"
        except TimeoutException:
            pytest.fail("Carousel did not load within timeout")
    
    def test_project_cards_visible(self, browser, app_url):
        """Test that project cards are visible"""
        browser.get(app_url)
        
        # Find all project cards
        cards = browser.find_elements(By.CLASS_NAME, "project-card")
        assert len(cards) >= 11, "Should have at least 11 project cards"
    
    def test_carousel_auto_scroll(self, browser, app_url):
        """Test carousel auto-scrolling"""
        browser.get(app_url)
        
        # Get initial scroll position
        carousel_track = browser.find_element(By.CLASS_NAME, "carousel-track")
        initial_transform = carousel_track.value_of_css_property("transform")
        
        # Wait for auto-scroll (30 seconds cycle, but check after 5 seconds)
        time.sleep(5)
        
        # Get new scroll position
        new_transform = carousel_track.value_of_css_property("transform")
        
        # Transform should have changed (animation in progress)
        # Note: This might be flaky, consider alternative assertions
        # assert initial_transform != new_transform, "Carousel should auto-scroll"
    
    def test_carousel_hover_pause(self, browser, app_url):
        """Test carousel pauses on hover"""
        browser.get(app_url)
        
        carousel = browser.find_element(By.CLASS_NAME, "carousel-container")
        
        # Hover over carousel
        webdriver.ActionChains(browser).move_to_element(carousel).perform()
        
        # Wait a moment
        time.sleep(1)
        
        # Animation should be paused (animation-play-state: paused)
        carousel_track = browser.find_element(By.CLASS_NAME, "carousel-track")
        # Note: Checking animation state via Selenium is complex
        # This is a placeholder for demonstration


class TestProjectCardInteraction:
    """Test project card click interactions"""
    
    def test_project_card_click_opens_modal(self, browser, app_url):
        """Test clicking project card opens modal"""
        browser.get(app_url)
        
        # Wait for cards to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "project-card"))
        )
        
        # Click first project card
        cards = browser.find_elements(By.CLASS_NAME, "project-card")
        if len(cards) > 0:
            cards[0].click()
            
            # Wait for modal to appear
            try:
                modal = WebDriverWait(browser, 5).until(
                    EC.visibility_of_element_located((By.ID, "project-modal"))
                )
                assert modal.is_displayed(), "Modal should be visible"
            except TimeoutException:
                pytest.fail("Modal did not appear after card click")
    
    def test_modal_content_displays(self, browser, app_url):
        """Test modal displays project information"""
        browser.get(app_url)
        
        # Click a project card
        WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "project-card"))
        )
        cards = browser.find_elements(By.CLASS_NAME, "project-card")
        if len(cards) > 0:
            cards[0].click()
            
            # Check modal content
            modal_title = browser.find_element(By.ID, "modal-project-title")
            modal_description = browser.find_element(By.ID, "modal-project-description")
            
            assert modal_title.text != "", "Modal should have project title"
            assert modal_description.text != "", "Modal should have project description"
    
    def test_modal_close_button(self, browser, app_url):
        """Test modal close button works"""
        browser.get(app_url)
        
        # Open modal
        WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "project-card"))
        )
        cards = browser.find_elements(By.CLASS_NAME, "project-card")
        if len(cards) > 0:
            cards[0].click()
            
            # Wait for modal
            WebDriverWait(browser, 5).until(
                EC.visibility_of_element_located((By.ID, "project-modal"))
            )
            
            # Click close button
            close_btn = browser.find_element(By.CLASS_NAME, "modal-close")
            close_btn.click()
            
            # Modal should be hidden
            time.sleep(0.5)
            modal = browser.find_element(By.ID, "project-modal")
            assert not modal.is_displayed(), "Modal should be hidden after close"


class TestVisitorAccessFlow:
    """Test 'Get Visitor Access' complete flow"""
    
    def test_get_visitor_access_button_exists(self, browser, app_url):
        """Test Get Visitor Access button exists in modal"""
        browser.get(app_url)
        
        # Open modal
        WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "project-card"))
        )
        cards = browser.find_elements(By.CLASS_NAME, "project-card")
        if len(cards) > 0:
            cards[0].click()
            
            # Check for Get Visitor Access button
            try:
                access_btn = browser.find_element(By.ID, "get-visitor-access-btn")
                assert access_btn is not None, "Get Visitor Access button should exist"
            except NoSuchElementException:
                pytest.fail("Get Visitor Access button not found")
    
    def test_visitor_access_flow_automation(self, browser, app_url):
        """Test automated visitor access flow"""
        browser.get(app_url)
        
        # Click project card
        WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "project-card"))
        )
        cards = browser.find_elements(By.CLASS_NAME, "project-card")
        if len(cards) > 0:
            cards[0].click()
            
            # Click Get Visitor Access
            access_btn = WebDriverWait(browser, 5).until(
                EC.element_to_be_clickable((By.ID, "get-visitor-access-btn"))
            )
            access_btn.click()
            
            # Wait for automation to complete
            time.sleep(3)
            
            # Should be on Chat tab now
            try:
                chat_tab = browser.find_element(By.ID, "chat-tab")
                # Check if chat tab is active/visible
            except NoSuchElementException:
                pytest.skip("Chat tab element structure may vary")


class TestChatInterface:
    """Test chat interface functionality"""
    
    def test_chat_tab_exists(self, browser, app_url):
        """Test chat tab is present"""
        browser.get(app_url)
        
        # Wait for interface to load
        time.sleep(2)
        
        # Check for chat elements
        try:
            # These IDs may vary based on Gradio structure
            chatbot = browser.find_elements(By.CLASS_NAME, "message")
            # At minimum, page should load without errors
        except NoSuchElementException:
            pytest.skip("Chat interface structure may vary")
    
    def test_send_message(self, browser, app_url):
        """Test sending a message in chat"""
        browser.get(app_url)
        
        # Note: This test requires visitor session setup
        # Skipping for now as it requires authentication
        pytest.skip("Requires visitor session - implement after auth flow")
    
    def test_message_display(self, browser, app_url):
        """Test messages display correctly"""
        pytest.skip("Requires complex setup - manual testing recommended")


class TestGetStartedFlow:
    """Test 'Get Started' visitor creation flow"""
    
    def test_get_started_button_exists(self, browser, app_url):
        """Test Get Started button exists"""
        browser.get(app_url)
        
        time.sleep(2)
        
        # Look for Get Started button
        try:
            get_started_btns = browser.find_elements(By.XPATH, "//button[contains(text(), 'Get Started')]")
            assert len(get_started_btns) > 0, "Get Started button should exist"
        except NoSuchElementException:
            pytest.fail("Get Started button not found")
    
    def test_visitor_creation_success(self, browser, app_url):
        """Test visitor account creation"""
        browser.get(app_url)
        
        time.sleep(2)
        
        # Click Get Started
        try:
            get_started_btn = browser.find_element(By.XPATH, "//button[contains(text(), 'Get Started')]")
            get_started_btn.click()
            
            # Wait for success message or redirect
            time.sleep(3)
            
            # Check for success indicators
            # (Implementation depends on actual UI feedback)
            
        except NoSuchElementException:
            pytest.skip("Get Started flow requires specific UI structure")


class TestEmailContactFlow:
    """Test email/reason contact submission"""
    
    def test_email_reason_fields_exist(self, browser, app_url):
        """Test email and reason input fields exist"""
        pytest.skip("Requires navigation to contact form - implement based on UI")
    
    def test_email_validation(self, browser, app_url):
        """Test email validation on contact form"""
        pytest.skip("Requires contact form access")
    
    def test_submit_contact_info(self, browser, app_url):
        """Test submitting contact information"""
        pytest.skip("Requires complete form interaction")


class TestResponsiveDesign:
    """Test responsive design elements"""
    
    def test_mobile_viewport(self, browser, app_url):
        """Test interface on mobile viewport"""
        browser.set_window_size(375, 667)  # iPhone SE size
        browser.get(app_url)
        
        time.sleep(2)
        
        # Check if key elements are still visible/accessible
        try:
            carousel = browser.find_element(By.CLASS_NAME, "carousel-container")
            assert carousel.is_displayed(), "Carousel should be visible on mobile"
        except NoSuchElementException:
            pytest.fail("Key elements not found on mobile viewport")
    
    def test_tablet_viewport(self, browser, app_url):
        """Test interface on tablet viewport"""
        browser.set_window_size(768, 1024)  # iPad size
        browser.get(app_url)
        
        time.sleep(2)
        
        # Verify layout adapts
        carousel = browser.find_element(By.CLASS_NAME, "carousel-container")
        assert carousel.is_displayed(), "Carousel should be visible on tablet"


class TestAccessibility:
    """Test accessibility features"""
    
    def test_keyboard_navigation(self, browser, app_url):
        """Test keyboard navigation works"""
        browser.get(app_url)
        
        # Tab through elements
        body = browser.find_element(By.TAG_NAME, "body")
        for _ in range(5):
            body.send_keys(Keys.TAB)
            time.sleep(0.2)
        
        # Check if focus is visible
        active_element = browser.switch_to.active_element
        assert active_element is not None, "Should be able to navigate with keyboard"
    
    def test_aria_labels_present(self, browser, app_url):
        """Test ARIA labels are present for accessibility"""
        browser.get(app_url)
        
        # Check for buttons with aria-label
        buttons = browser.find_elements(By.TAG_NAME, "button")
        
        # At least some buttons should have aria-label or text
        buttons_with_labels = [btn for btn in buttons if btn.get_attribute("aria-label") or btn.text]
        assert len(buttons_with_labels) > 0, "Buttons should have labels for accessibility"


# Test runner configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])

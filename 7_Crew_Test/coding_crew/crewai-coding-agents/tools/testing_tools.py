"""
Test generation and execution tools
"""
from typing import Type, Optional, Dict, Any, List
from pydantic import BaseModel, Field
from crewai_tools import BaseTool


class TestGeneratorInput(BaseModel):
    """Input schema for test generation"""
    language: str = Field(..., description="Programming language")
    test_type: str = Field(..., description="Test type (unit, integration, e2e)")
    target_code: str = Field(..., description="Code to test")
    target_name: str = Field(..., description="Name of function/class to test")


class TestGeneratorTool(BaseTool):
    name: str = "Test Generator Tool"
    description: str = """
    Generates test code for various testing frameworks.
    Supports unit tests, integration tests, and e2e tests.
    Use this tool to create comprehensive test suites.
    """
    args_schema: Type[BaseModel] = TestGeneratorInput
    
    def _run(
        self,
        language: str,
        test_type: str,
        target_code: str,
        target_name: str
    ) -> str:
        """Generate test code"""
        
        generators = {
            ("python", "unit"): self._generate_python_unit,
            ("python", "integration"): self._generate_python_integration,
            ("go", "unit"): self._generate_go_unit,
            ("nodejs", "unit"): self._generate_nodejs_unit,
            ("nodejs", "e2e"): self._generate_nodejs_e2e
        }
        
        generator = generators.get((language.lower(), test_type.lower()))
        if not generator:
            return f"❌ Unsupported combination: {language}/{test_type}"
        
        return generator(target_name, target_code)
    
    def _generate_python_unit(self, target_name: str, target_code: str) -> str:
        """Generate Python unit tests"""
        return f'''"""
Unit tests for {target_name}
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from {target_name.lower()} import {target_name}


class Test{target_name}:
    """Test cases for {target_name}"""
    
    @pytest.fixture
    def instance(self):
        """Create test instance"""
        return {target_name}()
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock external dependencies"""
        return {{
            "db": Mock(),
            "cache": Mock()
        }}
    
    def test_initialization(self, instance):
        """Test proper initialization"""
        assert instance is not None
    
    def test_basic_functionality(self, instance):
        """Test basic functionality"""
        # Arrange
        expected = "expected_result"
        
        # Act
        result = instance.some_method()
        
        # Assert
        assert result == expected
    
    def test_edge_cases(self, instance):
        """Test edge cases"""
        # Test with empty input
        with pytest.raises(ValueError):
            instance.some_method(None)
        
        # Test with invalid input
        with pytest.raises(TypeError):
            instance.some_method(123)
    
    @pytest.mark.parametrize("input_val,expected", [
        ("valid_input", "valid_output"),
        ("another_input", "another_output"),
    ])
    def test_parameterized(self, instance, input_val, expected):
        """Test with multiple input combinations"""
        result = instance.some_method(input_val)
        assert result == expected
    
    @patch("{target_name.lower()}.external_service")
    def test_with_mock(self, mock_service, instance):
        """Test with mocked external service"""
        mock_service.return_value = "mocked_result"
        
        result = instance.method_using_service()
        
        mock_service.assert_called_once()
        assert result == "mocked_result"
    
    @pytest.mark.asyncio
    async def test_async_method(self, instance):
        """Test async method"""
        result = await instance.async_method()
        assert result is not None


class Test{target_name}Integration:
    """Integration tests for {target_name}"""
    
    @pytest.fixture
    def real_dependencies(self):
        """Setup real dependencies for integration tests"""
        # Setup
        yield {{}}
        # Teardown
    
    @pytest.mark.integration
    def test_with_database(self, real_dependencies):
        """Test with real database connection"""
        pass
'''
    
    def _generate_python_integration(self, target_name: str, target_code: str) -> str:
        """Generate Python integration tests"""
        return f'''"""
Integration tests for {target_name} API
"""
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


class TestAPI{target_name}:
    """API integration tests for {target_name}"""
    
    def test_create_{target_name.lower()}(self, client):
        """Test create endpoint"""
        response = client.post(
            "/{target_name.lower()}s",
            json={{"name": "Test", "description": "Test description"}}
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
    
    def test_get_{target_name.lower()}_list(self, client):
        """Test list endpoint"""
        response = client.get("/{target_name.lower()}s")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_{target_name.lower()}_by_id(self, client):
        """Test get by ID endpoint"""
        # Create first
        create_response = client.post(
            "/{target_name.lower()}s",
            json={{"name": "Test"}}
        )
        item_id = create_response.json()["id"]
        
        # Get by ID
        response = client.get(f"/{target_name.lower()}s/{{item_id}}")
        assert response.status_code == 200
    
    def test_update_{target_name.lower()}(self, client):
        """Test update endpoint"""
        # Create first
        create_response = client.post(
            "/{target_name.lower()}s",
            json={{"name": "Test"}}
        )
        item_id = create_response.json()["id"]
        
        # Update
        response = client.put(
            f"/{target_name.lower()}s/{{item_id}}",
            json={{"name": "Updated"}}
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated"
    
    def test_delete_{target_name.lower()}(self, client):
        """Test delete endpoint"""
        # Create first
        create_response = client.post(
            "/{target_name.lower()}s",
            json={{"name": "Test"}}
        )
        item_id = create_response.json()["id"]
        
        # Delete
        response = client.delete(f"/{target_name.lower()}s/{{item_id}}")
        assert response.status_code == 204
        
        # Verify deleted
        get_response = client.get(f"/{target_name.lower()}s/{{item_id}}")
        assert get_response.status_code == 404
    
    def test_not_found(self, client):
        """Test 404 response"""
        response = client.get("/{target_name.lower()}s/99999")
        assert response.status_code == 404
    
    def test_validation_error(self, client):
        """Test validation error"""
        response = client.post(
            "/{target_name.lower()}s",
            json={{}}  # Missing required fields
        )
        assert response.status_code == 422
'''
    
    def _generate_go_unit(self, target_name: str, target_code: str) -> str:
        """Generate Go unit tests"""
        return f'''package main

import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
)

// Mock dependencies
type Mock{target_name}Repository struct {{
    mock.Mock
}}

func (m *Mock{target_name}Repository) Get(id string) (*{target_name}, error) {{
    args := m.Called(id)
    if args.Get(0) == nil {{
        return nil, args.Error(1)
    }}
    return args.Get(0).(*{target_name}), args.Error(1)
}}

func Test{target_name}_Create(t *testing.T) {{
    // Arrange
    mockRepo := new(Mock{target_name}Repository)
    service := New{target_name}Service(mockRepo)
    
    // Act
    result, err := service.Create(&{target_name}{{Name: "Test"}})
    
    // Assert
    assert.NoError(t, err)
    assert.NotNil(t, result)
}}

func Test{target_name}_Get(t *testing.T) {{
    // Arrange
    mockRepo := new(Mock{target_name}Repository)
    mockRepo.On("Get", "123").Return(&{target_name}{{ID: "123", Name: "Test"}}, nil)
    
    service := New{target_name}Service(mockRepo)
    
    // Act
    result, err := service.Get("123")
    
    // Assert
    assert.NoError(t, err)
    assert.Equal(t, "123", result.ID)
    mockRepo.AssertExpectations(t)
}}

func Test{target_name}_Get_NotFound(t *testing.T) {{
    // Arrange
    mockRepo := new(Mock{target_name}Repository)
    mockRepo.On("Get", "999").Return(nil, ErrNotFound)
    
    service := New{target_name}Service(mockRepo)
    
    // Act
    result, err := service.Get("999")
    
    // Assert
    assert.Error(t, err)
    assert.Nil(t, result)
}}

// Table-driven tests
func Test{target_name}_Validation(t *testing.T) {{
    tests := []struct {{
        name    string
        input   *{target_name}
        wantErr bool
    }}{{
        {{"valid input", &{target_name}{{Name: "Test"}}, false}},
        {{"empty name", &{target_name}{{Name: ""}}, true}},
        {{"nil input", nil, true}},
    }}
    
    for _, tt := range tests {{
        t.Run(tt.name, func(t *testing.T) {{
            err := Validate{target_name}(tt.input)
            if tt.wantErr {{
                assert.Error(t, err)
            }} else {{
                assert.NoError(t, err)
            }}
        }})
    }}
}}
'''
    
    def _generate_nodejs_unit(self, target_name: str, target_code: str) -> str:
        """Generate Node.js unit tests with Jest"""
        return f'''/**
 * Unit tests for {target_name}
 */
import {{ describe, it, expect, beforeEach, jest }} from '@jest/globals';
import {{ {target_name} }} from './{target_name.lower()}';

describe('{target_name}', () => {{
    let instance: {target_name};
    
    beforeEach(() => {{
        instance = new {target_name}();
    }});
    
    describe('initialization', () => {{
        it('should create instance', () => {{
            expect(instance).toBeDefined();
        }});
    }});
    
    describe('basic functionality', () => {{
        it('should perform basic operation', () => {{
            const result = instance.someMethod();
            expect(result).toBeDefined();
        }});
        
        it('should handle valid input', () => {{
            const result = instance.process('valid');
            expect(result).toBe('expected');
        }});
    }});
    
    describe('error handling', () => {{
        it('should throw on invalid input', () => {{
            expect(() => instance.process(null)).toThrow();
        }});
        
        it('should handle empty input', () => {{
            expect(() => instance.process('')).toThrow('Input cannot be empty');
        }});
    }});
    
    describe('with mocks', () => {{
        it('should call external service', async () => {{
            const mockService = jest.fn().mockResolvedValue('mocked');
            instance.setService(mockService);
            
            const result = await instance.callService();
            
            expect(mockService).toHaveBeenCalled();
            expect(result).toBe('mocked');
        }});
    }});
    
    describe.each([
        ['input1', 'output1'],
        ['input2', 'output2'],
    ])('parameterized tests', (input, expected) => {{
        it(`should return ${{expected}} for ${{input}}`, () => {{
            const result = instance.transform(input);
            expect(result).toBe(expected);
        }});
    }});
}});
'''
    
    def _generate_nodejs_e2e(self, target_name: str, target_code: str) -> str:
        """Generate Node.js E2E tests with Playwright"""
        return f'''/**
 * E2E tests for {target_name}
 */
import {{ test, expect }} from '@playwright/test';

test.describe('{target_name} E2E Tests', () => {{
    test.beforeEach(async ({{ page }}) => {{
        await page.goto('/');
    }});
    
    test('should load main page', async ({{ page }}) => {{
        await expect(page).toHaveTitle(/{target_name}/);
    }});
    
    test('should create new {target_name.lower()}', async ({{ page }}) => {{
        // Click create button
        await page.click('[data-testid="create-button"]');
        
        // Fill form
        await page.fill('[name="name"]', 'Test {target_name}');
        await page.fill('[name="description"]', 'Test description');
        
        // Submit
        await page.click('[type="submit"]');
        
        // Verify created
        await expect(page.locator('[data-testid="success-message"]')).toBeVisible();
    }});
    
    test('should display {target_name.lower()} list', async ({{ page }}) => {{
        await page.goto('/{target_name.lower()}s');
        
        const items = page.locator('[data-testid="{target_name.lower()}-item"]');
        await expect(items).toHaveCount(await items.count());
    }});
    
    test('should navigate to detail page', async ({{ page }}) => {{
        await page.goto('/{target_name.lower()}s');
        
        // Click first item
        await page.click('[data-testid="{target_name.lower()}-item"]:first-child');
        
        // Verify navigation
        await expect(page).toHaveURL(/{target_name.lower()}s\\/\\d+/);
    }});
    
    test('should handle errors gracefully', async ({{ page }}) => {{
        await page.goto('/{target_name.lower()}s/invalid-id');
        
        await expect(page.locator('[data-testid="error-message"]')).toContainText('Not found');
    }});
}});
'''


class TestRunnerInput(BaseModel):
    """Input schema for test runner"""
    language: str = Field(..., description="Programming language")
    test_directory: str = Field(default="tests", description="Test directory")
    coverage: bool = Field(default=True, description="Generate coverage report")


class TestRunnerTool(BaseTool):
    name: str = "Test Runner Tool"
    description: str = """
    Runs test suites and generates coverage reports.
    Supports pytest, go test, jest, and more.
    Use this tool to execute tests.
    """
    args_schema: Type[BaseModel] = TestRunnerInput
    
    def _run(
        self,
        language: str,
        test_directory: str = "tests",
        coverage: bool = True
    ) -> str:
        """Generate test run command"""
        
        commands = {
            "python": f"pytest {test_directory} {'--cov=. --cov-report=html' if coverage else ''} -v",
            "go": f"go test {'--cover' if coverage else ''} -v ./...",
            "nodejs": f"npm test {'-- --coverage' if coverage else ''}",
            "csharp": f"dotnet test {'--collect:\"XPlat Code Coverage\"' if coverage else ''}"
        }
        
        cmd = commands.get(language.lower())
        if not cmd:
            return f"❌ Unsupported language: {language}"
        
        return f"""
# Test Runner Command
# Language: {language}
# Coverage: {'Enabled' if coverage else 'Disabled'}

{cmd}

# For CI/CD, use:
# {cmd} --ci
"""

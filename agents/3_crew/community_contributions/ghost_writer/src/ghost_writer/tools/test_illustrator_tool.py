import base64
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from ghost_writer.tools.illustrator_tool import IllustratorTool

def test_image_is_written(tmp_path):
    # Prepare fake image data
    fake_img_bytes = b"FAKE_IMAGE"
    fake_b64 = base64.b64encode(fake_img_bytes).decode()
    
    # Mock OpenAI response
    mock_response = MagicMock()
    mock_response.data = [MagicMock(b64_json=fake_b64)]
    
    with patch("ghost_writer.tools.illustrator_tool.openai.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.images.generate.return_value = mock_response
        
        # Create a subfolder path for the output image
        output_file = tmp_path / "foo" / "bar.png"
        tool = IllustratorTool()
        result = tool._run("draw a cat", filename=str(output_file))
        
        assert output_file.exists()
        with open(output_file, "rb") as f:
            assert f.read() == fake_img_bytes
        assert "Image generated and saved" in result

def test_api_failure(tmp_path):
    # Patch OpenAI to throw
    with patch("ghost_writer.tools.illustrator_tool.openai.OpenAI") as MockOpenAI:
        MockOpenAI.return_value.images.generate.side_effect = Exception("fail!")
        tool = IllustratorTool()
        result = tool._run("draw a cat", filename=str(tmp_path / "fail.png"))
        assert "Failed to generate image" in result

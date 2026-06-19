import pytest

from ghost_writer.utils.filesystem_utils import purge_directory

@pytest.fixture
def test_dir(tmp_path):
    # Create a temp dir and a file and nested directory
    d = tmp_path / "test_output_dir"
    d.mkdir()
    (d / "temp.txt").write_text("test")
    
    # Create a nested directory
    nested_dir = d / "nested"
    
    # put  a file in the nested directory
    nested_dir.mkdir()
    
    yield d
    # Cleanup is handled by tmp_path fixture

def test_purge_directory_removes_contents_and_recreates(test_dir):
    # Arrange
    assert (test_dir / "temp.txt").exists()

    # Act
    purge_directory(str(test_dir))

    # Assert
    assert test_dir.exists()
    assert test_dir.is_dir()
    assert not any(test_dir.iterdir())

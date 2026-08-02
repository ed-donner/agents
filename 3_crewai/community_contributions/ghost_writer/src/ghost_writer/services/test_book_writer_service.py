import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from ghost_writer.services.book_writer_service import BookWriterService
from ghost_writer.models import Act, Chapter, Scene, Book
from crewai import Agent

@pytest.fixture
def mock_transcriber():
    return MagicMock()

@pytest.fixture
def mock_illustrator():
    return MagicMock()

@pytest.fixture
def mock_pdf_tool():
    return MagicMock()

@pytest.fixture
def author_agent():
    return Agent(config={"name": "Test Author", "role": "Writes scenes", "goal": "goal", "backstory": "backstory"}, verbose=False)

@pytest.fixture
def book_writer(tmp_path, author_agent, mock_transcriber, mock_illustrator, mock_pdf_tool):
    return BookWriterService(
        author_agent=author_agent,
        transcriber=mock_transcriber,
        illustrator=mock_illustrator,
        disable_illustration=False,
        pdf_tool=mock_pdf_tool,
        output_path=tmp_path
    )

def test_write_act_calls_transcriber_and_increments_chapter(book_writer, mock_transcriber):
    scene = Scene(
        scene_title="Opening Scene",
        scene_description="Introductory scene",
        scene_plot="An unexpected guest arrives",
        characters="John Doe"
    )
    chapter = Chapter(
        chapter_title="Chapter One",
        chapter_plot="The beginning of conflict",
        chapter_description="A quiet evening",
        scenes=[scene]
    )
    act = Act(
        act_number=1,
        act_title="Act I",
        act_description="The beginning",
        act_plot="Setup",
        chapters=[chapter]
    )

    with patch("crewai.Task.execute_sync", return_value=MagicMock(raw="Mocked paragraph text")):
        book_writer.write_act(act)

    assert mock_transcriber.run.called

def test_write_book_cover_runs_illustrator_and_transcriber(author_agent, mock_transcriber):
    book = Book(title="Test Title", author="Test Author", description="Test Description")

    with patch("ghost_writer.services.book_writer_service.IllustratorTool") as MockTool:
        mock_instance = MockTool.return_value
        book_writer = BookWriterService(
            author_agent=author_agent,
            transcriber=mock_transcriber,
            illustrator=mock_instance,
            disable_illustration=False,
            output_path=Path("tmp")
        )
        book_writer.set_artistic_vision("Impressionistic and symbolic")

        book_writer.write_book_cover(book)

        mock_instance.run.assert_called_once()
        contents = [call.kwargs.get("content", "") for call in mock_transcriber.run.call_args_list]
        assert any("Test Title" in c for c in contents)
        assert any("![Book Cover]" in c for c in contents)


def test_save_pdf_calls_pdf_tool(book_writer, mock_pdf_tool):
    book_writer.book_md_path.write_text("# Test Book\n\nSome content here.")
    book_writer.save_pdf()

    mock_pdf_tool.run.assert_called_once_with(
        markdown_path=str(book_writer.book_md_path),
        output_pdf_path=str(book_writer.book_pdf_path)
    )

from ghost_writer.models import Scene, Act, Chapter, Book

def get_scene_task_prompt(scene: Scene, act: Act, chapter: Chapter) -> str:
    """
    Generates a task prompt for writing a scene based on the provided scene, act, and chapter details.
    
    Args:
        scene (Scene): The scene object containing details about the scene.
        act (Act): The act object containing details about the act.
        chapter (Chapter): The chapter object containing details about the chapter.
    
    Returns:
        str: The generated task prompt.
    """
    return f"""
        Write the scene for the novel with the following plot elements and characters:
        Plot: {scene.scene_plot}
        Characters: {scene.characters}

        Act description: {act.act_description}
        Act plot: {act.act_plot}
        Chapter description: {chapter.chapter_description}
        Chapter plot: {chapter.chapter_plot}
        Overall novel idea: {{idea}}

        Important:
        - Do not use any headings, just paragraphs.
        - Do not use em dashes.
    """
    
def get_chapter_illustration_prompt(chapter: Chapter, artistic_vision: str) -> str:
    """
    Generates a prompt for illustrating a chapter based on the provided chapter details.
    
    Args:
        chapter (Chapter): The chapter object containing details about the chapter.
        artistic_vision (str): The artistic vision for the illustration.
    
    Returns:
        str: The generated illustration prompt.
    """
    return f"""
        Create an illustration for the chapter titled '{chapter.chapter_title}' with description 
        '{chapter.chapter_description}'. 
        
        IMPORTANT: Do not include any words, just an illustration. 
        
        Here is some additional information from the art director: {artistic_vision}.
    """
    
def get_book_cover_illustration_prompt(book_info: Book, artistic_vision: str) -> str:
    """
    Generates a prompt for illustrating a book cover based on the provided book information.
    
    Args:
        book_info (Book): The book object containing details about the book.
        artistic_vision (str): The artistic vision for the illustration.
    
    Returns:
        str: The generated illustration prompt.
    """
    return f"""
        Create a book cover for the book titled '{book_info.title}', by author {book_info.author},
        with description '{book_info.description}'. Here is some additional information from the
        art director: {artistic_vision}.
    """
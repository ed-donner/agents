from ghost_writer.utils.markdown_utils import image_markdown

class IllustrationWriter:
    def __init__(self, illustrator, transcriber, images_path, output_path):
        self.illustrator = illustrator
        self.transcriber = transcriber
        self.images_path = images_path
        self.output_path = output_path
    
    def write_illustration(self, prompt: str, size: str, filename: str) -> str:
        cover_image = self.images_path / filename
        self.illustrator.run(
            prompt=prompt,
            filename=str(cover_image),
            size=size
        )
        image_md = image_markdown(image_path=str(cover_image.relative_to(self.output_path)), alt_text="Book Cover")
        self.transcriber.run(content=image_md)
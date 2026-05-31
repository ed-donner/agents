from config.settings import get_settings
from db.repository import get_repository
from ui.auth_callback import start_callback_server
from ui.gradio_app import create_app


def main() -> None:
    settings = get_settings()
    settings.validate_all()
    get_repository().initialize()
    start_callback_server()
    app = create_app()
    app.launch(inbrowser=True)


if __name__ == "__main__":
    main()

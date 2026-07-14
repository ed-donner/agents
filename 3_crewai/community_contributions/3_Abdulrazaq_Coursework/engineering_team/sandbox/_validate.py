import app


def main() -> None:
    assert app.demo is not None
    assert hasattr(app.demo, "render")
    print("Blocks constructed successfully")


if __name__ == "__main__":
    main()

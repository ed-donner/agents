class Book:
    def __init__(self, title, author):
        self.title = title
        self.author = author

    def __str__(self):
        return f"{self.title} by {self.author}"

    def has_author(self):
        return self.author is not None

    def summarize(self) -> str:
        return f"{self.title} is a book by {self.author}"

class BookShelf:
    def __init__(self, books):
        self.books = books

    def author_generator(self):
        for book in self.books:
            if book.has_author():
                yield book.author

    def unique_authors(self):
        yield from set(self.author_generator())

books = [Book("The Great Gatsby", "F. Scott Fitzgerald"), Book("1984", "George Orwell"), Book("To Kill a Mockingbird", "Harper Lee"),
 Book("The Great Gatsby", "F. Scott Fitzgerald"), Book("The Great Gatsby", "F. Scott Fitzgerald"), Book("Unknown Author", None)]
book_shelf = BookShelf(books)

# Method 3: Using next() with a single generator (will stop after 3 iterations)
print("\nMethod 3 - Using next() with single generator:")
authors_gen = book_shelf.unique_authors()
try:
    print(next(authors_gen))
except StopIteration:
    pass
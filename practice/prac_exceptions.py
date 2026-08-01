import traceback

def divide_numbers(file_name):
    try:
        with open(file_name, "r") as f:
            a  = f.readline()
            b = f.readline()
            try:
                return a / b
            except ZeroDivisionError:
                return "Error: Division by zero"
                traceback.print_exc()
            except TypeError:
                return "Error: Invalid input"
                traceback.print_exc()
            except Exception as e:
                return f"Error: {e}"
                traceback.print_exc()
    except FileNotFoundError:
        return "Error: File not found"
        traceback.print_exc()
    finally:
        traceback.print_exc()



if __name__ == "__main__":
    print(divide_numbers("file.txt"))
# Decorator to make a determination if the time deserves a Good Night, Good Morning, Good Afternoon, Good Evening or Good Night greeting.

import time
import functools

def time_of_day_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        current_time = time.localtime()
        if current_time.tm_hour < 12:
            print(f"Good Morning, {args[0]}!")
        elif current_time.tm_hour < 18:
            print(f"Good Afternoon, {args[0]}!")
        else:
            print(f"Good Evening, {args[0]}!")
        result = func(*args, **kwargs)
        print(f"I hope this is the correct time of day greeting for you, {args[0]}!")
        return result
    
    # Return the wrapper function
    return wrapper    

@time_of_day_decorator
def greet(name: str):
    print(f"How are you doing today, {name}!")

greet("Ryan")
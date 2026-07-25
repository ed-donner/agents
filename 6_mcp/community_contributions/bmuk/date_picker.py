from datetime import datetime
from pytz import timezone as tz

def get_date_with_timezone(timezone):
    return datetime.now(tz(timezone)).strftime("%Y-%m-%d %H:%M:%S")

def get_date():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    print(get_date_with_timezone("US/Eastern"))
    print(get_date_with_timezone("Europe/London"))
    print(get_date_with_timezone("Asia/Tokyo"))

if __name__ == "__main__":
    main()

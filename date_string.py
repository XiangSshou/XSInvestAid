from datetime import datetime, timedelta

def get_now_time():
    return datetime.now() - timedelta(hours=8)

def get_time_string():
    adjusted_time = get_now_time()
    target_date = adjusted_time.strftime("%Y%m%d")
    return target_date
from datetime import datetime, timezone, timedelta
import pytz


def convert_to_local_time(utc_time, timezone_str):
    tz = pytz.timezone(timezone_str)
    return utc_time.replace(tzinfo=timezone.utc).astimezone(tz)

def overlap_hours(time, start_time, end_time):
    # Convert time, start_time, and end_time to datetime objects
    time = datetime.combine(datetime.today(), time)
    start_time = datetime.combine(datetime.today(), start_time)
    end_time = datetime.combine(datetime.today(), end_time)

    # Calculate the overlap in minutes for the current hour
    if start_time <= time < end_time:
        next_hour = time + timedelta(hours=1)
        overlap_start = time
        overlap_end = min(next_hour, end_time)
        return (overlap_end - overlap_start).seconds // 60
    else:
        return 0
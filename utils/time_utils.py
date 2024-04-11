from datetime import datetime, timezone
import pytz

def convert_to_utc(local_time, timezone_str):
    tz = pytz.timezone(timezone_str)
    return tz.localize(local_time).astimezone(pytz.utc)

def convert_to_local_time(utc_time, timezone_str):
    tz = pytz.timezone(timezone_str)
    return utc_time.replace(tzinfo=timezone.utc).astimezone(tz)

# def overlap_hours(time, start_time, end_time):
#     if start_time <= time < end_time:
#         return (end_time - time).seconds // 60
#     elif start_time <= end_time <= time:
#         return (end_time - start_time).seconds // 60
#     else:
#         return 0

def is_within_business_hours(local_time, start_time, end_time):
    local_time_obj = local_time.time()
    return start_time <= local_time_obj < end_time

def overlap_hours(time, start_time, end_time):
    # Convert time, start_time, and end_time to datetime objects
    time = datetime.combine(datetime.today(), time)
    start_time = datetime.combine(datetime.today(), start_time)
    end_time = datetime.combine(datetime.today(), end_time)

    # Calculate the overlap in minutes
    if start_time <= time < end_time:
        return (end_time - time).seconds // 60
    else:
        return 0
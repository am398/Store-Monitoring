from utils.time_utils import overlap_hours
from models.store_status import StoreStatus
from datetime import datetime, timedelta


def get_overlap_minutes( local_time, business_hour):
    if business_hour[0] is None and business_hour[1] is None:
        # If business hours are not available, assume the store is open 24 hours
        return 60  # Minutes in an hour
    else:
        return overlap_hours(local_time.time(), business_hour[0], business_hour[1])

def get_active_ratio_for_hour( store_id, start_time, business_hour):
    store_statuses = StoreStatus.query.filter(
        StoreStatus.store_id == store_id,
        StoreStatus.timestamp_utc <= start_time + timedelta(hours=1),
        StoreStatus.timestamp_utc >= start_time
    ).all()

    if store_statuses:
        active_periods = sum(1 for status in store_statuses if status.status == 'active')
        return active_periods / len(store_statuses)
    else:
        return get_active_ratio_from_previous_data(store_id, start_time, business_hour)

def get_active_ratio_from_previous_data( store_id, start_time, business_hour):
    # Check the previous hour
    prev_hour_active_ratio = get_active_ratio_from_interval(store_id, start_time - timedelta(hours=1), start_time)

    if prev_hour_active_ratio is not None:
        return prev_hour_active_ratio

    # Check the same hour from the previous day
    prev_day_active_ratio = get_active_ratio_from_interval(store_id, start_time - timedelta(days=1), start_time - timedelta(days=1) + timedelta(hours=1))

    if prev_day_active_ratio is not None:
        return prev_day_active_ratio

    # Check the same day of the previous week
    prev_week_active_ratio = get_active_ratio_from_interval(store_id, start_time - timedelta(days=7), start_time - timedelta(days=7) + timedelta(hours=1))

    if prev_week_active_ratio is not None:
        return prev_week_active_ratio

    # If no data is available for the previous week, assume the store was open during that hour
    return 1

def get_active_ratio_from_interval( store_id, start_time, end_time):
    store_statuses = StoreStatus.query.filter(
        StoreStatus.store_id == store_id,
        StoreStatus.timestamp_utc >= start_time,
        StoreStatus.timestamp_utc < end_time
    ).all()

    if store_statuses:
        active_periods = sum(1 for status in store_statuses if status.status == 'active')
        return active_periods / len(store_statuses)
    else:
        return None

def adjust_start_time_for_next_day( start_time, day_of_week, business_hour, business_hours, store_id):
    if business_hour[0] is None and business_hour[1] is None:
        # Store is open 24 hours
        return start_time
    elif start_time.time() >= business_hour[1]:
        # Business hours for the next day
        day_of_week = (day_of_week + 1) % 7
        business_hour = business_hours.get((store_id, day_of_week), (None, None))
        return datetime.combine((start_time + timedelta(days=1)).date(), business_hour[0] or start_time.time())
    else:
        return start_time
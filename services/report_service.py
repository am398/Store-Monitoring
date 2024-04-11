from models import db 
from models.business_hour import BusinessHour
from models.store_status import StoreStatus
from models.store_timezone import StoreTimezone
from models.report import Report
from datetime import timedelta,datetime,timezone
from utils.time_utils import convert_to_local_time, overlap_hours
import csv
import os

class ReportService:
    def __init__(self, app):
        self.app = app
    def generate_report(self, report_id):
        try:
            with self.app.app_context():
                report = Report.query.get(report_id)
                # As per the Assignment using the current UTC time as the maximum timestamp
                # last_timestamp = datetime.now(timezone.utc)
                last_timestamp = db.session.query(db.func.max(StoreStatus.timestamp_utc)).scalar()

                # Generate the report data
                file_path = self._generate_report_data(report_id, last_timestamp)

                # Update the report status and file path
                report.status = 'Complete'
                report.file_path = file_path
                db.session.commit()
        except Exception as e:
            # Log the error
            self.app.logger.error(f"Error generating report {report_id}: {e}")

    def _generate_report_data(self,report_id, last_timestamp):

        # Query the necessary data from the database
        business_hours = {(bh.store_id, bh.day_of_week): (bh.start_time_local, bh.end_time_local)
                          for bh in BusinessHour.query.all()}
        store_timezones = {tz.store_id: tz.timezone_str for tz in StoreTimezone.query.all()}

        # Iterate over unique store IDs
        store_ids = set(store_status.store_id for store_status in StoreStatus.query.all())

        try:
            file_path = os.path.join('reports', f'report_{report_id}.csv')
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', newline='') as csvfile:
                fieldnames = ['store_id', 'uptime_last_hour', 'uptime_last_day', 'uptime_last_week', 'downtime_last_hour', 'downtime_last_day', 'downtime_last_week']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                i=0
                for store_id in store_ids:
                    # Calculate uptime and downtime for the given intervals
                    uptime_last_hour, downtime_last_hour = self._calculate_uptime_downtime(store_id, last_timestamp, timedelta(hours=1), business_hours, store_timezones)
                    uptime_last_day, downtime_last_day = self._calculate_uptime_downtime(store_id, last_timestamp, timedelta(days=1), business_hours, store_timezones)
                    uptime_last_week, downtime_last_week = self._calculate_uptime_downtime(store_id, last_timestamp, timedelta(days=7), business_hours, store_timezones)
                    i+=1
                    print(({
                            'store_id': store_id,
                            'uptime_last_hour': uptime_last_hour * 60,
                            'uptime_last_day': uptime_last_day ,
                            'uptime_last_week': uptime_last_week,
                            'downtime_last_hour': downtime_last_hour * 60,
                            'downtime_last_day': downtime_last_day,
                            'downtime_last_week': downtime_last_week
                        }))
                    writer.writerow({
                            'store_id': store_id,
                            'uptime_last_hour': uptime_last_hour * 60,
                            'uptime_last_day': uptime_last_day ,
                            'uptime_last_week': uptime_last_week,
                            'downtime_last_hour': downtime_last_hour * 60,
                            'downtime_last_day': downtime_last_day,
                            'downtime_last_week': downtime_last_week
                        })
                    if(i==50):
                        break
            return file_path
        except Exception as e:
            print(f"Exception in _write_report_to_csv: {e}")
            return None
        
    def _calculate_uptime_downtime(self, store_id, last_timestamp, interval, business_hours, store_timezones):
        uptime = 0
        downtime = 0

        start_time = last_timestamp - interval
        end_time = last_timestamp

        # If stote timezone is not available then using default timezone as 'America/Chicago' as per Assignmentt
        store_timezone = store_timezones.get(store_id, 'America/Chicago')
        while start_time < end_time:
            local_time = convert_to_local_time(start_time, store_timezone)
            day_of_week = local_time.weekday()
            business_hour = business_hours.get((store_id, day_of_week), (None, None))
            overlap_minutes = self._get_overlap_minutes(local_time,business_hour)

            if overlap_minutes:
                try:
                    active_ratio = self._get_active_ratio_for_hour(store_id, start_time, business_hour)
                    uptime += active_ratio * overlap_minutes
                    downtime += (1 - active_ratio) * overlap_minutes
                except Exception as e:
                    self.app.logger.error(f"Error calculating uptime/downtime for store {store_id} at {start_time}: {e}")

            start_time += timedelta(hours=1)
            start_time = self._adjust_start_time_for_next_day(start_time, day_of_week, business_hour, business_hours, store_id)

        return uptime // 60, downtime // 60

    def _get_overlap_minutes(self, local_time,business_hour):
        if business_hour[0] is None and business_hour[1] is None:
            # If business hours are not available, assume the store is open 24 hours
            return 60  # Minutes in an hour
        else:
            return overlap_hours(local_time.time(), business_hour[0], business_hour[1])

    def _get_active_ratio_for_hour(self, store_id, start_time, business_hour):
        store_statuses = StoreStatus.query.filter(
            StoreStatus.store_id == store_id,
            StoreStatus.timestamp_utc <= start_time + timedelta(hours=1),
            StoreStatus.timestamp_utc >= start_time
        ).all()

        if store_statuses:
            active_periods = sum(1 for status in store_statuses if status.status == 'active')
            return active_periods / len(store_statuses)
        else:
            return self._get_active_ratio_from_previous_data(store_id, start_time, business_hour)

    def _get_active_ratio_from_previous_data(self, store_id, start_time, business_hour):
        # Check the previous hour
        prev_hour_active_ratio = self._get_active_ratio_from_interval(store_id, start_time - timedelta(hours=1), start_time)

        if prev_hour_active_ratio is not None:
            return prev_hour_active_ratio

        # Check the same hour from the previous day
        prev_day_active_ratio = self._get_active_ratio_from_interval(store_id, start_time - timedelta(days=1), start_time - timedelta(days=1) + timedelta(hours=1))

        if prev_day_active_ratio is not None:
            return prev_day_active_ratio

        # Check the same day of the previous week
        prev_week_active_ratio = self._get_active_ratio_from_interval(store_id, start_time - timedelta(days=7), start_time - timedelta(days=7) + timedelta(hours=1))

        if prev_week_active_ratio is not None:
            return prev_week_active_ratio

        # If no data is available for the previous week, assume the store was not open during that hour
        return 0

    def _get_active_ratio_from_interval(self, store_id, start_time, end_time):
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

    def _adjust_start_time_for_next_day(self, start_time, day_of_week, business_hour, business_hours, store_id):
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

            

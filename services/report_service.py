from models import db 
from models.business_hour import BusinessHour
from models.store_status import StoreStatus
from models.store_timezone import StoreTimezone
from models.report import Report
from datetime import datetime, timedelta
from utils.time_utils import convert_to_local_time, overlap_hours
import csv
import os
from flask import current_app

class ReportService:
    def __init__(self, app):
        self.app = app
    def generate_report(self, report_id):
        with self.app.app_context():
            report = Report.query.get(report_id)
            last_timestamp = db.session.query(db.func.max(StoreStatus.timestamp_utc)).scalar()

            # Generate the report data
            report_data = self._generate_report_data(last_timestamp)

            # Write the report data to a CSV file
            file_path = self._write_report_to_csv(report_data, report_id)

            # Update the report status and file path
            report.status = 'Complete'
            report.file_path = file_path
            db.session.commit()

    def _generate_report_data(self, last_timestamp):
        report_data = []

        # Query the necessary data from the database
        business_hours = {(bh.store_id, bh.day_of_week): (bh.start_time_local, bh.end_time_local)
                          for bh in BusinessHour.query.all()}
        store_timezones = {tz.store_id: tz.timezone_str for tz in StoreTimezone.query.all()}

        # Iterate over unique store IDs
        store_ids = set(store_status.store_id for store_status in StoreStatus.query.all())
        for store_id in store_ids:
            # Calculate uptime and downtime for the given intervals
            uptime_last_hour, downtime_last_hour = self._calculate_uptime_downtime(store_id, last_timestamp, timedelta(hours=1), business_hours, store_timezones)
            uptime_last_day, downtime_last_day = self._calculate_uptime_downtime(store_id, last_timestamp, timedelta(days=1), business_hours, store_timezones)
            uptime_last_week, downtime_last_week = self._calculate_uptime_downtime(store_id, last_timestamp, timedelta(days=7), business_hours, store_timezones)

            report_data.append({
                'store_id': store_id,
                'uptime_last_hour': uptime_last_hour,
                'uptime_last_day': uptime_last_day,
                'uptime_last_week': uptime_last_week,
                'downtime_last_hour': downtime_last_hour,
                'downtime_last_day': downtime_last_day,
                'downtime_last_week': downtime_last_week
            })

            if(len(report_data)==10):
                print("Anuj",report_data)
                break

        return report_data

    def _calculate_uptime_downtime(self, store_id, last_timestamp, interval, business_hours, store_timezones):
        uptime = 0
        downtime = 0

        start_time = last_timestamp - interval
        end_time = last_timestamp

        store_timezone = store_timezones.get(store_id, 'America/Chicago')

        # Iterate over the time interval in hours
        current_time = start_time
        while current_time < end_time:
            local_time = convert_to_local_time(current_time, store_timezone)
            day_of_week = local_time.weekday()
            business_hour = business_hours.get((store_id, day_of_week), (None, None))

            if business_hour[0] and business_hour[1]:
                overlap_minutes = overlap_hours(local_time.time(), business_hour[0], business_hour[1])
                if overlap_minutes:
                    store_statuses = StoreStatus.query.filter(
                        StoreStatus.store_id == store_id,
                        StoreStatus.timestamp_utc >= current_time - timedelta(hours=1),  # Consider the previous hour as well
                        StoreStatus.timestamp_utc <= current_time
                    ).all()
                    
                    # Interpolate uptime and downtime based on the available observations
                    active_periods = sum(1 for status in store_statuses if status.status == 'active')
                    if store_statuses:
                        uptime += (active_periods / len(store_statuses)) * overlap_minutes                    
                        downtime += ((len(store_statuses) - active_periods) / len(store_statuses)) * overlap_minutes

            current_time += timedelta(hours=1)

        return uptime // 60, downtime // 60

    def _write_report_to_csv(self, report_data, report_id):
        try:
            file_path = os.path.join('reports', f'report_{report_id}.csv')

            # file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', newline='') as csvfile:
                fieldnames = ['store_id', 'uptime_last_hour', 'uptime_last_day', 'uptime_last_week', 'downtime_last_hour', 'downtime_last_day', 'downtime_last_week']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for row in report_data:
                    writer.writerow(row)

            return file_path
        except Exception as e:
            print(f"Exception in _write_report_to_csv: {e}")





        









# def _calculate_uptime_downtime(self, store_id, last_timestamp, interval, business_hours, store_timezones):
#     uptime = 0
#     downtime = 0

#     start_time = last_timestamp - interval
#     end_time = last_timestamp

#     store_timezone = store_timezones.get(store_id, 'America/Chicago')

#     # Iterate over the time interval in hours
#     current_time = start_time
#     while current_time < end_time:
#         local_time = convert_to_local_time(current_time, store_timezone)
#         day_of_week = local_time.weekday()
#         business_hour = business_hours.get((store_id, day_of_week), (None, None))

#         if business_hour[0] and business_hour[1]:
#             overlap_minutes = overlap_hours(local_time.time(), business_hour[0], business_hour[1])
#             if overlap_minutes:
#                 store_statuses = StoreStatus.query.filter(
#                     StoreStatus.store_id == store_id,
#                     StoreStatus.timestamp_utc >= current_time - timedelta(hours=1),  # Consider the previous hour as well
#                     StoreStatus.timestamp_utc <= current_time
#                 ).all()
                
#                 # Interpolate uptime and downtime based on the available observations
#                 active_periods = sum(1 for status in store_statuses if status.status == 'active')
#                 uptime += (active_periods / len(store_statuses)) * overlap_minutes
#                 downtime += ((len(store_statuses) - active_periods) / len(store_statuses)) * overlap_minutes

#         current_time += timedelta(hours=1)

#     return uptime // 60, downtime // 60



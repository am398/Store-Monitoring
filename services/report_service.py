
from models import db 
from models.business_hour import BusinessHour
from models.store_status import StoreStatus
from models.store_timezone import StoreTimezone
from models.report import Report
from datetime import timedelta,datetime,timezone
from utils.time_utils import convert_to_local_time
import csv
import os
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Thread
from services.helper_functions import get_overlap_minutes, get_active_ratio_for_hour, adjust_start_time_for_next_day

class ReportService:
    def __init__(self, app):
        self.app = app
        with self.app.app_context():
            self.business_hours = {(bh.store_id, bh.day_of_week): (bh.start_time_local, bh.end_time_local)
                                for bh in BusinessHour.query.all()}
            self.store_timezones = {tz.store_id: tz.timezone_str for tz in StoreTimezone.query.all()}
            self.store_ids = set()
    def generate_report(self, report_id):
        try:
            with self.app.app_context():
                report = Report.query.get(report_id)
                last_timestamp = db.session.query(db.func.max(StoreStatus.timestamp_utc)).scalar()

                # Prepare the file path and open the CSV file
                file_path = os.path.join('reports', f'report_{report_id}.csv')
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                csv_file = open(file_path, 'w', newline='')
                fieldnames = ['store_id', 'uptime_last_hour', 'uptime_last_day', 'uptime_last_week',
                              'downtime_last_hour', 'downtime_last_day', 'downtime_last_week']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()

                # Use a queue to pass data from report generation to the writer thread
                data_queue = Queue()

                # Start a separate thread to handle writing data to the CSV file
                writer_thread = Thread(target=self.write_data_to_csv, args=(writer, data_queue))
                writer_thread.start()

                # Generate the report data and pass it to the queue
                self.generate_report_data(report_id, last_timestamp, data_queue)

                # After all data has been put in the queue, signal the writer thread to stop
                data_queue.put(None)
                writer_thread.join()

                # Close the CSV file
                csv_file.close()

                # Update the report status and file path
                report.status = 'Complete'
                report.file_path = file_path
                db.session.commit()
        except Exception as e:
            self.app.logger.error(f"Error generating report {report_id}: {e}")

    def write_data_to_csv(self, writer, data_queue):
        while True:
            # Get data from the queue
            data = data_queue.get()

            print(data)
            # If data is None, break the loop (stop the thread)
            if data is None:
                break
            
            # Write data to the CSV file
            writer.writerow(data)

    def generate_report_data(self, report_id, last_timestamp, data_queue):

        # Get the list of unique store IDs

        self.store_ids = set(store_status.store_id for store_status in StoreStatus.query.limit(50).all())
        store_ids = self.store_ids

        # Use a ThreadPoolExecutor to execute the worker function concurrently for each store ID
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Define the worker function
            def worker(store_id):
                # Calculate uptime and downtime for different intervals
                uptime_last_hour, downtime_last_hour = self._calculate_uptime_downtime(store_id, last_timestamp, timedelta(hours=1))
                uptime_last_day, downtime_last_day = self._calculate_uptime_downtime(store_id, last_timestamp, timedelta(days=1))
                uptime_last_week, downtime_last_week = self._calculate_uptime_downtime(store_id, last_timestamp, timedelta(days=7))

                # Prepare the row data for the CSV file
                row_data = {
                    'store_id': store_id,
                    'uptime_last_hour': uptime_last_hour * 60,
                    'uptime_last_day': uptime_last_day,
                    'uptime_last_week': uptime_last_week,
                    'downtime_last_hour': downtime_last_hour * 60,
                    'downtime_last_day': downtime_last_day,
                    'downtime_last_week': downtime_last_week
                }

                # Pass the row data to the queue for the writer thread to write to the CSV file
                data_queue.put(row_data)


            # Submit tasks to the executor for each store ID
            for store_id in store_ids:
                executor.submit(worker, store_id)

    def _calculate_uptime_downtime(self, store_id, last_timestamp, interval):
        with self.app.app_context():
            uptime = 0
            downtime = 0

            start_time = last_timestamp - interval
            end_time = last_timestamp

            business_hours = self.business_hours

            # If store timezone is not available, use default timezone 'America/Chicago'
            store_timezone = self.store_timezones.get(store_id, 'America/Chicago')
            while start_time < end_time:
                local_time = convert_to_local_time(start_time, store_timezone)
                day_of_week = local_time.weekday()
                business_hour = business_hours.get((store_id, day_of_week), (None, None))

                overlap_minutes = get_overlap_minutes(local_time, business_hour)


                if overlap_minutes:
                    try:
                        active_ratio =get_active_ratio_for_hour(local_time,store_id, start_time, business_hour,business_hours)
                        uptime += active_ratio * overlap_minutes
                        downtime += (1 - active_ratio) * overlap_minutes
                    except Exception as e:
                        self.app.logger.error(f"Error calculating uptime/downtime for store {store_id} at {start_time}: {e}")

                start_time += timedelta(hours=1)
                start_time =adjust_start_time_for_next_day(start_time, day_of_week, business_hour, business_hours, store_id)

        return uptime // 60, downtime // 60
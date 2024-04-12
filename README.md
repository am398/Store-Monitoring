# **Store Monitoring**

Welcome to the Store Monitoring project ! This repository contains tools and methods for monitoring the stores and check if the store is online or not and generate reports on uptime and downtime statistics.

The project uses the **Flask** framework for building the application, **SQLite** as the database, and **SQLAlchemy** as the ORM tool. I used my `seed_db.py` file to fill the values in my database.

## [Assignment Details](https://loopxyz.notion.site/Take-home-interview-Store-Monitoring-12664a3c7fdf472883a41457f0c9347d)

---

## **Algorithm :**
---

## **Table of Contents**

- [Generating the Report](#generating-the-report)
- [Report Data Generation using Multithreading](#report-data-generation-using-multithreading)
- [Concurrent Report Data Writing](#concurrent-report-data-writing)
- [Uptime and Downtime Calculation](#uptime-and-downtime-calculation)
- [Active Ratio Calculation](#active-ratio-calculation)

---

### **Generating the Report**

The `generate_report` method is responsible for creating a report for a specific `report_id`. The method:

- Prepares the file path and opens a CSV file to write report data.
- Uses a CSV writer object to handle writing data to the CSV file.

---

### **Report Data Generation using Multithreading**

The process includes:

- Retrieving a list of unique store IDs from the database.
- Utilizing a `ThreadPoolExecutor` to concurrently process data for each store ID.
- A worker function (`worker`) that calculates uptime and downtime statistics for a given store ID over different time intervals (hour, day, and week).

---

### **Concurrent Report Data Writing**

The method involves:

- Using a queue (`data_queue`) to pass data from the report generation process to a separate thread responsible for writing data to the CSV file.
- Starting a separate thread (`writer_thread`) to handle writing data to the CSV file.
- Continuously retrieving data from the queue and writing it to the CSV file.

---

### **Uptime and Downtime Calculation**

The `calculate_uptime_downtime` method is designed to calculate uptime and downtime for a given store, timestamp, and time interval by based on the active ratio:

1. **Previous Hour:**
    - The function first tries to get the active ratio from the previous hour by calling the `get_active_ratio_from_interval` function with the store ID, the start time minus one hour, and the start time.
    - If a value is returned, it is used as the active ratio.

2. **Entire Day Up to Start Time:**
    - If the previous step fails, the function tries to get the active ratio for the entire day up to the start time by calling `get_active_ratio_from_interval` with the store ID, the start of the business hour for that day, and the start time.
    - If a value is returned, it is used as the active ratio.

3. **Same Hour on Previous Day:**
    - If step 2 fails, the function tries to get the active ratio for the same hour on the previous day by calling `get_active_ratio_from_interval` with the store ID, the start time minus one day, and the start time minus one day plus one hour.
    - If a value is returned, it is used as the active ratio.

4. **Entire Previous Day:**
    - If step 3 fails, the function tries to get the active ratio for the entire previous day by determining the day of the week for the start time and using the `business_hours` dictionary to get the business hours for that day of the week and store ID.
    - It then calls `get_active_ratio_from_interval` with the store ID, the start of the business hour for the previous day, and the start time.
    - If a value is returned, it is used as the active ratio.

5. **Same Day of Previous Week:**
    - If step 4 fails, the function tries to get the active ratio for the same day of the previous week by calling `get_active_ratio_from_interval` with the store ID, the start of the business hour for that day of the week, and the end of the business hour for that day of the week.
    - If a value is returned, it is used as the active ratio.

6. **Default Case:**
    - If all previous steps fail, the function assumes the store was not open during that hour and returns an active ratio of 0.
---

### **Active Ratio Calculation**

The active ratio calculation involves two main steps:

1. **Calculate Active Periods:**
    - The function checks if `store_statuses` contains any records.
    - If it does, it uses a generator expression to count the number of records where the `status` attribute is equal to 'active'.
    - This count is stored in the variable `active_periods`.

2. **Calculate Active Ratio:**
    - If there were `store_statuses` retrieved, the function calculates the active ratio for the hour by dividing `active_periods` by the total number of `store_statuses` (i.e., the length of the list).
    - **This value represents the proportion of time within the hour that the store was active.**

---

Thank you for exploring the Store Monitoring project!.

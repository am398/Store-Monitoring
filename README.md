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

The `calculate_uptime_downtime` method is designed to calculate uptime and downtime for a given store, timestamp, and time interval by:

- Iterating over the time interval in hours and checking if the store is open during that hour based on the business hours.
- Retrieving store statuses for the current hour, and based on the ratio of 'active' statuses to total statuses, calculating the uptime and downtime for the overlapping period between business hours and the current hour.
- Accumulating uptime and downtime values and returning them in minutes.
- If no data is available for the current hour, checking the previous hour, the same hour on the previous day, and the same day of the previous week.
- Calculating the active ratio for that hour based on the available data and using it to interpolate the uptime and downtime for the current hour.
- **Assuming the store is open for that hour if no data is available from all of the above checks.**

---

### **Active Ratio Calculation**

The active ratio calculation involves two main steps:

1. **Calculate Active Periods:**
    - The function checks if `store_statuses` contains any records.
    - If it does, it uses a generator expression to count the number of records where the `status` attribute is equal to 'active'.
    - This count is stored in the variable `active_periods`.

2. **Calculate Active Ratio:**
    - If there were `store_statuses` retrieved, the function calculates the active ratio for the hour by dividing `active_periods` by the total number of `store_statuses` (i.e., the length of the list).
    - This value represents the proportion of time within the hour that the store was active.

---

Thank you for exploring the Store Monitoring project!.

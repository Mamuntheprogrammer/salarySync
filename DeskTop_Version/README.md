# AttenSync - HRMS & Terminal System

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run Application**:
    ```bash
    python main.py
    ```

## First Run
- On the first run, a wizard will appear.
- Configure time format and database location.
- By default, an admin user is created:
    - **Username**: `admin`
    - **Password**: `admin123`

## Features

- **Employee Terminal**: Left side of the main screen. Employees clock in/out using their 6-digit code.
- **Admin Portal**: Right side of the main screen. Login to manage the system.
- **Management**:
    - **Companies**: Define company structures.
    - **Employees**: Add employees and assign shifts.
    - **Shifts**: Define shift timings and late allowances.
- **Attendance**: Manual view and edit of attendance records.
- **Reports**: Generate CSV reports for attendance.
- **Payroll**: Calculate monthly salaries including overtime and late deductions.

# Payroll Calculation Logic

This document outlines the logic used by **AttenSync** to calculate employee salaries.

## Core Formula

The **Net Salary** is calculated as follows:

$$
\text{Net Salary} = \text{Gross Salary} - \text{Deductions} + \text{Additions}
$$

- **Additions** = Overtime Pay + Holiday Overtime Pay

---

## Payroll Configuration Rules

Below are the adjustable settings in the **Payroll Config Manager** and how they impact the calculation:

| Setting | Type | Description | Effect on Formula |
| :--- | :--- | :--- | :--- |
| **Overtime Rate** | Multiplier | Rate for regular overtime hours. | $\text{OT Pay} = \text{OT Hours} \times \text{Hourly Rate} \times \textbf{Multiplier}$ |
| **Holiday OT Rate** | Multiplier | Rate for overtime on holidays/weekends. | $\text{Hol. OT Pay} = \text{Hol. OT Hours} \times \text{Hourly Rate} \times \textbf{Multiplier}$ |
| **Late Deduction** | Multiplier | Deduction rate for late hours. | $\text{Late Ded.} = \text{Late Hours} \times \text{Hourly Rate} \times \textbf{Multiplier}$ |
| **Short Leave Ded.** | Multiplier | Deduction rate for short leave hours. | $\text{Short Lv Ded.} = \text{Short Lv Hours} \times \text{Hourly Rate} \times \textbf{Multiplier}$ |
| **Days in Month** | Divisor | Fixed number of days to divide Base Salary. | $\text{Daily Rate} = \text{Base Salary} / \textbf{Divisor}$ |
| **Use Actual Days** | Logic | If enabled, uses the actual days in the calendar month (e.g., 28, 30, 31). | Overrides "Days in Month" with actual count (e.g. 30 in April, 31 in May). |
| **Late Days Rule** | Threshold | Number of late days triggering a 1-day penalty. | $\text{Penalty Days} = \lfloor \text{Total Late Days} / \textbf{Threshold} \rfloor$ |

---

## Detailed Component Calculation

### 1. Calendar Variables

Before calculating pay, the system determines the nature of each day in the month:

*   **Total Days**: Number of days in the month (e.g., 28, 30, 31).
*   **Holidays**: Days marked in the `HolidayCalendar` (National, Festival, etc.).
    *   *Priority*: Employee Specific > Business Area Specific > Global.
*   **Weekends**: Recurring weekly holidays (e.g., Fridays).
    *   *Priority*: Employee Specific > Business Area Specific.
*   **Working Days**:
    $$
    \text{Working Days} = \text{Total Days} - \text{Holidays} - \text{Weekends}
    $$

### 2. Attendance Stats

*   **Present Days**: Count of days the employee clocked in (regardless of whether it was a holiday or not).
*   **Present on Working Days**: Count of days the employee was present on a standard "Working Day".

### 3. Deductions

#### A. Absent Deduction
Employees are penalized for not attending on Working Days.
$$
\text{Absent Days} = \max(0, \text{Working Days} - \text{Present on Working Days})
$$
$$
\text{Absent Deduction} = \text{Absent Days} \times \text{Daily Rate}
$$

*   **Daily Rate**: $\frac{\text{Base Salary}}{\text{Days in Month Config (Default 30)}}$

#### B. Late Deduction
$$
\text{Late Deduction} = \text{Total Late Hours} \times \text{Hourly Rate} \times \text{Late Multiplier}
$$

*   **Hourly Rate**: $\frac{\text{Daily Rate}}{8}$ (Assuming 8-hour shift)
*   **Late Multiplier**: Configurable in Payroll Settings (Default 1.0)

#### C. Short Leave Deduction
$$
\text{Short Leave Deduction} = \text{Total Short Leave Hours} \times \text{Hourly Rate} \times \text{Short Leave Multiplier}
$$

#### D. Late Days Penalty (New)
In addition to hourly deductions, a separate penalty applies if the employee exceeds a threshold of late days.
$$
\text{Penalty Days} = \lfloor \frac{\text{Total Late Days}}{\text{Threshold}} \rfloor
$$
$$
\text{Late Days Penalty Deduction} = \text{Penalty Days} \times \text{Daily Rate}
$$

*   **Threshold**: Configurable (e.g., Every 3 Late Days = 1 Day Salary Deduction).

### 4. Additions (Overtime)

#### A. Regular Overtime
Overtime performed on regular working days.
$$
\text{OT Pay} = \text{OT Hours} \times \text{Hourly Rate} \times \text{OT Multiplier}
$$
*   **OT Multiplier**: Default 1.5x

#### B. Holiday Overtime
Overtime performed on Holidays or Weekends.
$$
\text{Holiday OT Pay} = \text{Holiday OT Hours} \times \text{Hourly Rate} \times \text{Holiday OT Multiplier}
$$
*   **Holiday OT Multiplier**: Default 2.0x

---

## Example Calculation

**Scenario**:
*   **Base Salary**: 30,000
*   **Month**: January (30 Days Calculation Base)
*   **Working Days**: 25
*   **Employee Attendance**: Present for 20 Working Days.
*   **Late**: 5 Days (Total 2 Hours late).
*   **Late Days Rule**: Every 3 Late Days = 1 Day Penalty.

**Steps**:
1.  **Daily Rate**: $30,000 / 30 = 1,000$
2.  **Hourly Rate**: $1,000 / 8 = 125$
3.  **Absent Days**: $25 - 20 = 5$ Days.
4.  **Absent Deduction**: $5 \times 1,000 = 5,000$
5.  **Late Hourly Deduction**: $2 \text{ hours} \times 125 \times 1.0 = 250$
6.  **Late Days Penalty**:
    *   Late Days = 5
    *   Threshold = 3
    *   Penalty Days = $\lfloor 5 / 3 \rfloor = 1$ Day.
    *   Deduction = $1 \times 1,000 = 1,000$

**Net Salary**:
$$
30,000 - 5,000 (\text{Absent}) - 250 (\text{Late Hours}) - 1,000 (\text{Late Penalty}) = \mathbf{23,750}
$$

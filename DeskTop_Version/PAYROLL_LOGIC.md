# Payroll Calculation Logic

This document outlines the logic used by **AttenSync** to calculate employee salaries.

## Core Formula

The **Net Salary** is calculated as follows:

$$
\text{Net Salary} = \text{Gross Salary} - \text{Deductions} + \text{Additions}
$$

Where:
- **Gross Salary** = Employee's Base Salary
- **Deductions** = Late Penalty + Short Leave Deduction + Absent Deduction
- **Additions** = Overtime Pay + Holiday Overtime Pay

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
*   **Late**: 2 Hours total.

**Steps**:
1.  **Daily Rate**: $30,000 / 30 = 1,000$
2.  **Hourly Rate**: $1,000 / 8 = 125$
3.  **Absent Days**: $25 - 20 = 5$ Days.
4.  **Absent Deduction**: $5 \times 1,000 = 5,000$
5.  **Late Deduction**: $2 \times 125 \times 1.0 = 250$

**Net Salary**:
$$
30,000 - 5,000 (\text{Absent}) - 250 (\text{Late}) = \mathbf{24,750}
$$

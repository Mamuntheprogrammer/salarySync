# Payroll Configuration Manager Tutorial

This tutorial explains the purpose of each field in the Payroll Configuration Manager and provides examples of how they affect salary calculations.

## 1. Select Scope
This setting determines whether the rules you are defining apply globally to the entire organization, or to a specific company/business area.
* **Example**: If set to "Global Defaults," the rules apply to everyone. If you have a specific branch where overtime is paid differently, you could change the scope to that specific branch.

## 2. Overtime Rate (x Hourly)
The multiplier applied to the base hourly rate for hours worked beyond the standard shift length.
* **Example**: If an employee's base salary calculates to $20/hour, an Overtime Rate of `1.50` means they earn $30 for every hour of overtime worked ($20 * 1.50).

## 3. Holiday OT Rate (x Hourly)
The multiplier applied to the base hourly rate when an employee works on a designated holiday (or weekend/off-day, depending on company policy).
* **Example**: For that same $20/hour employee, a Holiday OT Rate of `2.00` means they earn double time, or $40/hour, for any hours worked on a public holiday.

## 4. Late Deduction (x Hourly)
The penalty multiplier applied against the hourly rate for time an employee is late (beyond any allowed grace period).
* **Example**: If set to `1.00`, the late time is deducted at their normal hourly rate. If they are exactly 1 hour late, they lose 1 hour's worth of pay. If set to `1.50`, being 1 hour late would cost them 1.5 hours' worth of pay as an extra penalty.

## 5. Short Leave Deduction (x Hourly)
The penalty multiplier applied for taking unapproved short leaves or leaving the shift early. 
* **Example**: Similar to Late Deduction, a value of `1.00` means standard hourly deduction. If an employee leaves 2 hours early during their shift, an amount equal to 2 hours of normal pay is deducted from their salary.

## 6. Late Days Penalty Rule
A rule that converts accumulated instances of being late into full-day absences (for salary deduction purposes), regardless of the exact minutes tardy.
* **Example**: As shown in the image, "3 Days Late = 1 Day Salary Deduction". If an employee clocks in late on Monday, Tuesday, and Thursday, they are penalized by losing one full day's base salary for that month, on top of any minute-by-minute late deductions you may or may not apply.

## 7. Calculation Mode
Determines the core philosophy of how the base salary is earned.
* **Checked (Calculate Salary based on Present Days)**: The employee's monthly rate is broken down into a daily rate. They only get paid for the days marked as "Present" or "Paid Leave".
* **Unchecked**: Often implies a fixed monthly salary where deductions are subtracted for absences, rather than building up from zero based on days present.

## 8. Divisor Mode & Days in Month Divisor
These two fields control how the monthly base salary is converted into a Daily Rate (to calculate deductions and pay).
* **Divisor Mode (Use Actual Days in Month)**: If checked, the system divides the salary by exactly how many days are in the current month (e.g., 28 in Feb, 31 in March).
* **Days in Month Divisor (e.g., 30)**: If the checkbox above is *unchecked*, the system uses this fixed number to calculate the daily rate every month.
* **Example**: An employee makes $3,000/month.
  * If "Use Actual Days" is checked, in February (28 days) their daily rate is `$3000 / 28 = $107.14/day`. In March (31 days), it's `$3000 / 31 = $96.77/day`.
  * If a fixed divisor of `30` is used, their daily rate is always `$3000 / 30 = $100.00/day`, regardless of the month.

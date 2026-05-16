# Pass-Printer Data Schema

The `schedule-scraper` maintains a SQLite database at `/opt/pass-printer/data.db`. This database is refreshed daily at 3:00 AM.

## Tables

### 1. `students`
Contains basic student profile information.
- `id` (INTEGER, PK): Smartpass internal User ID.
- `name` (TEXT): Display name (e.g., "John Doe").
- `email` (TEXT): Primary school email.
- `grade` (TEXT): Current grade level (9-12).
- `custom_id` (TEXT): The school's native Student ID (PowerSchool ID). Use this to avoid name collisions.

### 2. `schedules`
Contains the periods and classes for each student for the **current day**.
- `student_id` (INTEGER, FK): References `students.id`.
- `period` (TEXT): Name of the period (e.g., "Period 1 (Mon/Fri days)").
- `start_time` (TEXT): Start time in 24h format (e.g., "07:45").
- `end_time` (TEXT): End time in 24h format (e.g., "08:31").
- `class_name` (TEXT): The name of the course.
- `room` (TEXT): Room number or identifier (e.g., "C209").
- `teacher_name` (TEXT): Name of the primary teacher.
- `teacher_email` (TEXT): Email of the primary teacher.

## Semester Handling
The scraper automatically filters courses based on the current date:
- **Semester 1 (July 1 - Dec 31)**: Includes courses ending in " A" and ignores " B".
- **Semester 2 (Jan 1 - June 30)**: Includes courses ending in " B" and ignores " A".
- Courses without " A" or " B" suffixes are always included.

## SQL Query Examples for Pass-Printer

The following queries use a specific time (e.g., `'09:30'`) to find the student's active class.

### 1. Get current class, room, and teacher
Find where a student is supposed to be right now.
```sql
SELECT class_name, room, teacher_name, end_time
FROM schedules
WHERE student_id = ? AND start_time <= '09:30' AND end_time >= '09:30'
ORDER BY start_time DESC
LIMIT 1;
```

### 2. Get destination (Fuzzy/Passing Period handling)
If a student arrives during passing time (e.g., `'08:33'`), the strict `start_time <= T AND end_time >= T` might return nothing. Use this to find the *next* or *current* destination.
```sql
SELECT class_name, room, teacher_name, end_time
FROM schedules
WHERE student_id = ? AND end_time >= '08:33'
ORDER BY start_time ASC
LIMIT 1;
```
*Logic: "Find the first class that hasn't ended yet." This works for both mid-class arrivals and passing periods.*

### 3. Get current teacher's email
Used for automated notifications or printer routing.
```sql
SELECT teacher_email
FROM schedules
WHERE student_id = ? AND start_time <= '09:30' AND end_time >= '09:30'
ORDER BY start_time DESC
LIMIT 1;
```

### 3. Get student metadata by Student ID
Map the PowerSchool `custom_id` back to the Smartpass internal ID.
```sql
SELECT id, name, email
FROM students
WHERE custom_id = '722427';
```

## Maintenance
- The `schedules` table is wiped and repopulated every night to reflect the rotating block schedule for the new day.
- The `students` table is updated (upsert) to keep the roster current.

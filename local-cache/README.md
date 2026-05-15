# Local Attendance Cache

Having a local cache of attendance data helps make printed passes more data-full. 

Data in the local cache can be:
- updated nightly (suggesting 3:30AM)
- stored encrypted, to secure data
- minimize traffic to the primary SIS
- minimize exposure of student records on pass-printer device
- normalized and stored in a SQLite or Redis database
- formatted as needed for the pass-printer:
    - Student-facing `student_id` numbers
    - Daily schedule (bells, times, classes, teachers, teacher_email)
    - Student schedules
    - Basic tardy records: count of tardies to each class

It would also be good to update this cache on a regular schedule, but be able to 'force' an update when the schedule changes to a 2-hour delay or some other late-breaking nonstandard schedule. 
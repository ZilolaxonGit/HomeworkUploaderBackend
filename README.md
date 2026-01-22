# Learning Center Management System

A full-stack web application for managing lessons, homework submissions, and daily student ratings.

## Features

### Three User Roles

1. **Admin Dashboard**
   - Create and manage students, teachers, and lessons
   - Calculate daily leaderboards
   - View system statistics
   - Full CRUD operations for all entities

2. **Teacher Dashboard**
   - View submitted homework
   - Rate student homework (1-10 scale)
   - Track all ratings given

3. **Student Dashboard**
   - Submit homework (URL or file upload)
   - View all lessons
   - View personal ratings and feedback
   - **Daily Leaderboard** with top 3 students highlighted in different colors

## Technology Stack

### Backend
- Django 6.0
- Django REST Framework
- JWT Authentication (djangorestframework-simplejwt)
- SQLite (development) / PostgreSQL (production)
- Python 3.14

### Frontend
- React 18
- Vite
- React Router v6
- Axios
- CSS3

## Project Structure

```
backend/
├── config/                 # Django project settings
├── users/                  # User management app
├── lessons/                # Lessons app
├── homework/               # Homework submissions app
├── ratings/                # Ratings and leaderboard app
├── frontend/               # React frontend
│   ├── src/
│   │   ├── api/           # API client and services
│   │   ├── components/    # Reusable components
│   │   ├── contexts/      # React contexts (Auth)
│   │   ├── pages/         # Page components
│   │   │   ├── Admin/
│   │   │   ├── Teacher/
│   │   │   └── Student/
│   │   └── styles/        # CSS files
├── media/                  # Uploaded files
└── manage.py
```

## Installation & Setup

### Backend Setup

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install django djangorestframework djangorestframework-simplejwt psycopg2-binary pillow python-decouple django-cors-headers
   ```

3. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

4. **Create superuser (Admin):**
   ```bash
   python manage.py createsuperuser
   # Username: admin
   # Password: admin123 (or your choice)
   ```

5. **Start Django development server:**
   ```bash
   python manage.py runserver
   ```

   Backend will be available at: http://localhost:8000

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

   Frontend will be available at: http://localhost:5173

## Usage

### Admin Workflow

1. Login with admin credentials at http://localhost:5173/login
2. Create teachers and students from the Admin Dashboard
3. Create lessons and assign them to teachers
4. Calculate daily leaderboard using the "Calculate Today's Leaderboard" button

### Teacher Workflow

1. Login with teacher credentials (created by admin)
2. View submitted homework from students
3. Rate homework submissions (1-10 scale) with optional comments
4. Each rating is automatically recorded for daily leaderboard calculation

### Student Workflow

1. Login with Student ID and password (created by admin)
2. View available lessons
3. Submit homework via URL or file upload
4. View personal ratings and teacher feedback
5. Check daily leaderboard (top 3 highlighted):
   - 1st place: Gold background
   - 2nd place: Silver background
   - 3rd place: Bronze background

## API Endpoints

### Authentication
- `POST /api/auth/login/` - Login (all roles)
- `GET /api/auth/me/` - Get current user
- `POST /api/token/refresh/` - Refresh JWT token

### Students (Admin only for create/update/delete)
- `GET /api/auth/students/` - List all students
- `POST /api/auth/students/` - Create student
- `GET /api/auth/students/{id}/` - Get student details
- `PUT /api/auth/students/{id}/` - Update student
- `DELETE /api/auth/students/{id}/` - Delete student

### Teachers (Admin only for create/update/delete)
- `GET /api/auth/teachers/` - List all teachers
- `POST /api/auth/teachers/` - Create teacher
- `GET /api/auth/teachers/{id}/` - Get teacher details
- `PUT /api/auth/teachers/{id}/` - Update teacher
- `DELETE /api/auth/teachers/{id}/` - Delete teacher

### Lessons (Admin only for create/update/delete)
- `GET /api/lessons/` - List all lessons
- `POST /api/lessons/` - Create lesson
- `GET /api/lessons/{id}/` - Get lesson details
- `PUT /api/lessons/{id}/` - Update lesson
- `DELETE /api/lessons/{id}/` - Delete lesson

### Homework (Students create, Teachers can view)
- `GET /api/homework/` - List homework (filtered by role)
- `POST /api/homework/` - Submit homework (students only)
- `GET /api/homework/{id}/` - Get homework details
- `PATCH /api/homework/{id}/` - Update homework submission

### Ratings (Teachers create)
- `GET /api/ratings/` - List ratings (filtered by role)
- `POST /api/ratings/` - Create rating (teachers only)
- `GET /api/ratings/{id}/` - Get rating details

### Leaderboard
- `GET /api/leaderboard/` - Get leaderboard (with optional date parameter)
- `GET /api/leaderboard/today/` - Get today's leaderboard
- `GET /api/leaderboard/top_three/` - Get top 3 students
- `POST /api/leaderboard/calculate/` - Calculate daily leaderboard (admin only)

## Default Credentials

### Admin
- Username: `admin`
- Password: `admin123`

### Creating Additional Users

Use the Admin Dashboard to create:
- **Students**: Provide student_id, username, and password
- **Teachers**: Provide employee_id, username, and password

Students login using their username (or Student ID) and password.

## Database Models

### User
- Custom user model with role-based access (ADMIN, TEACHER, STUDENT)
- JWT authentication

### Student
- Extended profile linked to User
- Fields: student_id, phone, date_of_birth, address

### Teacher
- Extended profile linked to User
- Fields: employee_id, phone, specialization, bio

### Lesson
- Fields: title, description, teacher, start_date, end_date, is_active

### Homework
- Fields: student, lesson, submission_url, submission_file, description, status
- Status: PENDING, SUBMITTED, RATED

### Rating
- Fields: homework, teacher, student, score (1-10), comment, rating_date
- Automatic student assignment from homework

### DailyLeaderboard
- Fields: student, date, average_score, rank, total_ratings
- Calculated from daily ratings

## Features Implemented

✅ Role-based authentication and authorization
✅ Admin dashboard for managing users and lessons
✅ Teacher dashboard for rating homework
✅ Student dashboard with homework submission
✅ File upload support for homework
✅ Daily leaderboard calculation
✅ Top 3 students highlighted with different colors
✅ JWT token-based authentication
✅ Automatic token refresh
✅ Responsive UI design
✅ Protected routes based on user roles

## Development Notes

- The system uses SQLite for development (can be switched to PostgreSQL by setting `USE_SQLITE=False` in `.env`)
- Media files are stored locally in the `media/` directory
- CORS is configured to allow requests from `http://localhost:5173`
- JWT tokens expire after 12 hours (access) and 7 days (refresh)

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Switch to PostgreSQL by setting `USE_SQLITE=False`
3. Set a strong `SECRET_KEY`
4. Configure proper `ALLOWED_HOSTS`
5. Use a production web server (e.g., Gunicorn, uWSGI)
6. Set up static file serving (e.g., Nginx)
7. Configure HTTPS
8. Set up proper file storage (e.g., AWS S3, Azure Blob Storage)

## License

This project is built as an MVP for educational purposes.

## Support

For issues or questions, please contact the development team.

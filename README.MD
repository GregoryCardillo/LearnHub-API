# 🎓 LearnHub-API

A comprehensive and production-ready RESTful API for an e-learning platform built with Django and Django REST Framework.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0+-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14+-red.svg)](https://www.django-rest-framework.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-58%20Passed-success.svg)](tests/)
[![Coverage](https://img.shields.io/badge/Coverage-92%25-brightgreen.svg)](htmlcov/)

> **A full-stack e-learning solution with JWT authentication, role-based permissions, course management, progress tracking, and comprehensive testing.**

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Project Structure](#-project-structure)
- [API Endpoints](#-api-endpoints)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### 🔐 Authentication & Authorization
- JWT-based authentication with access and refresh tokens
- Role-based access control (Students & Instructors)
- Custom permissions for granular access control
- Secure password hashing and validation

### 📚 Course Management
- Full CRUD operations for courses, modules, and lessons
- Hierarchical course structure (Course → Module → Lesson)
- Multiple content types (video, article, quiz, assignment)
- Course status management (draft, published, archived)
- Advanced filtering, search, and ordering

### 👨‍🎓 Student Features
- Course enrollment with automatic progress tracking
- Real-time progress calculation and statistics
- Lesson completion tracking
- Student dashboard with comprehensive analytics
- Certificate generation upon course completion
- Estimated completion date calculation

### 👨‍🏫 Instructor Features
- Create and manage courses
- Module and lesson management
- View enrolled students and their progress
- Course analytics and statistics

### 🎯 Quiz System
- Multiple question types (single choice, multiple choice, true/false)
- Automatic grading and score calculation
- Attempt tracking and retry limits
- Time limits and passing scores
- Detailed answer feedback

### 🚀 Advanced Features
- Automatic progress record creation via Django signals
- Query optimization with select_related and prefetch_related
- Database indexing for performance
- Rate limiting and throttling
- Pagination for large datasets
- Comprehensive API documentation (Swagger/ReDoc)

## 🛠 Tech Stack

### Core
- **Python 3.11+** - Programming language
- **Django 5.0+** - Web framework
- **Django REST Framework 3.14+** - RESTful API toolkit
- **PostgreSQL / SQLite** - Database (SQLite for dev, PostgreSQL for prod)

### Authentication & Security
- **djangorestframework-simplejwt** - JWT authentication
- **python-decouple** - Environment variable management

### API & Documentation
- **drf-spectacular** - OpenAPI 3.0 schema generation
- **django-filter** - Advanced filtering
- **django-cors-headers** - CORS handling

### Testing & Quality
- **pytest** - Testing framework
- **pytest-django** - Django integration for pytest
- **pytest-cov** - Code coverage
- **factory-boy** - Test data generation
- **faker** - Fake data generation

### Development
- **Pillow** - Image processing
- **python-decouple** - Configuration management

## 🏗 Architecture

### Database Schema
```
User (Custom AbstractBaseUser)
  ├── Student (role='student')
  └── Instructor (role='instructor')

Course
  ├── instructor: FK(User)
  └── Module
      └── Lesson
          └── Quiz
              └── Question
                  └── AnswerChoice

Enrollment
  ├── student: FK(User)
  ├── course: FK(Course)
  └── Progress
      └── lesson: FK(Lesson)
```

### Key Design Patterns
- **Repository Pattern** - Clean separation of data access
- **Factory Pattern** - Object creation in tests
- **Signal Pattern** - Automatic progress record creation
- **Decorator Pattern** - Custom permissions and authentication

## 🚀 Getting Started

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Virtual environment tool (venv/virtualenv)
- Git

### Installation

1. **Clone the repository**
```bash
   git clone https://github.com/yourusername/LearnHub-API.git
   cd LearnHub-API
```

2. **Create and activate virtual environment**
```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
```

3. **Install dependencies**
```bash
   pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
   cp .env.example .env
   # Edit .env with your configuration
```

5. **Run migrations**
```bash
   python manage.py migrate
```

6. **Create a superuser**
```bash
   python manage.py createsuperuser
```

7. **Run the development server**
```bash
   python manage.py runserver
```

8. **Access the application**
   - API: http://127.0.0.1:8000/api/
   - Admin Panel: http://127.0.0.1:8000/admin/
   - API Docs (Swagger): http://127.0.0.1:8000/api/docs/
   - API Docs (ReDoc): http://127.0.0.1:8000/api/redoc/

## 📖 API Documentation

### Interactive Documentation

The API provides comprehensive interactive documentation:

- **Swagger UI**: http://127.0.0.1:8000/api/docs/
  - Interactive API explorer
  - Try out endpoints directly
  - View request/response schemas

- **ReDoc**: http://127.0.0.1:8000/api/redoc/
  - Beautiful, responsive documentation
  - Easy navigation
  - Detailed descriptions

- **OpenAPI Schema**: http://127.0.0.1:8000/api/schema/
  - Download OpenAPI 3.0 schema
  - Import into Postman/Insomnia

### Authentication

Most endpoints require authentication. To authenticate:

1. Register: `POST /api/auth/register/`
2. Login: `POST /api/auth/login/`
3. Use the access token in headers:
```
   Authorization: Bearer <your_access_token>
```

## 🧪 Testing

The project has comprehensive test coverage (92%+) with 58 tests across models, serializers, views, and permissions.

### Run all tests
```bash
pytest
```

### Run with coverage report
```bash
pytest --cov=courses --cov-report=html
```

### Run specific test file
```bash
pytest courses/tests/test_api.py
```

### Run specific test class
```bash
pytest courses/tests/test_api.py::TestCourseAPI
```

### View coverage report
```bash
# Generate HTML report
pytest --cov=courses --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## 📁 Project Structure
```
elearning_platform/
├── config/                  # Project configuration
│   ├── settings.py         # Django settings
│   ├── urls.py            # Main URL configuration
│   └── wsgi.py            # WSGI configuration
├── courses/                # Main application
│   ├── migrations/        # Database migrations
│   ├── tests/            # Test suite
│   │   ├── conftest.py   # Pytest fixtures
│   │   ├── factories.py  # Test data factories
│   │   ├── test_models.py
│   │   ├── test_serializers.py
│   │   ├── test_api.py
│   │   └── test_permissions.py
│   ├── admin.py          # Django admin configuration
│   ├── models.py         # Database models
│   ├── serializers.py    # DRF serializers
│   ├── views.py          # API views
│   ├── permissions.py    # Custom permissions
│   ├── filters.py        # Custom filters
│   └── urls.py           # App URL routing
├── media/                 # User-uploaded files
├── static/               # Static files
├── .env.example          # Environment variables template
├── .gitignore           # Git ignore rules
├── manage.py            # Django management script
├── pytest.ini           # Pytest configuration
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🔌 API Endpoints

### Authentication
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register/` | Register new user | ❌ |
| POST | `/api/auth/login/` | Login and get tokens | ❌ |
| POST | `/api/auth/logout/` | Logout (blacklist token) | ✅ |
| POST | `/api/auth/refresh/` | Refresh access token | ❌ |
| GET | `/api/auth/verify/` | Verify token validity | ✅ |
| PUT | `/api/auth/change-password/` | Change password | ✅ |

### Users
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/users/me/` | Get current user profile | ✅ |
| PUT | `/api/users/me/` | Update user profile | ✅ |

### Courses
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/courses/` | List all published courses | ❌ |
| POST | `/api/courses/` | Create course (instructors only) | ✅ |
| GET | `/api/courses/{slug}/` | Get course details | ❌ |
| PUT | `/api/courses/{slug}/` | Update course (owner only) | ✅ |
| DELETE | `/api/courses/{slug}/` | Delete course (owner only) | ✅ |
| GET | `/api/courses/{slug}/modules/` | List course modules | ❌ |
| POST | `/api/courses/{slug}/enroll/` | Enroll in course | ✅ |

### Instructor
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/instructor/courses/` | List instructor's courses | ✅ |
| GET | `/api/courses/{slug}/students/` | View enrolled students | ✅ |
| POST | `/api/courses/{slug}/modules/create/` | Create module | ✅ |
| POST | `/api/modules/{id}/lessons/create/` | Create lesson | ✅ |

### Student
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/student/dashboard/` | Get dashboard stats | ✅ |
| GET | `/api/enrollments/` | List my enrollments | ✅ |
| GET | `/api/enrollments/{id}/` | Get enrollment details | ✅ |
| POST | `/api/enrollments/{id}/unenroll/` | Unenroll from course | ✅ |
| GET | `/api/enrollments/{id}/certificate/` | Get certificate | ✅ |

### Progress
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/enrollments/{id}/progress/` | Get enrollment progress | ✅ |
| POST | `/api/enrollments/{id}/lessons/{lesson_id}/complete/` | Mark lesson complete | ✅ |
| POST | `/api/enrollments/{id}/lessons/{lesson_id}/reset/` | Reset lesson progress | ✅ |

### Filtering & Search Examples

**Filter courses by level:**
```
GET /api/courses/?level=beginner
```

**Search courses:**
```
GET /api/courses/?search=python
```

**Filter by price range:**
```
GET /api/courses/?min_price=0&max_price=50
```

**Combine filters:**
```
GET /api/courses/?level=beginner&is_free=true&search=django&ordering=-created_at
```

### Coding Standards
- Follow PEP 8 style guide
- Write tests for new features
- Update documentation as needed

# Restaurant Management System

A comprehensive restaurant management application built with React frontend and Flask backend, featuring AI-powered menu planning, inventory management, demand forecasting, and nutritional analysis.

Dataset link: https://www.kaggle.com/datasets/jordanchan20/restaurant-menu-price

The Model_Evaluation.zip file contains the code for model training, fine-tuning, feature importance analysis, and error evaluation.

## Features

### 🍽️ Menu Management
- Interactive menu display with AI-generated food images
- Menu item creation and editing
- Nutritional information tracking
- Dietary restriction filtering
- Dynamic pricing adjustments

### 📊 Inventory & Stock Management
- Real-time inventory tracking
- Automated stock alerts
- Ingredient usage analytics
- Low stock notifications
- Supplier management

### 🤖 AI-Powered Features
- **Menu Planning**: AI-assisted menu creation and optimization
- **Demand Forecasting**: Predictive analytics for ingredient demand
- **Nutritional Analysis**: Automated nutrition calculation
- **Chatbot**: Interactive AI assistant for restaurant operations
- **Image Generation**: AI-generated food images for menu items

### 📈 Analytics & Reporting
- Sales analytics and trends
- Ingredient usage patterns
- Performance metrics
- Financial reporting
- Customer order analysis

### 🎯 Dashboard
- Real-time operational overview
- Key performance indicators
- Quick access to critical functions
- Alert management

## Technology Stack

### Frontend
- **React** - User interface framework
- **Material-UI (MUI)** - Component library
- **Axios** - HTTP client
- **React Router** - Navigation

### Backend
- **Flask** - Web framework
- **SQLAlchemy** - Database ORM
- **Flask-Migrate** - Database migrations
- **APScheduler** - Task scheduling
- **Flask-CORS** - Cross-origin resource sharing

### AI & Machine Learning
- **Google Gemini API** - AI chat and analysis
- **Custom ML Models** - Demand forecasting
- **USDA Nutrition API** - Nutritional data

### Database
- **SQLite** - Development database
- Support for PostgreSQL/MySQL in production

## Project Structure

```
first-app/
├── backend/                 # Flask backend application
│   ├── models/             # Database models
│   ├── routes/             # API route handlers
│   ├── services/           # Business logic services
│   ├── utils/              # Utility functions
│   ├── static/             # Static files (images)
│   ├── instance/           # Database files
│   ├── app.py              # Main Flask application
│   ├── config.py           # Configuration settings
│   └── requirements.txt    # Python dependencies
├── src/                    # React frontend application
│   ├── Client_Side/        # Customer-facing components
│   ├── Server_Side/        # Admin/staff components
│   ├── components/         # Reusable UI components
│   ├── app.js              # Express server
│   └── index.js            # React entry point
├── public/                 # Public assets
├── package.json            # Node.js dependencies
└── README.md               # This file
```

## Installation & Setup

### Prerequisites
- **Node.js** (v14 or higher)
- **Python** (v3.8 or higher)
- **npm** or **yarn**
- **Git**

### 1. Clone the Repository
```bash
git clone <repository-url>
cd first-app
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 3. Frontend Setup
```bash
# Navigate to project root
cd ..

# Install Node.js dependencies
npm install
```

### 4. Environment Configuration

Create a `.env` file in the `backend/` directory:

```env
# Database Configuration
DATABASE_URL=sqlite:///instance/restaurant.db

# Server Configuration
PORT=5001
FLASK_DEBUG=False

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. Database Setup
```bash
# Navigate to backend
cd backend

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Running the Application

### Development Mode

1. **Start the Backend Server**:
```bash
cd backend
python app.py
```
The Flask server will run on `http://localhost:5001`

2. **Start the Frontend Server**:
```bash
# In project root
npm start
```
The React app will run on `http://localhost:3000` (or next available port)

### Production Mode

1. **Build the Frontend**:
```bash
npm run build
```

2. **Deploy Backend**:
- Configure production database
- Set environment variables
- Use a production WSGI server (e.g., Gunicorn)

## API Endpoints

### Core APIs
- `GET /api/menu` - Retrieve menu items
- `POST /api/menu` - Create new menu item
- `GET /api/inventory` - Get inventory status
- `POST /api/orders` - Create new order
- `GET /api/dashboard/stats` - Dashboard statistics

### AI Features
- `POST /api/ai-agent/menu-planning` - AI menu suggestions
- `POST /api/ai-agent/gemini-chat` - Chat with AI assistant
- `GET /api/forecasted-demand` - Demand predictions
- `POST /api/ai-agent/analyze-nutrition` - Nutrition analysis

### Configuration
- `GET /api/config/api-key` - Get API configuration
- `GET /api/scheduler/status` - Scheduler status

## Key Features Usage

### Menu Planning
1. Navigate to Menu Planning page
2. Use AI suggestions for menu optimization
3. Add/edit menu items with nutritional info
4. Generate AI images for new items

### Inventory Management
1. Access Inventory page
2. Track stock levels in real-time
3. Set up automated alerts
4. Monitor usage patterns

### Analytics Dashboard
1. View key metrics on Dashboard
2. Analyze sales trends
3. Monitor ingredient usage
4. Track performance indicators

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API endpoints

## Changelog

### Latest Updates
- ✅ Consolidated API key configuration
- ✅ Fixed image loading issues
- ✅ Improved frontend-backend integration
- ✅ Enhanced error handling
- ✅ Updated security practices

---

**Built with ❤️ for restaurant management efficiency**

# HK Shipping - Transport Invoice & Payment Tracker

A Flask-based logistics management system for tracking shipments, invoices, and payments with role-based access control.

## Features

- 📦 Shipment tracking with GPS checkpoints and ETAs
- 💰 Invoice management with payment tracking
- 🚚 Fleet management (trucks and drivers)
- 👥 Customer relationship management (CRM)
- 👤 Role-based access control (RBAC)
- 🤖 AI-powered logistics feedback engine
- 📊 Dashboard with real-time tracking
- 🛡️ Audit logging for compliance

## Tech Stack

- **Backend:** Flask (Python)
- **Database:** SQLite
- **Frontend:** HTML5, CSS3, JavaScript
- **Deployment:** Gunicorn + Nginx/Cloud platforms

## Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/hk-shipping-tracker.git
   cd hk-shipping-tracker
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

5. **Open in browser:**
   ```
   http://localhost:5000
   ```

## Deployment

### Quick Deploy to Render (Free)

1. Fork this repository
2. Go to [render.com](https://render.com)
3. Click "New +" → "Web Service"
4. Connect your GitHub repo
5. Set Build Command: `pip install -r requirements.txt`
6. Set Start Command: `gunicorn app:app`
7. Deploy!

### Deploy to Railway

1. Go to [railway.app](https://railway.app)
2. Create new project from GitHub
3. Railway auto-detects and deploys

### Deploy to Heroku

```bash
heroku login
heroku create your-app-name
git push heroku main
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed instructions.

## Project Structure

```
├── app.py                 # Main Flask application
├── test_app.py           # Unit tests
├── requirements.txt      # Python dependencies
├── Procfile             # Deployment configuration
├── .gitignore           # Git ignore rules
├── .env.example         # Environment variables template
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── images/
└── templates/
    ├── index.html       # Dashboard
    ├── crm.html         # Booking wizard
    ├── accounts.html    # Invoice management
    ├── fleet.html       # Vehicle & driver mgmt
    ├── trip.html        # Trip tracking
    ├── detail.html      # Detailed tracking
    └── dashboard.html   # Analytics
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```bash
FLASK_ENV=production
FLASK_DEBUG=False
DATABASE_FILE=hk_shipping.db
PORT=5000
```

## Testing

```bash
python -m pytest test_app.py
```

## License

Private Project - HK Shipping Private Limited

## Support

For issues or questions, contact: support@hkshipping.com

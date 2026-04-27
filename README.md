# NutriTrack 🥗

NutriTrack is an advanced, AI-powered Progressive Web App (PWA) designed to track your daily food and health metrics. Built with a Flask backend and an optimized Vanilla JS frontend, it boasts cutting-edge features for Hackathons, including Voice Logging, Barcode Scanning, and Heuristic AI Analysis.

## 🌟 Hackathon "WOW" Features

1. **Voice Logging (NLP)**: Leverage the native Web Speech API to log meals conversationally ("I had 2 rotis for lunch"). A custom regex parser extracts entities and auto-logs them.
2. **Barcode Scanner**: Turn your device's camera into a scanner using QuaggaJS. It queries the OpenFoodFacts API to instantly pull nutritional data.
3. **AI Meal Suggestions**: A heuristic algorithm calculates your remaining daily macronutrient deficit and optimally suggests foods from the local database.
4. **Deep Analytics & Health Score**: Analyzes the last 7 days of logs to compute a 0-100 Health Score, identify favorite foods, and generate actionable textual trends.
5. **Medical PDF Export**: Generate professionally styled PDF reports summarizing 7-day health metrics using `html2pdf`.
6. **Progressive Web App (PWA)**: Installable on any mobile device with offline caching via Service Workers.

## 💻 Tech Stack

- **Backend**: Python 3.13, Flask, SQLite (optimized with indexing)
- **Frontend**: HTML5, Vanilla CSS3 (Glassmorphism UI), Vanilla JavaScript
- **Libraries**: Chart.js (Data Visualization), QuaggaJS (Barcode Scanning), Canvas Confetti (Gamification)
- **Security & Quality**: Flask-CORS, Google Cloud Logging, input type validation, full Python docstrings, and a dedicated `unittest` suite.

## 🚀 Deployment to Google Cloud Run

NutriTrack is containerized and ready to be deployed to Google Cloud Run for infinite scalability. 

### Prerequisites
1. A Google Cloud Platform (GCP) Project
2. `gcloud` CLI installed and authenticated

### Deployment Steps
1. Make the deployment script executable:
   ```bash
   chmod +x deploy.sh
   ```
2. Run the deployment script and provide your GCP Project ID:
   ```bash
   ./deploy.sh
   ```
   *Note: Ensure the Cloud Run and Cloud Build APIs are enabled in your GCP project.*
3. Visit the URL provided in the terminal once the deployment completes!

## 🛠️ Local Development

1. **Install Dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```
2. **Run Tests**
   ```bash
   python3 tests.py
   ```
3. **Run Application**
   ```bash
   python3 app.py
   ```
4. Access the app at `http://127.0.0.1:8080`.

## ♿ Accessibility (A11y)
NutriTrack is built with inclusivity in mind. The interface uses ARIA labels, semantic HTML tags, and supports complete keyboard navigation via `tabindex` to ensure a smooth experience for screen readers.

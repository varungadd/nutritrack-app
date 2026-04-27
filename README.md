# NutriTrack 🥗

NutriTrack eliminates manual data entry using AI and hardware integrations. It’s a blazing-fast Progressive Web App (PWA) making logging food as easy as talking or snapping a photo.

## 🌟 Killer Features

* 🎙️ **Voice Logging (NLP):** Say "I had 2 rotis for lunch". Our Web Speech API integration extracts entities, calculates macros, and auto-logs it instantly. 
* 📸 **Barcode Scanner:** Point your camera at any wrapper. QuaggaJS scans the barcode, queries OpenFoodFacts, and drops nutrition data into your diary.
* 🧠 **AI Coach:** Missing your protein goal? Our local AI calculates your macro deficit and recommends perfect foods to hit 100%. 
* 📊 **Deep Analytics:** Analyzes 7-day habits for a Health Score, live Radar Charts, and trend insights.
* 👨‍⚕️ **Doctor Exports:** Generate PDF Medical Reports instantly.

## 🛠️ Stack & Deploy

* **Tech:** Python, Flask, SQLite, Vanilla JS/CSS, Chart.js
* **A11y:** Fully ARIA compliant
* **Deploy:** `./deploy.sh` for Google Cloud Run

## ☁️ Google Services Integration

* **Google Cloud Run:** Hosts the containerized application.
* **Google Cloud Build:** Builds the Docker container.
* **Google Artifact Registry:** Stores the built container images.
* **Google Cloud Logging:** Logs all API requests and errors in real-time.

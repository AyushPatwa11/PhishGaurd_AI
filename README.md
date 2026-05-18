<div align="center">
  <img src="https://media.giphy.com/media/V81XE0wF8a1kP9T2kF/giphy.gif" alt="Hacker typing" width="200" />
  <br>
  <h1>🎣 PhishGuard AI <br> <span style="font-size: 18px; color: #7c6df0;">Because trusting every email is a terrible idea.</span></h1>
  
  <p>
    <strong>A shockingly smart, Glassmorphism-dripped AI that catches scammers before they catch your bank details.</strong>
  </p>

  <p>
    <a href="https://python.org"><img src="https://img.shields.io/badge/Powered%20by-Python%20%26%20Flask-black?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
    <a href="https://scikit-learn.org"><img src="https://img.shields.io/badge/Brain-Scikit--Learn-orange?style=for-the-badge&logo=scikit-learn&logoColor=white" alt="Sklearn"></a>
    <img src="https://img.shields.io/badge/Vibe-Immaculate-7c6df0?style=for-the-badge" alt="Vibe">
  </p>
</div>

<br>

## 🛑 Stop Right There, Scammer!
Ever looked at an email from your "CEO" asking for $50,000 in iTunes gift cards and thought, *"Hmm, seems legit"*? 

**PhishGuard AI** is here to save you from yourself. We don't just say "this looks bad"—we use **Explainable AI (XAI)** to tell you exactly *why* it's bad. Oh, and we trace the scammer's IP and drop a pinpoint on a gorgeous 3D Live Threat Map. Take that, cybercriminals! 🥷💥

---

## ✨ Features That Make You Go "Whoa"

<details>
<summary><b>👀 The "Glassmorphism" UI</b> <i>(Click to expand!)</i></summary>
<br>
We didn't just build a security tool; we built a futuristic command center. Expect smooth micro-animations, pulsing threat indicators, and dynamic progress bars that make you feel like you're hacking the mainframe in a sci-fi movie.
</details>

<details>
<summary><b>🧠 Big Brain AI (Explainable ML)</b> <i>(Click to expand!)</i></summary>
<br>
Instead of a black-box "trust me bro" score, our Random Forest classifier breaks down the threat using 19 distinct features. It catches structural anomalies (like raw IP addresses) and psychological manipulation tactics (Urgency, Fear, Authority).
</details>

<details>
<summary><b>🌍 Live Threat Map Auto-Flight 🛫</b> <i>(Click to expand!)</i></summary>
<br>
Drop a sketchy URL into the dashboard. Watch as our backend resolves the IP, and the frontend instantly swoops across a beautiful Leaflet.js globe to drop a giant red pin exactly where the server is located. <i>*pew pew*</i> 🎯
</details>

---

## 🛠️ The Tech Sauce

We kept it ridiculously lightweight. No crazy build steps. No Webpack configuration tears. Just pure, unadulterated Python and Vanilla JS magic.

```mermaid
graph TD;
    A[Sleek Glassmorphism UI 💎] -->|REST API| B(Flask App Engine 🚂)
    B --> C{The Feature Extractor 🕵️‍♂️}
    C -->|Sniffing URLs| D[Regex Magic ✨]
    C -->|Reading Minds| E[NLP Keyword Analysis 🧠]
    D --> F[Random Forest ML 🌲]
    E --> F
    F --> G[Explainable Breakdown 📊]
    G --> A
```

---

## 🚀 How to Launch This Bad Boy

You're 3 commands away from feeling like an elite cybersecurity analyst. 

### 1. Grab the Code
```bash
git clone https://github.com/AyushPatwa11/PhishGaurd_AI.git
cd PhishGaurd_AI/backend
```

### 2. Fuel the Engine
```bash
pip install -r requirements.txt
```

### 3. Ignite! 🚀
```bash
python app.py
```
👉 Open **`http://localhost:5000`** in your browser and start interrogating suspicious links!

---

## 🤖 Talk to the API (For the Nerds)

Don't want to use the UI? Fine. Be that way. Our REST API is ready for your scripts.

| Method | Endpoint | What it does |
|--------|----------|--------------|
| `POST` | `/api/predict` | Feed it `{text, url}` and get a terrifyingly accurate breakdown of the scam. |
| `GET` | `/api/examples` | Bored? Get a list of mock CEO fraud and delivery scams to play with. |
| `GET` | `/api/live-threats`| Gives you live coordinates of Botnet C2 servers. Great for party tricks. |

---

<div align="center">
  <img src="https://media.giphy.com/media/l41Yl2CVK4HEnG424/giphy.gif" alt="Mic Drop" width="150" />
  <br><br>
  <i>Crafted with excessive caffeine and ❤️ by <a href="https://github.com/AyushPatwa11">AyushPatwa11</a>.</i>
</div>

# 🧑🏾‍⚖️ Quantathon Judging App

![Demo](https://github.com/ChantelleAA/ChantelleAA/blob/main/judging_demo.gif)

A streamlined Django-based platform for fair and flexible hackathon judging. Built specifically for the **Quantathon**, this app supports expert-specific criteria filtering, secure one-time submissions, public voting, real-time statistics dashboards, detailed analytical visualizations, and automatic final score computation — all within an elegant, responsive, quantum-inspired interface.

---

## 🌟 Enhanced Features

* 🧠 **Dynamic Expert-Based Criteria Filtering**
  Judges only evaluate criteria aligned with their expertise (e.g., Quantum Tech Quality for quantum experts, Business Viability for business experts).

* 🔐 **Secure Single-Use Judge Links**
  Personalized judging links ensure each judge and public voter submits scores exactly once, enhancing integrity and accountability.

* 🧮 **Real-Time Score Aggregation and Analytics**
  Live calculation and presentation of scores, weighted averages, and dynamic ranking updates, accessible via intuitive dashboards for admins, judges, and the public.

* 🌍 **Dedicated Public Voting Interface**
  Allows community engagement with simplified scoring forms. Public votes are automatically integrated with appropriate weighting.

* ⚙️ **Admin Dashboard for Link and Judge Management**
  Comprehensive control for administrators, including automatic generation of judge-specific and public links, judge assignments, and access management.

* 📊 **Interactive Rankings and Visualization Dashboards**
  Detailed analytics with customizable Chart.js visualizations including final scores, criterion-level breakdowns, team comparisons, and voting patterns.

* 📤 **CSV and JSON Data Export**
  Admins can export complete judging data and analytics for further review or offline archiving.

* 🚨 **Robust Validation and Error Handling**
  Clearly communicates invalid or expired links with direct admin contact options.

---

## 🧱 Tech Stack

| Backend | Frontend | Styling     | Database & Hosting       |
| ------- | -------- | ----------- | ------------------------ |
| Django  | HTMX     | Bootstrap 5 | PostgreSQL (via Railway) |

---

## 📸 Screenshots

| Judge Interface                                                                          | Results                                                                                | Public Voting                                                                              |
| ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| ![Judge View](https://github.com/ChantelleAA/judging_criteria/blob/main/judge_view1.png) | ![Results](https://github.com/ChantelleAA/judging_criteria/blob/main/results_vid.mp4) | ![Public](https://github.com/ChantelleAA/judging_criteria/blob/main/public_judge_view.png) |

---

## 🧩 Core Models (Updated)

* `Judge`: Represents judges with assigned expertise areas (Quantum Expert, General Judge, Public).
* `JudgingCriteria`: Criteria including weighted scores for Quantum Tech Quality, Social Impact, Innovation, Presentation, Business Viability.
* `Score`: Individual criterion scores provided by judges for teams.
* `TeamSubmission`: Teams participating and evaluated.
* `TeamFinalScore`: Aggregates and weights individual scores automatically.
* `JudgingLink`: Secure, single-use URL generation for judges.
* `PublicVote`: Stores public voting results separately for community engagement insights.

---

## 🚀 Quick Setup

1. Clone and install dependencies:

```bash
git clone https://github.com/ChantelleAA/judging_criteria.git
cd judging_criteria
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Apply migrations and create admin:

```bash
python manage.py migrate
python manage.py createsuperuser
```

3. Launch app:

```bash
python manage.py runserver
```

Admin panel at `http://127.0.0.1:8000/admin`.

---

## 🧪 Admin Configuration Steps

1. Log in at `/admin/`
2. Populate Judges, Criteria, and Teams.
3. Generate and distribute judge-specific links at `/admin/generate-links/`.
4. Monitor and export live results at `/results/`.

---

## 🛡️ Security Highlights

* Single-use, secure voting links.
* Password-protected admin access.
* IP-based restrictions to prevent duplicate public votes.
* Anonymous public judging with no personal data stored.

---

## ✨ Live Demo

👉 [Public Judging Platform](https://judgingcriteria-production.up.railway.app/public-judge/)
👉 [Live Results Dashboard](https://judgingcriteria-production.up.railway.app/public-results/)
👉 [GitHub Repository](https://github.com/ChantelleAA/judging_criteria)

---

## 🙌 Credits

Developed by [Chantelle Amoako-Atta](https://linkedin.com/in/chantelleaa) with precision and care for the Quantathon event.

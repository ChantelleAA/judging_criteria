Here’s a comprehensive and well-structured `README.md` for your **Quantathon Judging App**, tailored to your style and standards:

---

# 🧑🏾‍⚖️ Quantathon Judging App

![Demo](https://github.com/ChantelleAA/ChantelleAA/blob/main/judging_demo.gif)

A streamlined Django-based platform for fair and flexible hackathon judging. Built for the **Quantathon**, this system supports expert-specific criteria filtering, secure one-time submissions, public voting, and automatic final score computation — all within an elegant, responsive interface.

---

## 🌟 Features

* 🧠 **Expert-Based Criteria Filtering**
  Judges only see the criteria they are assigned to based on their area of expertise (e.g. Business Viability, Innovation, Technical Execution).

* 🔐 **One-Time Secure Submissions**
  Each judge or public voter can only submit their scores once — preventing duplicates and encouraging thoughtful evaluations.

* 🧮 **Real-Time Score Aggregation**
  Scores across all criteria and judges are automatically averaged and updated, with results available on a central leaderboard.

* 🌍 **Public Voting Support**
  Separate interface for public voters to rate entries on simplified criteria. Their votes are factored in with the appropriate weight.

* ⚙️ **Admin Panel for Link Generation**
  Easily generate judging links from the Django Admin. Judges are emailed personalized links tied to their expertise.

* 📊 **Live Rankings Page**
  View cumulative scores and team rankings in a dedicated results dashboard.

---

## 🧱 Tech Stack

| Backend | Frontend | Styling     | DB & Hosting             |
| ------- | -------- | ----------- | ------------------------ |
| Django  | HTMX     | Bootstrap 5 | PostgreSQL (via Railway) |

---

## 📸 Screenshots

| Judge Interface                                                                    | Results                                                                   | Public Voting                                                                   |
| ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| ![Judge View](https://github.com/ChantelleAA/judging_criteria/blob/main/judge_view1.png) | ![Results](https://github.com/ChantelleAA/judging_criteria/blob/main/results_view.png) | ![Public](https://github.com/ChantelleAA/judging_criteria/blob/main/public_judge_view.png) |

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/ChantelleAA/judging_criteria.git
cd judging_criteria
```

### 2. Set up environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Apply migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create superuser

```bash
python manage.py createsuperuser
```

### 5. Run the server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/admin` to log in and begin managing judges, criteria, and links.

---

## 🧩 Core Models

* `Judge`: Represents a person judging, includes expertise field.
* `JudgingCriteria`: All scoring categories (e.g., Technicality, Presentation).
* `Score`: A judge’s rating for a team on a criterion.
* `TeamSubmission`: Teams being evaluated.
* `TeamFinalScore`: Auto-updated average scores per team.
* `JudgingLink`: Secure per-judge unique access.
* `PublicVote`: Simple form for public rating.

---

## 🗃️ Folder Structure

```
judging_criteria/
│
├── judging/              # Main app
│   ├── models.py         # Data schema
│   ├── views.py          # Logic for scoring, voting, results
│   ├── templates/        # Custom HTML templates
│   ├── static/           # Bootstrap + custom styles
│   └── admin.py          # Admin panel customizations
│
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🧪 Admin Setup Guide

1. Login: `/admin/`
2. Add judges under **Judge** model
3. Add judging criteria under **JudgingCriteria**
4. Add team submissions
5. Use **Generate Links** to produce secure judge URLs
6. Monitor results at `/results/`

---

## 🛡️ Security Notes

* All voting links are unique and single-use
* Admin access is password-protected
* No personal data is collected from public voters
* Criteria visibility is dynamically restricted per judge

---

## ✨ Live Demo

👉 [Judging Platform](https://judgingcriteria-production.up.railway.app/)
👉 [Results Page](https://judgingcriteria-production.up.railway.app/results/)
👉 [GitHub Repo](https://github.com/ChantelleAA/judging_criteria)

---

## 🙌 Credits

Built by [Chantelle Amoako-Atta](https://linkedin.com/in/chantelleaa) for the Quantathon judging team, with love and precision.

---

## 📄 License

[MIT License](LICENSE)

---

Would you like this version added to the `README.md` in your GitHub repo, or do you want a version that includes badges and shields too? I can also generate a `judging_demo.gif` placeholder if needed.

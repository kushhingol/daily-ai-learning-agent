# 🚀 Daily AI Learning Coach

**Daily AI Learning Coach** is an automated learning system that delivers a personalized AI lesson directly to your inbox every day using GitHub Actions, OpenAI, or Gemini.

The project generates a fresh AI topic, creates a structured 60-minute learning plan, and emails it to you automatically. It also maintains a learning history to prevent topic repetition, ensuring a continuous and diverse AI education journey.

### ✨ Features

- 🤖 AI-generated daily lessons using OpenAI or Gemini
- 📚 Structured 60-minute learning plans
- 📧 Automated email delivery via SMTP (Brevo supported)
- 🔄 Smart topic rotation with 30-day repetition avoidance
- ⚡ Zero Python dependencies (uses only the standard library)
- 🛡️ Fallback topic generation when AI APIs are unavailable
- ⏰ Fully automated through GitHub Actions scheduling
- 📝 Learning history tracking and persistence

### 🎯 Perfect For

- Developers learning AI and LLMs
- Software engineers exploring Generative AI
- Students building daily AI learning habits
- Teams running internal AI upskilling programs
- Anyone who wants a curated AI lesson every day

### 🏗️ How It Works

1. GitHub Actions triggers the workflow daily.
2. OpenAI or Gemini generates a unique AI learning topic.
3. A complete lesson and practice exercise are created.
4. The lesson is emailed to the learner.
5. Learning history is updated to avoid repeating recent topics.

Whether you're starting your AI journey or expanding your expertise, Daily AI Learning Coach helps you learn consistently—one focused lesson at a time.

This repository runs a daily GitHub Actions workflow that:

1. Uses Gemini or Open AI to generate one focused AI topic and lesson.
2. Builds a 60-minute learning plan.
3. Sends the lesson by email through SMTP.
4. Commits `learning_history.json` so topics are not repeated within 30 days.

The script uses the OpenAI or Gemini Responses API directly through the Python standard library, so there are no package dependencies to install. If `OPENAI_API_KEY` or `GEMINI_API_KEY` is missing or the API call fails, the script falls back to a small built-in topic list so the scheduled workflow can still produce an email.

## Free Mailer Option

Use Brevo's free SMTP relay. Brevo's official pricing/help pages currently list a free plan with 300 daily email sends, which is more than enough for one daily learning email.

Useful links:

- [Brevo free plan limits](https://help.brevo.com/hc/en-us/articles/208580669-What-are-the-limits-of-the-Free-plans-)
- [Brevo transactional email](https://www.brevo.com/products/transactional-email/)
- [GitHub Actions workflow syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)

## Setup

1. Create a GitHub repository and push this code.
2. Create a free Brevo account.
3. In Brevo, verify a sender email/domain.
4. In Brevo, create SMTP credentials.
5. In GitHub, open your repository settings:
   `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`.
6. Add these secrets:

| Secret           | Example                                   |
| ---------------- | ----------------------------------------- |
| `OPENAI_API_KEY` | Your OpenAI API key                       |
| `SMTP_HOST`      | `smtp-relay.brevo.com`                    |
| `SMTP_PORT`      | `587`                                     |
| `SMTP_USER`      | Your Brevo SMTP login                     |
| `SMTP_PASS`      | Your Brevo SMTP key                       |
| `MAIL_FROM`      | `Your Name <verified-sender@example.com>` |
| `MAIL_TO`        | `YOUR_EMAIL@example.com`                  |
| `GEMINI_API_KEY` | Your Gemini API key                       |
| `AI_VENDOR`      | `Gemini` or `OpenAI`                      |

Optional repository variable:

| Variable       | Default      |
| -------------- | ------------ |
| `OPENAI_MODEL` | `gpt-5-mini` |

## Running

The workflow runs every day at 8:30 AM Asia/Kolkata:

```yaml
schedule:
  - cron: "00 3 * * *"
```

GitHub cron schedules are evaluated in UTC, so `03:00 UTC` maps to `08:30 IST`.

You can also run it manually from:

`Actions` -> `Daily AI Learning Coach` -> `Run workflow`

## Local Test

Generate the email preview without sending:

```bash
python scripts/ai_learning_coach.py
```

or

```bash
python scripts/ai_learning_coach_gemini.py
```

Send locally after setting SMTP environment variables:

```bash
python scripts/ai_learning_coach.py --send
```

or

```bash
python scripts/ai_learning_coach_gemini.py --send
```

For local OpenAI topic generation, create a `.env` file:

```bash
cp .env.example .env
```

PowerShell:

```powershell
Copy-Item .env.example .env
```

```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-5-mini
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=your-brevo-smtp-login
SMTP_PASS=your-brevo-smtp-key
MAIL_FROM=Your Name <verified-sender@example.com>
MAIL_TO=YOUR_EMAIL@example.com
```

The generated email preview is written to:

```text
dist/daily-email.md
dist/daily-email.html
```

## Customizing Topics

The normal path asks OpenAI for a fresh topic each day while passing recent `learning_history.json` entries so the model avoids repeats. Edit the fallback `TOPICS` list in `scripts/ai_learning_coach.py` only if you want better offline behavior. Each topic includes:

- category
- one-line hook
- reading block
- practical exercise
- starter scaffold
- detailed practice steps
- success criteria
- stretch challenge

The workflow records completed topics in `learning_history.json` and avoids repeating topics from the last 30 days when alternatives exist.

## 🚀 Let's Connect

<p align="center">
  <img src="https://media.licdn.com/dms/image/v2/D4D03AQExq8xiys4Maw/profile-displayphoto-shrink_100_100/profile-displayphoto-shrink_100_100/0/1712999308042?e=1782345600&v=beta&t=8iYi3LQrNgnBsRyWtM2_YvsoR1MdtdbXOjl-FXMsEQM" alt="Kush Hingol" width="100" style="border-radius:50%;" />
</p>

<p align="center">
  <b>Kush Hingol</b><br>
  AI • Cloud • Software Engineering • Automation
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/kush-hingol/">
    <img src="https://img.shields.io/badge/Follow%20on-LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"/>
  </a>
</p>

<p align="center">
  If you enjoy this project, let's connect and discuss AI, AWS, Cloud Engineering, Automation, and Software Development.
</p>

⭐ If this repository helped you, consider giving it a star!

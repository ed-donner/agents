# 🤖 Telegram Customer Care Bot

This project is a continuation of the previous **Customer Care Agent**. The exciting part? You can now interact with the bot using **Telegram**! Ask your friends and family to try it out — anyone can experience it and see the capabilities of your smart assistant in action.

---

## ✅ Features

* ✅ It can answer normal user queries related to your brand or data
* ✅ It can interact with your actual database to get the most relevant and up-to-date data
* ✅ It can take an order from a user and place it in your database
* ✅ It can email users with their order summary
* ✅ Users can check their order status

---

## 🚀 Getting Started

### 1⃣ Set Up Environment Variables

Copy the `.env-example` file and rename it to `.env`. Fill in all the required credentials.

---

### 2⃣ Update Configuration Files

#### Edit `modules/tools/send_email.py`

Replace:

```python
<your_email>
```

with your actual sending email address.

#### Edit `modules/tools/setup_sheets.py`

Replace:

```python
<your_sheet_name>
```

with the name of your actual Google Sheet.

---

### 3⃣ Prepare Your Google Sheets

You need to create **two sheets** inside your Google Spreadsheet:

* `products`
* `orders`

You can download and upload this sample sheet to get started quickly:

📄 [Sample Sheets (Google Drive)](https://docs.google.com/spreadsheets/d/1mW1MWP85l0s10jDKSZv26q31P1Rtzbb5lQTn8Bqjzpg/edit?usp=sharing)

Make sure to get a `credentials.json` file from Google Cloud Platform with **edit access** to the sheet.

---

### 4⃣ Deploy to Render

1. Visit [https://render.com](https://render.com)
2. Create an account (if you haven’t already)
3. Deploy this project as a **Web Service**

---

### 5⃣ You're Ready to Go!

Once deployment is complete, you're all set! 🎉
Start interacting with your smart customer care agent through the **Telegram Bot** you built.

---

## 🤪 Share & Showcase

Show off your project to friends, family, or potential employers. Let anyone experience it in real time via Telegram.

---

Enjoy showcasing your project 🚀

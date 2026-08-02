# Deploying your twin to Render

_If you're looking at this in Cursor, please right click on the file in the File Explorer and select "Open Preview" to see the formatted version_

HuggingFace Spaces now requires a paid PRO subscription to host Gradio apps, so here is an alternative: [Render](https://render.com). Render has a free tier, doesn't ask for a credit card, and can run the twin exactly as it is, with no code changes.

One thing to know up front: on the free tier, your app goes to sleep after 15 minutes without visitors. The next visitor wakes it up, which takes 30 to 60 seconds. After that it responds normally.

## What you'll need

- A GitHub account (you probably have one already from cloning this course)
- Your OpenAI API key, and your Pushover user and token, from your `.env` file
- The `twin` directory, updated with your own `linkedin.pdf` and `summary.txt`

## Step 1: Put the twin in its own GitHub repository

Render deploys from a GitHub repository. This course repo won't work for that, because it contains everything else too, and it belongs to the course. You want a small separate repo containing just the contents of the `twin` directory.

The easiest way, with no git commands at all:

1. Go to [github.com/new](https://github.com/new) and create a repository. Call it `twin`. Choose **Private**, since your LinkedIn PDF is personal. Check the box to add a README so the repo isn't empty.
2. On your new repo's page, click **Add file**, then **Upload files**.
3. Drag in these 7 files from `1_foundations/twin` on your computer: `app.py`, `context.py`, `tools.py`, `styles.py`, `requirements.txt`, `summary.txt` and `linkedin.pdf`. Don't include the `__pycache__` folder if you see one.
4. Click **Commit changes**.

If you prefer the command line: copy the `twin` folder to somewhere outside this course repo first (for example `cp -r twin ~/twin`), then run `git init`, commit the files, and push to a new private GitHub repo in the usual way. The copy matters because creating a git repo inside the course repo causes confusion.

Never put your `.env` file or any API keys in the repo. Your keys will go into Render's dashboard in Step 4.

## Step 2: Create a Render account

1. Go to [render.com](https://render.com) and click **Sign In**, then sign up with your GitHub account. This makes the next step easier.
2. Verify your email if asked. You do not need to enter a credit card.

## Step 3: Create the web service

1. From the Render dashboard, click **New +** and choose **Web Service**.
2. Connect your GitHub account if prompted, and give Render access to your `twin` repository.
3. Select the `twin` repository.
4. Fill in the settings:
   - **Language**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Instance Type**: Free
5. Don't click Deploy yet. First add the environment variables below.

## Step 4: Environment variables

In the **Environment Variables** section of the same page (or later under the service's **Environment** tab), add these five:

| Key | Value |
|---|---|
| `OPENAI_API_KEY` | your OpenAI key from `.env` |
| `PUSHOVER_USER` | your Pushover user from `.env` |
| `PUSHOVER_TOKEN` | your Pushover token from `.env` |
| `GRADIO_SERVER_NAME` | `0.0.0.0` |
| `GRADIO_SERVER_PORT` | `10000` |

The last two need a word of explanation. Render expects your app to listen for web traffic on port 10000, and Gradio reads these two variables at startup, so this is how we tell Gradio where to listen. No code changes needed.

## Step 5: Deploy

1. Click **Deploy Web Service**.
2. Watch the logs. The first build takes a few minutes while it installs the requirements.
3. When you see the Gradio startup message in the logs, your app is live. The URL is at the top of the page and looks like `https://twin-xxxx.onrender.com`.
4. Open it and say hello to your twin. Check that a Pushover notification arrives when you share your email address with it.

## Updating your twin

When you change a file (for example improving `summary.txt`), upload the new version to the GitHub repo, or push if you used the command line. Render notices the change and redeploys automatically.

## Troubleshooting

- **The page takes ages to load.** If nobody has visited for 15 minutes, the app is asleep and takes up to a minute to wake. This is normal on the free tier.
- **The build fails.** Check the logs on the service page. The most common cause is a missing file, so confirm all 7 files are in the GitHub repo.
- **The app builds but the page shows an error.** Usually a missing or mistyped environment variable. Check all five under the **Environment** tab, then use **Manual Deploy** to restart.
- **No Pushover notifications.** Check `PUSHOVER_USER` and `PUSHOVER_TOKEN` in the Environment tab, and remember the user key starts with `u` and the token starts with `a`.

# Replit walkthrough — step by step

If you've never used Replit or run a web app before, this is for you.
Total time: ~15 minutes. You won't need to type any code.

---

## Step 1 — Get your free Gemini API key (3 min)

1. Open https://aistudio.google.com/apikey in a new tab.
2. Sign in with your Google account (the same one you use for Gmail
   or Google Classroom is fine).
3. Click the blue **"Create API key"** button.
4. If asked to pick a project, choose **"Create API key in new project."**
5. A long string starting with `AIzaSy...` appears. **Click the copy
   icon next to it.** Paste it into a notes app for a moment — you'll
   need it in Step 4.

> No credit card needed. The free tier gives you 1,500 lesson analyses
> per day on Gemini 2.5 Flash, which is way more than any single school
> leader will ever use.

---

## Step 2 — Sign up for Replit (2 min)

1. Open https://replit.com in a new tab.
2. Click **Sign up** in the top right.
3. The easiest option is **"Continue with Google."** Use the same
   Google account if you'd like — it just makes life simpler.
4. You'll land on the Replit dashboard. You can ignore any onboarding
   prompts about templates or tutorials.

---

## Step 3 — Create the project (3 min)

1. Top-right of the dashboard, click **"+ Create Repl."**
2. In the template picker, search for and choose **"Python."**
3. Name it `lesson-voice-analyzer`.
4. Make sure **"Public"** is selected (the free option). Click **"Create Repl."**
5. You'll see Replit's editor with three panes:
   - **Left:** file list (a single `main.py` is there now)
   - **Middle:** code editor
   - **Right:** a console/output panel

### Now bring in the project files

Download `lesson-voice-analyzer-replit.zip` and **unzip it on your
computer.** You should see a folder called `lesson-voice-analyzer-replit`
containing `app.py`, `analyzer.py`, etc.

6. In Replit, **delete the existing `main.py`** — right-click it in
   the file list, choose **Delete**, confirm.
7. **Drag the entire unzipped folder's contents** into the Replit file
   list (drag the files, not the wrapping folder — you want `app.py`
   at the root, not inside a subfolder).
   - The `samples/` folder should drag in as a folder with the
     transcript inside it.
   - The hidden `.replit` file might not drag — see the next step if so.
8. **Make sure `.replit` is there.** If you don't see it:
   - Click the three-dot menu (⋯) at the top of the file list
   - Toggle **"Show hidden files"** on
   - If `.replit` is still missing, click **"+ Add file"**, name it
     exactly `.replit` (with the leading dot), and paste in the
     contents from the file in your downloaded folder.

Your file list should look like:

```
.replit
README.md
REPLIT_GUIDE.md  (this file)
analyzer.py
app.py
prompts.py
report.py
requirements.txt
samples/
  sample_transcript.txt
```

---

## Step 4 — Add the Gemini key as a Secret (1 min)

**Never paste API keys into code files.** Replit has a Secrets feature
that keeps them safe and out of public view.

1. In the left sidebar, click the **🔒 Secrets** icon (sometimes called
   "Tools → Secrets" depending on your Replit version).
2. Click **"+ New Secret."**
3. **Key:** `GEMINI_API_KEY`  (exactly that, no quotes, no spaces)
4. **Value:** paste your Gemini key from Step 1
5. Click **Add Secret.**

---

## Step 5 — Run it (2 min)

1. Click the big green **▶ Run** button at the top.
2. The first run takes about 60–90 seconds — Replit is installing
   Python packages. You'll see lots of text scrolling in the console.
   That's normal.
3. When you see something like:
   ```
   You can now view your Streamlit app in your browser.
   Local URL: http://0.0.0.0:8080
   ```
   …Replit will open a **Webview** panel showing your app. If it
   doesn't pop up on its own, click the **"Webview"** tab at the top
   of the right pane.
4. You should see the **Lesson Voice Analyzer** with the sidebar nav.
   Click **"Load sample transcript,"** then **"Next →,"** then fill in
   the details on step 2 and click **"Analyze lesson →."**

If the analysis succeeds, you're done. 🎉

---

## Step 6 — Get a shareable URL (30 sec)

In the Webview panel, look at the URL bar. It will be something like:

```
https://lesson-voice-analyzer.YOUR-USERNAME.repl.co
```

**That URL is public.** You can send it to colleagues to try the tool.
It only works while the Repl is running, though — see "Keeping it
alive" below.

---

## Keeping it alive

Free Replit projects **go to sleep when no one's using them**, and
take a few seconds to wake up on the next visit. For a tool you
share with 2–5 colleagues, that's fine.

If you want it permanently on, Replit's **Deployments** feature
(paid, around $7/month) gives you an always-on URL. To set it up:

1. Click the **"Deploy"** button at the top of your Repl.
2. Choose **"Autoscale Deployment"** (cheapest, scales to zero).
3. Use the default settings — the `.replit` file already has the
   deployment command configured.
4. Click **Deploy.**

You'll get a stable URL like `lesson-voice-analyzer.replit.app`.

---

## Things that might go wrong

**"ModuleNotFoundError: No module named 'streamlit'"**
Replit hasn't finished installing packages. Wait 30 seconds and
click Run again.

**"GEMINI_API_KEY is not set" or any API key error**
Step 4 didn't save. Go back to the 🔒 Secrets pane, confirm the key
name is exactly `GEMINI_API_KEY`, then click Stop and Run again.

**The Webview shows a blank page**
Sometimes the first connection is flaky. Click the refresh icon in
the Webview, or open the URL in a new tab.

**"Cannot connect" / port errors**
Make sure `.replit` made it into your project (Step 3, point 8).
Without it, Replit doesn't know to start Streamlit.

**Reports look different each time on the same transcript**
That's normal — the language model isn't deterministic. The numbers
(talk-time, question count) will always be the same, but the coaching
phrasing will vary. If you want stricter consistency, open
`analyzer.py` and change `temperature=0.3` to `temperature=0.0` in
the `call_llm` function.

**Anything else**
Take a screenshot, paste it back into our chat, and I'll help debug.

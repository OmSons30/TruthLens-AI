---
description: How to deploy the TruthLens AI application (Frontend on Vercel and Backend on Render)
---

This guide details how to deploy the TruthLens AI platform live on free hosting tiers.

## Step 1: Deploy Backend to Render

1. Go to [Render](https://render.com/) and sign up/log in with your GitHub account.
2. Click **New +** and select **Web Service**.
3. Choose the **Connect a repository** option and select your `TruthLens-AI` repository.
4. Configure the Web Service settings:
   - **Name**: `truthlens-backend`
   - **Root Directory**: `backend` (Important: do not leave empty)
   - **Language**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Select the **Free** plan.
5. Add Environment Variables:
   - Go to the **Environment** tab on Render.
   - Click **Add Environment Variable**:
     - `OPENAI_API_KEY` = `your_openai_api_key_here`
     - `OPENAI_MODEL` = `gpt-4o-mini`
6. Click **Create Web Service** to deploy.
7. Once deployed, copy the Render URL (e.g., `https://truthlens-backend.onrender.com`).

---

## Step 2: Deploy Frontend to Vercel

1. Go to [Vercel](https://vercel.com/) and log in with your GitHub account.
2. Click **Add New** and select **Project**.
3. Import your `TruthLens-AI` repository.
4. Configure the Project settings:
   - **Framework Preset**: `Vite` (Vercel should auto-detect this)
   - **Root Directory**: Click **Edit** and select the `frontend` folder.
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Add Environment Variables (optional, if your frontend points to the backend dynamically):
   - Add `VITE_API_URL` = `https://your-backend-url.onrender.com` (use your actual Render URL).
6. Click **Deploy**.

---

## Step 3: Update Frontend API calls (If needed)

Ensure that your frontend code (typically in request/service functions) uses the environment variable `import.meta.env.VITE_API_URL` instead of a hardcoded `localhost:8000`.

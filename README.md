# RSS Maker

## Deploy on Render (Free 24/7)

1. GitHub-এ এই ফাইলগুলো আপলোড করো।
2. Render.com → New → Web Service → GitHub repo সিলেক্ট করো।
3. Build: `pip install -r requirements.txt`
4. Start: `gunicorn -w 2 -k gthread -b 0.0.0.0:$PORT main:app`
5. Deploy হলে URL পাবে: `https://your-app.onrender.com`

### Usage
/feed?url=TARGET_URL&selector=CSS_SELECTOR&limit=30

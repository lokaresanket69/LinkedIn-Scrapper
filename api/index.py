from main import app

# This file is specifically for Vercel deployment
# Vercel uses the serverless function approach, so this file directs traffic to your Flask app

# The vercel.json file configures routes to send all traffic to this handler
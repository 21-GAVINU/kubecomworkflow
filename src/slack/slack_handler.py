import logging
import os
from flask import Flask, request, jsonify
from slackeventsapi import SlackEventAdapter
import slack
from src.config.config import SIGNING_SECRET, SLACK_BOT_TOKEN  # Import from config
from src.intent_processing.message_processor import process_slack_message
from src.config.logging_config import logger  # Central logging configuration
from src.lifecycle.lifecycle import send_processing_message  # Import lifecycle function

# Initialize Flask app
app = Flask(__name__)

# Validate environment variables
if not SIGNING_SECRET or not SLACK_BOT_TOKEN:
    logger.error("Missing Slack environment variables. Check your .env file!")
    exit(1)

# Initialize Slack Event Adapter and Slack WebClient
slack_events_adapter = SlackEventAdapter(SIGNING_SECRET, "/slack/events", app)
web_client = slack.WebClient(token=SLACK_BOT_TOKEN)

@app.route("/test", methods=["POST"])
def test_endpoint():
    data = request.get_json()
    logger.info(f"Test endpoint received: {data}")
    return jsonify({"status": "received", "data": data})

# Global set to track processed event_ids for deduplication
processed_events = set()

@slack_events_adapter.on("message")
def handle_message_event(payload):
    global processed_events
    event_id = payload.get("event_id")
    if event_id in processed_events:
        logger.info(f"🔁 Skipping duplicate event: {event_id}")
        return
    processed_events.add(event_id)
    
    try:
        logger.info(f"🔍 Raw Slack Event: {payload}")

        event = payload.get("event", {})
        user_id = event.get("user")
        text = event.get("text")
        channel_id = event.get("channel")

        logger.info(f"📩 Received message from User: {user_id}, Channel: {channel_id}, Text: {text}")

        # Check if the event has text and ignore bot messages
        if not text:
            logger.warning("⚠️ No text found in the event payload.")
            return

        if "bot_id" in event:
            logger.info("🤖 Ignoring bot message.")
            return

        # Send a processing acknowledgment message using lifecycle function
        logger.info("Sending processing acknowledgment to user")
        send_processing_message(channel_id, text)

        # Use the generator to get live updates from processing
        for update in process_slack_message(text):
            # Each update is a dict with keys 'stage' and 'message'
            web_client.chat_postMessage(channel=channel_id, text=update["message"])

    except Exception as e:
        logger.error(f"⚠️ Error processing Slack event: {e}")

def start_slack_bot():
    logger.info("🚀 Starting Slack bot on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

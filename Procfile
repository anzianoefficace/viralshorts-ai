web: gunicorn simple_app:app
worker: python -c "from daily_auto_poster import DailyAutoPoster; poster = DailyAutoPoster(); poster.start()"

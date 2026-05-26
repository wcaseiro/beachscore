def timeline_summary(events):
    return [
        {
            "id": event["id"],
            "action": event["action"],
            "text": event["text"],
            "created_at": event["created_at"],
        }
        for event in events
    ]

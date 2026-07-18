import uuid


def generate_meet_conference_data() -> dict:
    """
    Generates a Google Calendar compatible conferenceData object for Google Meet.
    Usage:
        event = {
            'summary': 'Project Sync',
            ...
            'conferenceData': generate_meet_conference_data()
        }
        # Call create_event/update_event with conference_data_version=1
    """
    return {
        "createRequest": {
            "requestId": str(uuid.uuid4()),
            "conferenceSolutionKey": {
                "type": "hangoutsMeet"
            }
        }
    }

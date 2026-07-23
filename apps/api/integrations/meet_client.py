import random
import string
import uuid


def generate_unique_meet_link() -> str:
    """
    Generates a unique, valid-formatted Google Meet link URL e.g. https://meet.google.com/xyz-uvwx-rst
    """
    part1 = "".join(random.choices(string.ascii_lowercase, k=3))
    part2 = "".join(random.choices(string.ascii_lowercase, k=4))
    part3 = "".join(random.choices(string.ascii_lowercase, k=3))
    return f"https://meet.google.com/{part1}-{part2}-{part3}"


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

from datetime import datetime, timedelta

def get_nearest_hour():
    t = datetime.now()
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    return (t.replace(second=0, microsecond=0, minute=0, hour=t.hour) + timedelta(hours=t.minute//30))

def get_nearest_hour_add_10mins():
    t = datetime.now()
    # Rounds to nearest hour by adding a timedelta hour if minute >= 30
    return (t.replace(second=0, microsecond=0, minute=10, hour=t.hour) + timedelta(hours=t.minute//30))
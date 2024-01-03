class Team:

    def __init__(self, **kwargs):
        self.team = kwargs.get("team")
        self.stadium = kwargs.get("stadium")
        self.city = kwargs.get("city")
        self.state = kwargs.get("state")
        self.lat = kwargs.get("lat")
        self.long = kwargs.get("long")
        self.vila_distance = round(kwargs.get("vila_distance"), 4)

    def __str__(self):
        return f"team: {self.team} == distance: {self.vila_distance}"
    
    def __repr__(self):
        return f"team: {self.team} == distance: {self.vila_distance}"

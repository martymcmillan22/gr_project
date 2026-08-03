class LatticeManager:
    """
    Core infrastructure for the 12-Compartment Lattice.
    Acts as the source of truth for validation and system capacity.
    """
    CONFIG = {
        1:  {"color": "Red", "category": "Math", "time": "Past", "capacity": 4},
        2:  {"color": "Blue", "category": "Language", "time": "Pres-Past", "capacity": 16},
        3:  {"color": "Yellow", "category": "Arts", "time": "Pres-Fut", "capacity": 64},
        4:  {"color": "Green", "category": "Science", "time": "Future", "capacity": 256},
        5:  {"color": "Purple", "category": "General Information", "time": "Past", "capacity": 1024},
        6:  {"color": "Teal", "category": "Literature", "time": "Pres-Past", "capacity": 4096},
        7:  {"color": "Orange", "category": "Crafts", "time": "Pres-Fut", "capacity": 16384},
        8:  {"color": "Lime", "category": "Technology", "time": "Future", "capacity": 65536},
        9:  {"color": "Pink", "category": "History", "time": "Past", "capacity": 262144},
        10: {"color": "Cyan", "category": "Geography", "time": "Pres-Past", "capacity": 1048576},
        11: {"color": "Amber", "category": "Architecture", "time": "Pres-Fut", "capacity": 4194304},
        12: {"color": "Green-Lime", "category": "Ecology", "time": "Future", "capacity": 16777216},
    }

    @classmethod
    def validate_submission(cls, lattice_id, content):
        config = cls.CONFIG.get(lattice_id)
        if not config:
            return {"status": "error", "message": "Invalid Lattice ID"}
        
        # Enforce Capacity Constraint
        if len(content) > config['capacity']:
            return {"status": "rejected", "message": f"Content exceeds {config['capacity']} bytes"}
        
        return {"status": "approved", "category": config['category']}
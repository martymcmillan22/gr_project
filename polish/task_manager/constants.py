PHASE_CREATE = "create"
PHASE_POST = "post"
PHASE_WORK = "work"

BTIF_PHASE_ORDER = (PHASE_CREATE, PHASE_POST, PHASE_WORK)
BTIF_COMPARTMENTS_BY_PHASE = {
    PHASE_CREATE: ("R", "B", "Y", "G"),
    PHASE_POST: ("P", "T", "O", "L"),
    PHASE_WORK: ("P", "C", "A", "G-L"),
}

ASSIGNMENT_LINEAR = "linear"
ASSIGNMENT_DOUBLE_LINEAR = "double_linear"
ASSIGNMENT_TWELVE_POINT = "twelve_point"
ASSIGNMENT_PERPETUAL = "perpetual"

ASSIGNMENT_CHOICES = (
    (ASSIGNMENT_LINEAR, "Linear Assignment"),
    (ASSIGNMENT_DOUBLE_LINEAR, "2x Linear Assignment"),
    (ASSIGNMENT_TWELVE_POINT, "12-Point Assignment"),
    (ASSIGNMENT_PERPETUAL, "Perpetual Assignment"),
)

ASSIGNMENT_DOCUMENT_TITLES = {
    ASSIGNMENT_LINEAR: "Linear document",
    ASSIGNMENT_DOUBLE_LINEAR: "2xlinear document",
    ASSIGNMENT_TWELVE_POINT: "12 Point Document",
    ASSIGNMENT_PERPETUAL: "Perpetual Document",
}

ITEM_STATUS_RECEIVED = "received"
ITEM_STATUS_WORKING = "working"
ITEM_STATUS_COMPLETED = "completed"

ITEM_STATUS_CHOICES = (
    (ITEM_STATUS_RECEIVED, "Received"),
    (ITEM_STATUS_WORKING, "Working"),
    (ITEM_STATUS_COMPLETED, "Completed"),
)


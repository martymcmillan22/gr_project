DOMAIN_CELLS = {
	"cp": {
		"label": "CP",
		"color": "#d72638",
		"color_tint": "#f8d7db",
		"color_name": "Red",
		"subject": "Math",
		"time": "1 pm",
		"srl": "4",
	},
	"in": {
		"label": "IN",
		"color": "#1f6feb",
		"color_tint": "#d6e6ff",
		"color_name": "Blue",
		"subject": "Language",
		"time": "2 pm",
		"srl": "16",
	},
	"dc-yellow": {
		"label": "DC",
		"color": "#f2c94c",
		"color_tint": "#fff3cd",
		"color_name": "Yellow",
		"subject": "Arts",
		"time": "3 pm",
		"srl": "64",
	},
	"no-green": {
		"label": "NO",
		"color": "#2e7d32",
		"color_tint": "#d7f2d8",
		"color_name": "Green",
		"subject": "Science",
		"time": "4 pm",
		"srl": "256",
	},
	"bot": {
		"label": "BOT",
		"color": "#7a3db8",
		"color_tint": "#eadbfa",
		"color_name": "Purple",
		"subject": "General Information",
		"time": "5 pm",
		"srl": "1,024",
	},
	"analyze": {
		"label": "Analyze",
		"color": "#0f766e",
		"color_tint": "#d5f6f2",
		"color_name": "Teal",
		"subject": "Literature",
		"time": "6 pm",
		"srl": "4,096",
	},
	"evaluate": {
		"label": "Evaluate",
		"color": "#f97316",
		"color_tint": "#ffe4d1",
		"color_name": "Orange",
		"subject": "Crafts",
		"time": "7 pm",
		"srl": "16,384",
	},
	"persuasive": {
		"label": "Persuasive",
		"color": "#84cc16",
		"color_tint": "#effccb",
		"color_name": "Lime",
		"subject": "Technology",
		"time": "8 pm",
		"srl": "65,536",
	},
	"ptg": {
		"label": "PTG",
		"color": "#ec4899",
		"color_tint": "#ffd8eb",
		"color_name": "Pink",
		"subject": "History",
		"time": "9 pm",
		"srl": "262,144",
	},
	"phd": {
		"label": "PH&D",
		"color": "#06b6d4",
		"color_tint": "#d8f8ff",
		"color_name": "Cyan",
		"subject": "Geography",
		"time": "10 pm",
		"srl": "1,048,576",
	},
	"lw": {
		"label": "LW",
		"color": "#f59e0b",
		"color_tint": "#fff0cf",
		"color_name": "Amber",
		"subject": "Architecture",
		"time": "11 pm",
		"srl": "4,194,304",
	},
	"tr": {
		"label": "TR",
		"color": "#65a30d",
		"color_tint": "#ecfbc9",
		"color_name": "Green-Lime",
		"subject": "Ecology",
		"time": "12 am",
		"srl": "16,777,216",
	},
}

DOMAIN_CELL_ALIASES = {
	"bos-domain": {**DOMAIN_CELLS["cp"], "label": "BOS Domain"},
	"bridge-domain": {**DOMAIN_CELLS["in"], "label": "Bridge Domain"},
	"openfields-domain": {**DOMAIN_CELLS["dc-yellow"], "label": "OpenFields Domain"},
	"seedlings-domain": {**DOMAIN_CELLS["no-green"], "label": "Seedlings Domain"},
	"roots-domain": {**DOMAIN_CELLS["bot"], "label": "Roots Domain"},
	"growth-domain": {**DOMAIN_CELLS["analyze"], "label": "Growth Domain"},
	"sunrise-domain": {**DOMAIN_CELLS["evaluate"], "label": "Sunrise Domain"},
	"pathways-domain": {**DOMAIN_CELLS["persuasive"], "label": "Pathways Domain"},
	"community-domain": {**DOMAIN_CELLS["ptg"], "label": "Community Domain"},
	"exchange-domain": {**DOMAIN_CELLS["phd"], "label": "Exchange Domain"},
	"harvestprep-domain": {**DOMAIN_CELLS["lw"], "label": "HarvestPrep Domain"},
	"harvestcrops-domain": {**DOMAIN_CELLS["tr"], "label": "HarvestCrops Domain"},
}

DOMAIN_CELLS.update(DOMAIN_CELL_ALIASES)

DOMAIN_COMPARTMENT_DEFINITIONS = [
	{"slug": "cp", "field": "compartment_1_label", "default": "CP", "form_label": "Compartment 1", "editable": True, "min_length": 12},
	{"slug": "in", "field": "compartment_2_label", "default": "IN", "form_label": "Compartment 2", "editable": True, "min_length": 12},
	{"slug": "dc-yellow", "field": "compartment_3_label", "default": "DC", "form_label": "Compartment 3", "editable": True, "min_length": 12},
	{"slug": "no-green", "field": "compartment_4_label", "default": "NO", "form_label": "Compartment 4", "editable": True, "min_length": 12},
	{"slug": "bot", "field": "compartment_5_label", "default": "BOT", "form_label": "Compartment 5", "editable": True, "min_length": 12},
	{"slug": "analyze", "field": "compartment_6_label", "default": "Analyze", "form_label": "Compartment 6", "editable": False},
	{"slug": "evaluate", "field": "compartment_7_label", "default": "Evaluate", "form_label": "Compartment 7", "editable": False},
	{"slug": "persuasive", "field": "compartment_8_label", "default": "Persuasive", "form_label": "Compartment 8", "editable": True, "min_length": 12},
	{"slug": "ptg", "field": "compartment_9_label", "default": "PTG", "form_label": "Compartment 9", "editable": True, "min_length": 12},
	{"slug": "phd", "field": "compartment_10_label", "default": "PH&D", "form_label": "Compartment 10", "editable": True, "min_length": 12},
	{"slug": "lw", "field": "compartment_11_label", "default": "LW", "form_label": "Compartment 11", "editable": True, "min_length": 12},
	{"slug": "tr", "field": "compartment_12_label", "default": "TR", "form_label": "Compartment 12", "editable": True, "min_length": 12},
]

DOMAIN_CELL_FIELD_BY_SLUG = {item["slug"]: item["field"] for item in DOMAIN_COMPARTMENT_DEFINITIONS}
DOMAIN_CELL_FIELD_BY_SLUG.update({
	"bos-domain": "compartment_1_label",
	"bridge-domain": "compartment_2_label",
	"openfields-domain": "compartment_3_label",
	"seedlings-domain": "compartment_4_label",
	"roots-domain": "compartment_5_label",
	"growth-domain": "compartment_6_label",
	"sunrise-domain": "compartment_7_label",
	"pathways-domain": "compartment_8_label",
	"community-domain": "compartment_9_label",
	"exchange-domain": "compartment_10_label",
	"harvestprep-domain": "compartment_11_label",
	"harvestcrops-domain": "compartment_12_label",
})
DOMAIN_EDITABLE_COMPARTMENT_FIELDS = [item["field"] for item in DOMAIN_COMPARTMENT_DEFINITIONS if item["editable"]]
DOMAIN_LOCKED_COMPARTMENT_FIELDS = [item["field"] for item in DOMAIN_COMPARTMENT_DEFINITIONS if not item["editable"]]
DOMAIN_DEFAULT_COMPARTMENT_VALUES = {item["field"]: item["default"] for item in DOMAIN_COMPARTMENT_DEFINITIONS}

DOMAIN_BOARD_DEFINITIONS = [
	{"field": "board_corporation_label", "default": "Personal Corporation", "form_label": "Board Card 1", "min_length": 16},
	{"field": "board_museum_label", "default": "Personal Museum", "form_label": "Board Card 2", "min_length": 16},
	{"field": "board_garden_label", "default": "Personal Garden", "form_label": "Board Card 3", "min_length": 16},
]

DOMAIN_EDITABLE_BOARD_FIELDS = [item["field"] for item in DOMAIN_BOARD_DEFINITIONS]
DOMAIN_DEFAULT_BOARD_VALUES = {item["field"]: item["default"] for item in DOMAIN_BOARD_DEFINITIONS}

DOMAIN_DEFAULT_PROFILE_VALUES = {
	**DOMAIN_DEFAULT_COMPARTMENT_VALUES,
	**DOMAIN_DEFAULT_BOARD_VALUES,
}
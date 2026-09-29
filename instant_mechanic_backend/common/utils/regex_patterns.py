import re

AUTOMOTIVE_KEYWORDS: frozenset[str] = frozenset({
    # Vehicle parts
    "engine", "motor", "transmission", "gearbox", "brake", "brakes",
    "tyre", "tire", "wheel", "exhaust", "muffler", "radiator", "coolant",
    "battery", "alternator", "starter", "clutch", "suspension", "shock",
    "absorber", "strut", "axle", "differential", "driveshaft", "cv joint",
    "oil", "fuel", "petrol", "diesel", "spark plug", "ignition", "coil",
    "injector", "carburetor", "throttle", "turbo", "intercooler",
    "catalytic", "converter", "dpf", "egr", "valve", "camshaft", "crankshaft",
    "timing", "belt", "chain", "head gasket", "piston", "cylinder",
    "air filter", "cabin filter", "power steering", "rack", "pinion",
    "caliper", "rotor", "drum", "pad", "abs", "traction", "esp",
    "headlight", "taillight", "indicator", "wiper", "horn", "ac",
    "compressor", "condenser", "evaporator", "heater", "thermostat",
    # Symptoms / actions
    "stalling", "stall", "knocking", "knock", "vibrating", "vibration",
    "shaking", "shake", "leaking", "leak", "smoking", "smoke", "overheating",
    "overheat", "squealing", "squeal", "grinding", "grind", "clicking",
    "click", "rattling", "rattle", "misfiring", "misfire", "surging",
    "surge", "hesitating", "hesitate", "backfiring", "backfire",
    "check engine", "warning light", "dashboard", "rpm", "idle",
    "starting", "won't start", "dead", "flat", "puncture",
    # Car brands
    "toyota", "honda", "hyundai", "kia", "ford", "chevrolet", "bmw",
    "mercedes", "audi", "volkswagen", "vw", "nissan", "mazda", "subaru",
    "suzuki", "maruti", "tata", "mahindra", "renault", "skoda", "jeep",
    # Generic vehicle terms
    "car", "vehicle", "automobile", "sedan", "suv", "hatchback", "truck",
    "van", "bike", "motorcycle", "scooter", "mechanic", "garage", "service",
    "repair", "inspect", "maintenance", "mot", "service centre",
})

HARD_REJECT_PATTERNS: list[str] = [
    r"\b(recipe|cooking|baking|food|restaurant|menu|cuisine)\b",
    r"\b(weather|forecast|rain|temperature|humidity|climate)\b",
    r"\b(stocks?|shares?|invest|crypto|bitcoin|finance|market)\b",
    r"\b(politics|election|government|minister|president|parliament)\b",
    r"\b(movie|film|series|netflix|tv show|music|song|album)\b",
    r"\b(homework|essay|poem|translate|maths|math|algebra|calculus)\b",
    r"\b(write me|tell me a joke|write a|generate a|create a poem)\b",
    r"\b(sports|cricket|football|soccer|tennis|match|score)\b",
]

GREETING_PATTERNS: list[str] = [
    r"\b(hi|hello|hey|hiya|howdy|good\s+morning|good\s+afternoon|good\s+evening|what'?s\s+up)\b",
]

FAREWELL_PATTERNS: list[str] = [
    r"\b(bye|goodbye|good\s*bye|see\s+you|later|thanks|thank\s+you|cheers|done|all\s+good)\b",
]

BOOKING_PATTERNS: list[str] = [
    r"\b(book|booking|schedule|appointment|visit|send\s+a\s+mechanic|get\s+help|need\s+a\s+mechanic)\b",
]

UPLOAD_PATTERNS: list[str] = [
    r"\b(upload|attach|send|share|photo|image|picture|video|recording|audio|file|clip)\b",
]

ISSUE_PATTERNS: list[str] = [
    # Whole words
    r"\b(problem|issue|trouble|noise|sound|leak|check\s+engine|warning|light|not\s+working|"
    r"broken|fault|error|broke\s+down|breakdown|dead|flat|puncture|stuck)\b",
    # Stems — no trailing \b so "vibrat" matches "vibrating", "overheat" matches "overheating"
    r"\b(smok|stall|vibrat|shak|squeal|squeak|grind|rattl|knock|click|overheat|dying|drain|"
    r"misfir|jerk|slipp|fail|burn|hiss|wobbl|pull(s|ing)?\s+to)",
    # Negated function: "won't start", "not starting", "doesn't crank", "can't shift"
    r"\b(won'?t|wont|doesn'?t|does\s+not|isn'?t|is\s+not|can'?t|cannot|not)\s+\w+",
    r"\bhard\s+to\s+\w+",
]


def compile_patterns(patterns: list[str]) -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


COMPILED_HARD_REJECTS = compile_patterns(HARD_REJECT_PATTERNS)
COMPILED_GREETINGS = compile_patterns(GREETING_PATTERNS)
COMPILED_FAREWELLS = compile_patterns(FAREWELL_PATTERNS)
COMPILED_BOOKINGS = compile_patterns(BOOKING_PATTERNS)
COMPILED_UPLOADS = compile_patterns(UPLOAD_PATTERNS)
COMPILED_ISSUES = compile_patterns(ISSUE_PATTERNS)

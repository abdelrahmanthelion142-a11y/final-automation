"""Doctor name translator module.

This module maintains a static dictionary mapping English doctor names
to Arabic names for use in follow-up messages.
"""

import logging

logger = logging.getLogger(__name__)

# To add a new doctor:
# 1. Add their lowercase English first name as key
# 2. Add their Arabic name as value
# 3. If the first name is "eman" or "mohamed", use full lowercase name as key
#    (e.g., "eman hassan": "إيمان")

DOCTOR_TRANSLATIONS: dict[str, str] = {
    # Standard first-name lookups
    # "john": "جون",
    # "sarah": "سارة",
    #
    # Full-name lookups for disambiguation (eman, mohamed)
    # "eman lastname": "إيمان",
    # "mohamed lastname": "محمد",
    "ayaa": "آية",
    "mariam": "مريم",
    "hamed": "حامد",
    "nehal": "نهال",
    "badr": "بدر",
    "mohamed abdelwahab": "محمد عبد الوهاب",
    "mohamed azab": "محمد عزب",
    "samar": "سمر",
    "dina": "دينا",
    "hanan": "حنان",
    "mohamed ashour": "محمد عاشور",
    "reham": "ريهام",
    "marah": "مرح",
    "nada": "ندى",
    "asmaa": "أسماء",
    "miraam": "ميرام",
    "eman ahmed": "إيمان أحمد",
    "eman nasr": "يمان نصر",
    "ragaa": "رجاء",
    "walaa": "ولاء",
    "najwan": "نجوان",
    "mona": "مني",
    "yousra": "يسرا",
    "mahmoud": "محمود",
    "ranya": "رانيا",
}

FULL_NAME_DOCTORS = {"eman", "mohamed"}

logger.info(
    f"Doctor translation dictionary loaded with {len(DOCTOR_TRANSLATIONS)} entries"
)


def translate_doctor(english_name: str) -> str:
    """Translate an English doctor name to Arabic.

    Args:
        english_name: Doctor's name in English (from EHR)

    Returns:
        str: Arabic translation if found, otherwise the original English name

    Side effects:
        Logs a WARNING if the doctor name is not in the translation dictionary

    Disambiguation rule:
        - For doctors named "eman" or "mohamed", use the full lowercase name as lookup key
        - For all other doctors, use just the first name as lookup key
    """
    first_name = english_name.strip().split()[0].lower()

    if first_name in FULL_NAME_DOCTORS:
        lookup_key = english_name.strip().lower()
    else:
        lookup_key = first_name

    if lookup_key in DOCTOR_TRANSLATIONS:
        return DOCTOR_TRANSLATIONS[lookup_key]

    logger.warning(
        f"Doctor '{english_name}' not in translation dictionary — using English name"
    )
    return english_name

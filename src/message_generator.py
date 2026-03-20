"""Message generator module for creating personalised Arabic follow-up messages.

This module generates gender-aware Arabic WhatsApp follow-up messages
using the correct verb forms based on patient gender.
"""

import logging

logger = logging.getLogger(__name__)


def generate_message(
    patient_name: str, gender: str, doctor_arabic: str, date: str
) -> str:
    """Generate a personalised Arabic follow-up message.

    Args:
        patient_name: Patient's first name (Arabic)
        gender: "Male" or "Female" (empty defaults to masculine)
        doctor_arabic: Doctor's name in Arabic
        date: Appointment date string

    Returns:
        str: Complete Arabic message with gendered verbs and doctor name

    Side effects:
        Logs a WARNING if gender is empty/unknown (defaults to masculine)

    Gender-verb mapping:
        - Female: "تكوني" (takunī)
        - Male/Unknown: "تكون" (takun)

    Doctor prefix rule:
        - If doctor_arabic == "آية": no prefix (use name as-is)
        - Otherwise: prefix with "د/" → "د/{doctor_arabic}"
    """
    if gender == "Female":
        verb = "تكوني"
    elif gender == "Male":
        verb = "تكون"
    else:
        verb = "تكون"
        logger.warning(
            f"Unknown gender for patient '{patient_name}', defaulting to masculine form"
        )

    if doctor_arabic == "آية":
        doctor_display = doctor_arabic
    else:
        doctor_display = f"د/{doctor_arabic}"

    message = f"""مرحبا {patient_name} 👋🏻
بنتمنالك يوم سعيد 🌸
هاي رسالة تذكيرية بموعدك في عيادة WellSkin مع {doctor_display} بتاريخ {date} 📅
بنتمنى {verb} بصحة وعافية دايمًا 💛
لو عندك اي استفسار تواصل/ي معنا 📲"""

    return message

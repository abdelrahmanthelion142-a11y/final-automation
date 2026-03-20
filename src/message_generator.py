"""Message generator module for creating personalised Arabic follow-up messages.

This module generates gender-aware Arabic WhatsApp follow-up messages
using the correct verb forms based on patient gender.
"""

import logging

logger = logging.getLogger(__name__)


def get_verb_form(gender: str) -> str:
    """Get the correct Arabic verb form based on gender.

    Args:
        gender: "Male" or "Female"

    Returns:
        str: Arabic verb form ("تكوني" for female, "تكون" for male/unknown)
    """
    if gender == "Female":
        return "تكوني"
    return "تكون"


def generate_message(row: dict) -> str:
    """Generate a personalised Arabic follow-up message.

    Args:
        row: DataFrame row containing Patient, Gender, DoctorArabic

    Returns:
        str: Complete Arabic message
    """
    verb = get_verb_form(row["Gender"])
    title = "د/" if row["Doctor"] != "آية" else ""

    msg = f"""مساء الخير أ / {row["Patient"]}
نتمنى حضرتك {verb} بخير.
مع حضرتك أسماء من
           Wellskin Clinic ❤
حابين نعرف رأي حضرتك في الجلسة اللي عملناها مع {title}{row["DoctorArabic"]}
ولو عند حضرتك أي ملاحظات تخص الكلينك من حيث (الاستقبال / النظافة) لتحسين مستوى الخدمة.
"""
    return msg

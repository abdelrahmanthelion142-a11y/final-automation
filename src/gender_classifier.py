"""Gender classifier module for determining patient gender from names.

This module classifies patient genders using:
1. CSV lookup from Google Drive (known genders)
2. OpenAI fallback for unknown names
"""

import os
import logging
from typing import Any

import pandas as pd
from openai import OpenAI
from pydantic import BaseModel
from typing import List


logger = logging.getLogger(__name__)


class PatientGender(BaseModel):
    name: str
    gender: str


class PatientGenderList(BaseModel):
    patients: List[PatientGender]


def classify_from_csv(
    first_names: list[str], gender_df: pd.DataFrame
) -> dict[str, str]:
    """Look up gender classifications from the CSV knowledge base.

    Args:
        first_names: List of patient first names to look up
        gender_df: DataFrame with columns ["Patient", "Gender"]

    Returns:
        dict[str, str]: Mapping of {name: gender} for names found in CSV

    Side effects:
        Logs the count of names found
    """
    if len(gender_df) == 0:
        logger.info("Gender CSV is empty")
        return {}

    gender_map = dict(zip(gender_df["Patient"], gender_df["Gender"]))

    found = {}
    for name in first_names:
        if name in gender_map:
            found[name] = gender_map[name]

    logger.info(f"Gender mapped from CSV: {len(found)} / {len(first_names)}")
    return found


def classify_from_ai(unknown_names: list[str]) -> dict[str, str]:
    """Classify unknown names using OpenAI.

    Args:
        unknown_names: List of patient first names not found in CSV

    Returns:
        dict[str, str]: Mapping of {name: gender} for names classified by AI.
            Keys are the original input names (not the AI-returned names),
            ensuring exact match with the DataFrame.

    Raises:
        Exception: If the OpenAI API call fails (connection error, auth error, etc.)

    Side effects:
        - Makes API call to OpenAI
        - Logs count of names classified
    """
    if not unknown_names:
        return {}

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    # Number the names so results come back in order
    numbered = "\n".join(f"{i+1}. {name}" for i, name in enumerate(unknown_names))
    prompt = (
        f"Classify the gender of these Arabic first names as Male or Female. "
        f"Return them in the same order:\n{numbered}"
    )

    response = client.responses.parse(
        model="gpt-5.4-nano",
        input=[{"role": "user", "content": prompt}],
        text_format=PatientGenderList,
    )

    # Map results back using the ORIGINAL input names (by position),
    # not the AI-returned names which may have different Unicode/diacritics
    result = {}
    ai_patients = response.output_parsed.patients
    for i, name in enumerate(unknown_names):
        if i < len(ai_patients):
            result[name] = ai_patients[i].gender

    logger.info(f"OpenAI classified {len(result)} names")
    return result


def classify_genders(df: pd.DataFrame, gender_df: pd.DataFrame) -> pd.DataFrame:
    """Classify genders for all patients in the DataFrame.

    Args:
        df: DataFrame with column "_first_name" containing patient first names
        gender_df: DataFrame from CSV with known gender classifications

    Returns:
        pd.DataFrame: Input DataFrame with added "Gender" column

    Side effects:
        - Calls classify_from_csv for known names
        - Calls classify_from_ai for unknown names
        - Logs classification progress
    """
    first_names = df["_first_name"].unique().tolist()

    known = classify_from_csv(first_names, gender_df)

    unknown = [n for n in first_names if n not in known]

    ai_classified = {}
    if unknown:
        logger.info(f"Sending {len(unknown)} unknown names to OpenAI...")
        ai_classified = classify_from_ai(unknown)

    all_genders = {**known, **ai_classified}

    df["Gender"] = df["_first_name"].map(all_genders).fillna("")

    return df


def update_gender_csv(
    gender_df: pd.DataFrame, new_classifications: dict[str, str]
) -> pd.DataFrame:
    """Update the gender CSV with newly classified names.

    Args:
        gender_df: Existing DataFrame from CSV
        new_classifications: Dict of {name: gender} from AI classification

    Returns:
        pd.DataFrame: Updated DataFrame ready for upload

    Side effects:
        None (caller must upload to Drive)
    """
    if not new_classifications:
        return gender_df

    new_rows = pd.DataFrame(
        [
            {"Patient": name, "Gender": gender}
            for name, gender in new_classifications.items()
        ]
    )

    updated = pd.concat([gender_df, new_rows], ignore_index=True)

    updated = updated.drop_duplicates(subset=["Patient"], keep="last")

    updated = updated.sort_values("Patient").reset_index(drop=True)

    return updated

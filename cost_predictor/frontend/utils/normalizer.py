# =====================================================
# INPUT NORMALIZER
# Converts Hindi / Kannada user input to backend English
# =====================================================

def normalize_procedure(text: str) -> str:
    if not text:
        return ""

    t = text.strip().lower()

    mapping = {

        # -------------------------------------------------
        # KNEE SURGERY
        # -------------------------------------------------
        "knee surgery": "Knee Surgery",
        "घुटना सर्जरी": "Knee Surgery",
        "घुटने की सर्जरी": "Knee Surgery",
        "ಮೊಣಕಾಲು ಶಸ್ತ್ರಚಿಕಿತ್ಸೆ": "Knee Surgery",

        # -------------------------------------------------
        # HEART BYPASS
        # -------------------------------------------------
        "heart bypass": "Heart Bypass",
        "heart bypass surgery": "Heart Bypass",
        "हार्ट बायपास": "Heart Bypass",
        "हार्ट बायपास सर्जरी": "Heart Bypass",
        "ಹೃದಯ ಬೈಪಾಸ್": "Heart Bypass",

        # -------------------------------------------------
        # CATARACT
        # -------------------------------------------------
        "cataract surgery": "Cataract Surgery",
        "मोतियाबिंद सर्जरी": "Cataract Surgery",
        "ಮುತ್ತಿನಕಣ್ಣು ಶಸ್ತ್ರಚಿಕಿತ್ಸೆ": "Cataract Surgery",

        # -------------------------------------------------
        # DELIVERY
        # -------------------------------------------------
        "normal delivery": "Normal Delivery",
        "डिलीवरी": "Normal Delivery",
        "प्रसव": "Normal Delivery",
        "ಹೆರಿಗೆ": "Normal Delivery",

        # -------------------------------------------------
        # C SECTION
        # -------------------------------------------------
        "c section": "C Section",
        "cesarean": "C Section",
        "सी सेक्शन": "C Section",
        "ಸಿ ಸೆಕ್ಷನ್": "C Section",

        # -------------------------------------------------
        # APPENDIX
        # -------------------------------------------------
        "appendix surgery": "Appendix Surgery",
        "appendicitis surgery": "Appendix Surgery",
        "अपेंडिक्स सर्जरी": "Appendix Surgery",
        "ಅಪೆಂಡಿಕ್ಸ್ ಶಸ್ತ್ರಚಿಕಿತ್ಸೆ": "Appendix Surgery",

        # -------------------------------------------------
        # BOTOX
        # -------------------------------------------------
        "botox": "Botox",
        "बोटॉक्स": "Botox",
        "ಬೋಟಾಕ್ಸ್": "Botox",

        # -------------------------------------------------
        # GENERAL CHECKUP
        # -------------------------------------------------
        "checkup": "General Checkup",
        "general checkup": "General Checkup",
        "जांच": "General Checkup",
        "ತಪಾಸಣೆ": "General Checkup",
    }

    return mapping.get(t, text)


# =====================================================
# SPECIALTY NORMALIZER
# =====================================================

def normalize_specialty(text: str) -> str:

    if not text:
        return ""

    t = text.strip().lower()

    mapping = {

        "orthopedics": "Orthopedics",
        "हड्डी रोग": "Orthopedics",
        "ಎಲುಬು ವಿಭಾಗ": "Orthopedics",

        "cardiology": "Cardiology",
        "हृदय रोग": "Cardiology",
        "ಹೃದಯ ವಿಭಾಗ": "Cardiology",

        "ophthalmology": "Ophthalmology",
        "नेत्र रोग": "Ophthalmology",
        "ಕಣ್ಣು ವಿಭಾಗ": "Ophthalmology",

        "gynecology": "Gynecology",
        "स्त्री रोग": "Gynecology",
        "ಮಹಿಳಾ ವಿಭಾಗ": "Gynecology",

        "cosmetic": "Cosmetic",
        "कॉस्मेटिक": "Cosmetic",
        "ಕಾಸ್ಮೆಟಿಕ್": "Cosmetic",
    }

    return mapping.get(t, text)


# =====================================================
# DROPDOWN NORMALIZERS
# =====================================================

def normalize_city(text):

    mapping = {
        "Tier-1": "Tier-1",
        "Tier-2": "Tier-2",
        "Tier-3": "Tier-3",

        "स्तर-1": "Tier-1",
        "स्तर-2": "Tier-2",
        "स्तर-3": "Tier-3",

        "ಹಂತ-1": "Tier-1",
        "ಹಂತ-2": "Tier-2",
        "ಹಂತ-3": "Tier-3",
    }

    return mapping.get(text, "Tier-1")


def normalize_hospital(text):

    mapping = {
        "Private": "Private",
        "Government": "Government",

        "निजी": "Private",
        "सरकारी": "Government",

        "ಖಾಸಗಿ": "Private",
        "ಸರ್ಕಾರಿ": "Government"
    }

    return mapping.get(text, "Private")


def normalize_ward(text):

    mapping = {
        "general": "general",
        "semi-private": "semi-private",
        "private": "private",

        "जनरल": "general",
        "सेमी प्राइवेट": "semi-private",
        "प्राइवेट": "private",

        "ಜನರಲ್": "general",
        "ಸೆಮಿ ಪ್ರೈವೇಟ್": "semi-private",
        "ಪ್ರೈವೇಟ್": "private"
    }

    return mapping.get(text, "general")
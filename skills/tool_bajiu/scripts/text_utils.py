"""Shared text processing utilities: stemming, word matching, segmentation."""
import re


def stem(word: str) -> str:
    """Conservative English stemmer. Only strips high-confidence inflectional
    suffixes to avoid false positives. Minimum word length: 5 for most rules."""
    if len(word) < 5:
        return word

    w = word

    # -tion/-sion -> remove
    if w.endswith("tion") and len(w) > 6:
        return w[:-4]
    if w.endswith("sion") and len(w) > 6:
        return w[:-4]

    # -ment -> remove
    if w.endswith("ment") and len(w) > 6:
        return w[:-4]

    # -ness -> remove
    if w.endswith("ness") and len(w) > 6:
        return w[:-4]

    # -ing -> remove, handle doubled consonant (refactoring -> refactor)
    if w.endswith("ing") and len(w) > 5:
        base = w[:-3]
        if len(base) >= 3 and base[-1] == base[-2]:
            return base[:-1]
        if len(base) >= 3:
            return base

    # -ed -> remove, handle doubled consonant (refactored -> refactor)
    if w.endswith("ed") and len(w) > 4:
        base = w[:-2]
        if len(base) >= 3 and base[-1] == base[-2]:
            return base[:-1]
        if len(base) >= 3:
            return base

    # -ly -> remove (globally -> global)
    if w.endswith("ly") and len(w) > 4:
        return w[:-2]

    # -ies -> -y
    if w.endswith("ies") and len(w) > 5:
        return w[:-3] + "y"

    # -es -> remove
    if w.endswith("es") and len(w) > 4:
        return w[:-2]

    # -er -> remove (only if base >= 4)
    if w.endswith("er") and len(w) > 5:
        base = w[:-2]
        if len(base) >= 4:
            return base

    # -est -> remove
    if w.endswith("est") and len(w) > 5:
        base = w[:-3]
        if len(base) >= 4:
            return base

    # -able/-ible -> remove
    if w.endswith("able") and len(w) > 6:
        return w[:-4]
    if w.endswith("ible") and len(w) > 6:
        return w[:-4]

    # -ful -> remove
    if w.endswith("ful") and len(w) > 5:
        return w[:-3]

    # -ize/-ise -> remove
    if w.endswith("ize") and len(w) > 5:
        return w[:-3]
    if w.endswith("ise") and len(w) > 5:
        return w[:-3]

    return word


def _has_cjk(text: str) -> bool:
    """Check if text contains CJK characters."""
    return any("\u4e00" <= c <= "\u9fff" for c in text)


# Cross-language keyword mapping: English <-> Chinese
_EN_TO_ZH = {
    "fix": ["\u4fee\u590d", "\u4fee\u6b63"],
    "repair": ["\u4fee\u590d", "\u4fee\u7406"],
    "patch": ["\u8865\u4e01", "\u4fee\u590d"],
    "add": ["\u65b0\u589e", "\u6dfb\u52a0"],
    "create": ["\u521b\u5efa", "\u65b0\u5efa"],
    "implement": ["\u5b9e\u73b0", "\u5f00\u53d1"],
    "feature": ["\u529f\u80fd", "\u7279\u6027"],
    "refactor": ["\u91cd\u6784", "\u91cd\u5199"],
    "rewrite": ["\u91cd\u5199", "\u91cd\u6784"],
    "restructure": ["\u91cd\u7ec4", "\u91cd\u6784"],
    "delete": ["\u5220\u9664"],
    "remove": ["\u79fb\u9664", "\u5220\u9664"],
    "cleanup": ["\u6e05\u7406"],
    "deprecated": ["\u5e9f\u5f03", "\u8fc7\u65f6"],
    "global": ["\u5168\u5c40"],
    "entire": ["\u6574\u4e2a", "\u5168\u90e8"],
    "single": ["\u5355\u4e2a", "\u5355\u6587\u4ef6"],
}

_ZH_TO_EN = {}
for en, zh_list in _EN_TO_ZH.items():
    for zh in zh_list:
        if zh not in _ZH_TO_EN:
            _ZH_TO_EN[zh] = []
        _ZH_TO_EN[zh].append(en)


# Known compound technical term prefixes: keyword -> compound words it appears in
# Only these keywords get prefix matching to avoid false positives (e.g. "remove" != "removeDuplicates")
_COMPOUND_PREFIXES = {
    "none",      # NoneType, NoneError
    "null",      # NullPointerException, NullReferenceError
    "import",    # ImportError, ModuleNotFoundError
    "attribute", # AttributeError
    "typeerror", # (exact match is usually fine, but for safety)
    "index",     # IndexError
    "value",     # ValueError
    "key",       # KeyError
    "runtime",   # RuntimeError
    "overflow",  # OverflowError
    "assert",    # AssertionError
}


def _kw_matches_text(kw_lower: str, all_words: set, text: str) -> bool:
    """Core keyword-to-text matching logic used by word_match and score_keywords.
    - Multi-word keywords (e.g. "this file"): substring match in text
    - Hyphenated keywords (e.g. "multi-file"): split into parts, ALL must appear as words
    - Compound technical terms: prefix matching ONLY for known compound prefixes
    - Standard: exact word match, then stem match, then cross-language equivalent"""
    # Multi-word keyword: use substring matching (phrases need exact sequence)
    if " " in kw_lower:
        return kw_lower in text

    # Hyphenated keyword: require ALL parts present as words (stem-aware)
    if "-" in kw_lower:
        parts = kw_lower.split("-")
        return all(
            _kw_matches_text(p, all_words, text) for p in parts if p
        )

    # Exact word or stem match
    kw_stemmed = stem(kw_lower)
    if kw_lower in all_words or kw_stemmed in all_words:
        return True

    # Compound technical term prefix matching - ONLY for known prefixes
    if kw_lower in _COMPOUND_PREFIXES:
        for w in all_words:
            if w.startswith(kw_lower) and len(w) > len(kw_lower):
                return True

    # Cross-language equivalent
    zh_equivalents = _EN_TO_ZH.get(kw_lower, [])
    for zh_kw in zh_equivalents:
        if zh_kw in text:
            return True

    return False


def word_match(text: str, keywords: list) -> bool:
    """Match keywords against text with stemming, substring, and cross-language awareness.
    - English keywords: word-boundary + stemming, compound word prefix matching, cross-language
    - Chinese keywords: substring match, also check English equivalents
    - Hyphenated keywords (e.g. "multi-file"): ALL parts must appear as words
    - Multi-word phrases (e.g. "this file"): substring match in text
    Prevents false positives (additive !~ add) while catching inflected forms and compounds."""
    text_lower = text.lower()
    text_words = re.findall(r'[a-z]+', text_lower)
    stemmed_set = {stem(w) for w in text_words}
    all_words = stemmed_set | set(text_words)

    for kw in keywords:
        kw_lower = kw.lower()

        if _has_cjk(kw):
            if kw in text:
                return True
            en_equivalents = _ZH_TO_EN.get(kw, [])
            for en_kw in en_equivalents:
                if _kw_matches_text(en_kw.lower(), all_words, text_lower):
                    return True
        else:
            if _kw_matches_text(kw_lower, all_words, text_lower):
                return True
    return False


def score_keywords(text: str, weighted_keywords: dict) -> float:
    """Score text against weighted keywords. Returns 0.0-1.0.
    weighted_keywords: {keyword: weight} dict.
    Score = sum(matched_weights) / sum(all_weights), capped at 1.0.
    Supports hyphenated keywords, compound word prefix matching, and cross-language."""
    if not weighted_keywords:
        return 0.5

    text_lower = text.lower()
    text_words = re.findall(r'[a-z]+', text_lower)
    stemmed_set = {stem(w) for w in text_words}
    all_words = stemmed_set | set(text_words)

    total_weight = sum(weighted_keywords.values())
    matched_weight = 0.0

    for kw, weight in weighted_keywords.items():
        kw_lower = kw.lower()

        if _has_cjk(kw):
            if kw in text:
                matched_weight += weight
                continue
            matched = False
            for en_kw in _ZH_TO_EN.get(kw, []):
                if _kw_matches_text(en_kw.lower(), all_words, text_lower):
                    matched = True
                    break
            if matched:
                matched_weight += weight
        else:
            if _kw_matches_text(kw_lower, all_words, text_lower):
                matched_weight += weight

    if total_weight == 0:
        return 0.5
    return min(matched_weight / total_weight, 1.0)

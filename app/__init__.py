"""SH Ads Desk — full self-hostable build.

Labels used across the whole system (brief rule):
- MOCK     — fake data/client standing in for Meta (the default mode).
- UNTESTED — code-complete but never exercised against a real Meta account.
- VERIFIED — exercised by the local test suite (see TEST_RESULTS.md).
"""

__version__ = "1.1.0"
BUILD_LABEL = ("Full build + API Providers — Step 1 logic VERIFIED locally; "
               "live Meta path aur provider adapters UNTESTED")

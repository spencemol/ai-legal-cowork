"""Legal database search stub (task 7.2).

Provides a ``LegalDBSearchTool`` interface that mirrors what a real
Westlaw / LexisNexis integration would expose.  For v1, it returns a pool
of hardcoded mock case-law results shaped exactly like real API responses.
The stub is ready for real integration: replace ``_MOCK_RESULTS`` with
live API calls without changing the public interface.
"""

from __future__ import annotations

_MOCK_RESULTS: list[dict] = [
    {
        "title": "Smith v. Jones",
        "citation": "123 F.3d 456 (9th Cir. 2020)",
        "snippet": (
            "The court held that breach of contract requires: (1) a valid contract, "
            "(2) plaintiff's performance, (3) defendant's breach, and "
            "(4) resulting damages."
        ),
        "source": "westlaw",
        "url": "https://westlaw.example.com/smith-v-jones",
    },
    {
        "title": "Doe v. Roe",
        "citation": "456 F.2d 789 (2d Cir. 2019)",
        "snippet": (
            "Expectation damages in breach of contract cases aim to put the "
            "non-breaching party in the position they would have occupied "
            "had the contract been performed."
        ),
        "source": "lexisnexis",
        "url": "https://lexisnexis.example.com/doe-v-roe",
    },
    {
        "title": "ABC Corp v. XYZ Inc",
        "citation": "789 F. Supp. 2d 101 (S.D.N.Y. 2021)",
        "snippet": (
            "The implied covenant of good faith and fair dealing is present in "
            "every contract and requires that neither party do anything to "
            "deprive the other of the benefits of the agreement."
        ),
        "source": "westlaw",
        "url": "https://westlaw.example.com/abc-v-xyz",
    },
    {
        "title": "Johnson v. Williams",
        "citation": "321 F.3d 654 (5th Cir. 2022)",
        "snippet": (
            "A party seeking to avoid its contractual obligations on grounds "
            "of impossibility must show that performance is objectively "
            "impossible, not merely more difficult or expensive."
        ),
        "source": "lexisnexis",
        "url": "https://lexisnexis.example.com/johnson-v-williams",
    },
    {
        "title": "Taylor v. Anderson",
        "citation": "567 F.2d 890 (7th Cir. 2018)",
        "snippet": (
            "The statute of frauds requires that certain categories of contracts, "
            "including those for the sale of goods over $500, be in writing "
            "and signed by the party to be charged."
        ),
        "source": "westlaw",
        "url": "https://westlaw.example.com/taylor-v-anderson",
    },
]


class LegalDBSearchTool:
    """Stub for Westlaw/LexisNexis legal database search.

    Returns mock case-law results shaped like real API responses.
    The interface is ready for live integration without changes to
    calling code.

    Parameters
    ----------
    default_max_results:
        Default number of results to return.
    """

    def __init__(self, default_max_results: int = 5) -> None:
        self.default_max_results = default_max_results

    def search(self, query: str, max_results: int | None = None) -> list[dict]:
        """Search the legal database and return case-law results.

        Parameters
        ----------
        query:
            Legal research query string.
        max_results:
            Maximum number of results.  Defaults to ``self.default_max_results``.

        Returns
        -------
        list[dict]
            Each item has ``title``, ``citation``, ``snippet``, ``source``,
            and ``url`` keys.  ``source`` is ``"westlaw"`` or ``"lexisnexis"``.
        """
        n = max_results if max_results is not None else self.default_max_results
        return _MOCK_RESULTS[:n]

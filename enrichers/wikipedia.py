from enrichers import Enrichment
from urllib.parse import quote
from utils import logger


class Wikipedia(Enrichment):
    static_search: str = "https://en.wikipedia.org/wiki/"
    api_search: str = "https://en.wikipedia.org/w/api.php"
    facility_terms: list = [
        "detention",
        "prison",
        "jail",
        "correctional",
        "penitentiary",
        "facility",
        "center",
        "complex",
        "institution",
        "processing",
    ]

    def search(self) -> dict:
        """Search Wikipedia for facility and return final URL after redirects"""
        self.resp_info["enrichment_type"] = "wikipedia"
        facility_name = self.search_args["facility_name"]
        # Clean facility name for search
        search_name: str = self._clean_facility_name(facility_name)
        logger.debug("Searching Wikipedia for %s", facility_name)
        # Try direct page access first (replace space with underscores is the only change)
        wiki_url = f"{self.static_search}{quote(facility_name.replace(' ', '_').replace('|', '_'))}"
        self.resp_info["search_query_steps"].append(wiki_url)  # type: ignore [attr-defined]
        initial_response = False
        try:
            response = self._req(wiki_url)
            initial_response = True
        except Exception as e:
            logger.debug("  Wikipedia search error for '%s': %s", wiki_url, e)
            self.resp_info["search_query_steps"].append(f"(Failed -> {e})")  # type: ignore [attr-defined]
            wiki_url = f"{self.static_search}{quote(facility_name.replace(' ', '_').replace('|', '_'))}"
            self.resp_info["search_query_steps"].append(wiki_url)  # type: ignore [attr-defined]
            try:
                response = self._req(wiki_url)
                initial_response = True
            except Exception as e:
                logger.debug("  Wikipedia search error for '%s': %s", wiki_url, e)
                self.resp_info["search_query_steps"].append(f"(Failed -> {e})")  # type: ignore [attr-defined]

        if initial_response:
            # Check if we got a real article (not a disambiguation or search page)
            page_text = response.text.lower()

            # Enhanced false positive detection
            false_positive_indicators = [
                "may refer to:",  # Disambiguation page
                "did you mean",  # Search suggestion
                "disambiguation)",  # Disambiguation in title
                "is a disambiguation",  # Disambiguation description
                "this article is about",  # Generic topic page
                "for other uses",  # Disambiguation header
            ]

            # Additional check: ensure result is actually about a detention facility
            is_false_positive = any(indicator in page_text for indicator in false_positive_indicators)
            has_facility_context = any(indicator in page_text for indicator in self.facility_terms)

            # Only accept if it's not a false positive AND has facility context
            # OR if the cleaned name still contains facility-related terms
            facility_terms_in_name = any(term in search_name.lower() for term in self.facility_terms)

            if not is_false_positive and (has_facility_context or facility_terms_in_name):
                self.resp_info["url"] = response.url
                self.resp_info["method"] = "direct_access"
                return self.resp_info
            else:
                self.resp_info["search_query_steps"].append("[REJECTED: false_positive or no_facility_context]")  # type: ignore [attr-defined]

        logger.debug("  Falling back to Wikipedia API searches for %s and %s", facility_name, search_name)
        # If direct access fails, try Wikipedia search API with original name first
        search_queries = [
            facility_name,  # Original full name
            search_name,  # Cleaned name
        ]

        # Add variations if the name contains common facility types
        if any(term in facility_name.lower() for term in ["county", "parish"]):
            # For county facilities, try with facility type intact
            minimal_clean = self._minimal_clean_facility_name(facility_name)
            if minimal_clean != search_name:
                search_queries.append(minimal_clean)

        for query_attempt, search_query in enumerate(search_queries):
            self.resp_info["search_query_steps"].append(search_query)  # type: ignore [attr-defined]

            params = {
                "action": "query",
                "list": "search",
                "srsearch": search_query,
                "format": "json",
                "srlimit": 5,
            }

            try:
                response = self._req(self.api_search, params=params)
                data = response.json()
            except Exception as e:
                logger.debug("   Wikipedia search for %s failed: %s", self.api_search, e)
                self.resp_info["search_query_steps"].append(f"(Failed: {search_query} -> {e})")  # type: ignore [attr-defined]
                continue

            if data.get("query", {}).get("search"):
                # Examine each result for relevance
                # Arbitrary but sort of useful.
                for result in data["query"]["search"]:
                    page_title = result["title"]
                    snippet = result.get("snippet", "").lower()

                    # Enhanced relevance scoring
                    relevance_score = 0

                    # Check if title contains facility-related terms
                    title_lower = page_title.lower()

                    for term in self.facility_terms:
                        if term in title_lower:
                            relevance_score += 2

                    # Check if snippet mentions detention/prison context
                    detention_context = [
                        "detention",
                        "prison",
                        "jail",
                        "correctional",
                        "inmates",
                        "custody",
                        "incarceration",
                        "processing",
                    ]
                    for term in detention_context:
                        if term in snippet:
                            relevance_score += 1

                    # Penalize generic location pages without facility context
                    generic_indicators = ["county", "city", "town", "village", "township"]
                    if any(term in title_lower for term in generic_indicators) and not any(
                        term in title_lower for term in self.facility_terms
                    ):
                        relevance_score -= 3

                    # Check name similarity (basic heuristic)
                    original_tokens = set(facility_name.lower().split())
                    title_tokens = set(page_title.lower().split())
                    common_tokens = original_tokens.intersection(title_tokens)

                    if len(common_tokens) >= 2:
                        relevance_score += len(common_tokens)

                    # Only accept results with positive relevance score
                    if relevance_score > 0:
                        final_url = f"{self.static_search}{quote(page_title.replace(' ', '_'))}"

                        # Verify the page exists and isn't a redirect to something unrelated
                        try:
                            verify_response = self._req(final_url)
                        except Exception as e:
                            logger.debug("    Wikipedia query for %s failed: %s", final_url, e)
                            self.resp_info["search_query_steps"].append(final_url)  # type: ignore [attr-defined]
                        else:
                            self.resp_info["url"] = verify_response.url
                            self.resp_info["method"] = f"api_search_attempt_{query_attempt + 1}_score_{relevance_score}"
                            self.resp_info["search_query_steps"].append(f"-> {page_title} (score: {relevance_score})")  # type: ignore [attr-defined]
                            return self.resp_info

            # If this search query didn't work, try the next one
            if query_attempt < len(search_queries) - 1:
                self.resp_info["search_query_steps"].append("[no_relevant_results] ->")  # type: ignore [attr-defined]

        # No results found
        self.resp_info["search_query_steps"].append("[no_results_found]")  # type: ignore [attr-defined]
        self.resp_info["method"] = "failed"

        return self.resp_info

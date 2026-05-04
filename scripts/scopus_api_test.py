import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_KEY = "	e6a7ee701cf06a5ff538fbaa0ebbd778"
QUERY = "TITLE-ABS-KEY(econometrics)"
COUNT = 3


def build_url():
    params = {
        "query": QUERY,
        "count": COUNT,
    }
    return "https://api.elsevier.com/content/search/scopus?" + urlencode(params)


def main():
    if API_KEY == "PASTE_YOUR_SCOPUS_API_KEY_HERE":
        print("Please paste your Scopus API key into API_KEY first.")
        sys.exit(1)

    url = build_url()
    headers = {
        "X-ELS-APIKey": API_KEY,
        "Accept": "application/json",
    }
    request = Request(url, headers=headers)

    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP error: {exc.code}")
        print(body)
        sys.exit(1)
    except URLError as exc:
        print("Network error:")
        print(exc)
        sys.exit(1)

    search_results = payload.get("search-results", {})
    entries = search_results.get("entry", [])

    print("Scopus API call succeeded.")
    print(f"Results returned: {len(entries)}")
    print("-" * 60)

    for index, item in enumerate(entries, start=1):
        title = item.get("dc:title", "-")
        authors = item.get("dc:creator", "-")
        journal = item.get("prism:publicationName", "-")
        year = item.get("prism:coverDate", "-")
        eid = item.get("eid", "-")

        print(f"{index}. {title}")
        print(f"   Authors: {authors}")
        print(f"   Journal: {journal}")
        print(f"   Date: {year}")
        print(f"   EID: {eid}")
        print()


if __name__ == "__main__":
    main()

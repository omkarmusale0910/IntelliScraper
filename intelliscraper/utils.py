from urllib.parse import urljoin, urldefrag

def normalize_links(base_url: str, links: list[str]) -> list[str]:
    """
    Convert relative links to absolute URLs, remove fragments, and remove duplicates.
    
    Args:
        base_url (str): The base URL to resolve relative links.
        links (list[str]): List of links (absolute or relative).

    Returns:
        list[str]: List of unique, absolute URLs.
    """
    normalized = [urldefrag(urljoin(base_url, link))[0] for link in links]

    seen = set()
    result = []
    for link in normalized:
        if link not in seen:
            seen.add(link)
            result.append(link)

    return result

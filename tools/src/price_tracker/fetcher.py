from datetime import date

import httpx

from price_tracker.models import BalfourProject, PriceFetchStatus


def fetch_prices(project: BalfourProject) -> dict:
    results = {"checked": 0, "success": 0, "broken": 0, "unavailable": 0}
    today = date.today().isoformat()

    for supplier in project.suppliers:
        for sel in supplier.selections:
            if not sel.product_url:
                continue

            results["checked"] += 1
            try:
                with httpx.Client(timeout=15, follow_redirects=True) as client:
                    resp = client.head(sel.product_url)

                if resp.status_code == 404:
                    sel.price_fetch_status = PriceFetchStatus.PRODUCT_UNAVAILABLE
                    sel.price_validated_date = today
                    results["unavailable"] += 1
                elif resp.status_code >= 400:
                    sel.price_fetch_status = PriceFetchStatus.FETCH_ERROR
                    sel.price_validated_date = today
                    results["broken"] += 1
                else:
                    sel.price_fetch_status = PriceFetchStatus.SUCCESS
                    sel.price_validated_date = today
                    results["success"] += 1

            except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError):
                sel.price_fetch_status = PriceFetchStatus.LINK_BROKEN
                sel.price_validated_date = today
                results["broken"] += 1

    return results


def validate_urls(project: BalfourProject) -> dict:
    results = {"total": 0, "reachable": 0, "unreachable": 0}

    for supplier in project.suppliers:
        for sel in supplier.selections:
            if not sel.product_url:
                continue

            results["total"] += 1
            try:
                with httpx.Client(timeout=15, follow_redirects=True) as client:
                    resp = client.head(sel.product_url)
                if resp.status_code < 400:
                    results["reachable"] += 1
                else:
                    results["unreachable"] += 1
            except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError):
                results["unreachable"] += 1

    return results

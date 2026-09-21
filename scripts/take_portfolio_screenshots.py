"""
Generate portfolio screenshots for Pi Market using Playwright (headless Chromium).

Usage:
    python3 scripts/take_portfolio_screenshots.py

Output: docs/portfolio/*.png + README.md
Requires: pip install playwright && playwright install chromium

The script starts its own Django server on 127.0.0.1:8777 (migrate + seed),
performs the real user journey, then stops the server.
"""
import json
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
import http.cookiejar
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = BASE_DIR / "docs" / "portfolio"

PORT = 8777
BASE = f"http://127.0.0.1:{PORT}"

SERVER_ENV = {
    "DJANGO_SUPERUSER_PHONE": "+221000000000",
    "DJANGO_SUPERUSER_PASSWORD": "demo1234",
}
ADMIN_PHONE = "+221000000000"
ADMIN_PASS = "demo1234"

BUYER_PHONE = "+221770112233"
BUYER_NAME = "Fatou Ndiaye"
BUYER_ADDRESS = "Dakar Plateau, Rue Jules Ferry 12, Dakar 18524"

CART_SEED = [
    {"productId": "1", "quantity": 1, "title": "Wireless Headphones",
     "price_fiat": 79.99, "price_pi": 112.0,
     "image": "/media/products/wireless-headphones.png"},
    {"productId": "2", "quantity": 1, "title": "Smart Watch",
     "price_fiat": 129.0, "price_pi": 180.6,
     "image": "/media/products/smart-watch.png"},
]


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

def start_server():
    env = {**dict(__import__("os").environ), **SERVER_ENV}
    proc = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", f"127.0.0.1:{PORT}", "--noreload"],
        cwd=str(BASE_DIR), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    for _ in range(50):
        try:
            urllib.request.urlopen(f"{BASE}/products/", timeout=2)
            print("✓ Server ready")
            return proc
        except Exception:
            time.sleep(0.5)
    proc.terminate()
    out = proc.stdout.read().decode(errors="replace")
    raise RuntimeError(f"Server did not start:\n{out[-2000:]}")


def stop_server(proc):
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def login_token():
    """Register-or-login via API (idempotent get_or_create) using urllib."""
    req = urllib.request.Request(
        f"{BASE}/api/accounts/register/",
        data=json.dumps({"phone_number": BUYER_PHONE,
                         "display_name": BUYER_NAME}).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
        return data["access"], data.get("refresh", "")
    except urllib.error.HTTPError as e:
        # Already registered → fall back to login
        if e.code == 400:
            req2 = urllib.request.Request(
                f"{BASE}/api/accounts/login/",
                data=json.dumps({"phone_number": BUYER_PHONE}).encode(),
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(req2, timeout=10) as r:
                data = json.loads(r.read().decode())
            return data["access"], data.get("refresh", "")
        raise


def add_toast(page, kind, msg):
    page.evaluate("([t, m]) => showToast(t, m)", [kind, msg])
    page.wait_for_timeout(400)


def shot(page, path, full=False, clip=None):
    page.screenshot(path=str(OUT_DIR / path), full_page=full, clip=clip)
    print(f"  → {path}")


def seed_cart(page):
    page.evaluate("(items) => localStorage.setItem('cart', JSON.stringify(items))", CART_SEED)
    page.evaluate("() => localStorage.setItem('cartCount', String(JSON.parse(localStorage.getItem('cart')).length))")


# ---------------------------------------------------------------------------
# Capture journey
# ---------------------------------------------------------------------------

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    proc = start_server()
    access, refresh = login_token()
    print("✓ Logged in via API (JWT)")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()

            # ---------- Public context ----------
            ctx = browser.new_context(
                viewport={"width": 1440, "height": 900},
                device_scale_factor=2,
                locale="fr-FR",
                timezone_id="Africa/Dakar",
            )
            page = ctx.new_page()
            # Inject JWT before any page script runs → authenticated session everywhere
            ctx.add_init_script(
                "localStorage.setItem('access_token', %s);"
                "localStorage.setItem('refresh_token', %s);"
                % (json.dumps(access), json.dumps(refresh))
            )

            # 1. Home
            print("Home…")
            page.goto(f"{BASE}/", wait_until="networkidle")
            page.evaluate("() => localStorage.removeItem('cart')")
            add_toast(page, "success", "Bienvenue sur Pi Market ! 🎉")
            page.wait_for_timeout(300)
            shot(page, "01_home_hero.png")
            shot(page, "02_home_full.png", full=True)

            # 2. Catalog
            print("Catalog…")
            page.goto(f"{BASE}/products/", wait_until="networkidle")
            add_toast(page, "info", "6 produits disponibles")
            shot(page, "03_product_list.png", full=True)

            # 3. Product detail
            print("Product detail…")
            page.goto(f"{BASE}/products/1/", wait_until="networkidle")
            add_toast(page, "success", "Wireless Headphones ajouté au panier !")
            shot(page, "04_product_detail.png", full=True)

            # 4. Cart
            print("Cart…")
            seed_cart(page)
            page.goto(f"{BASE}/cart/", wait_until="networkidle")
            add_toast(page, "info", "2 articles dans votre panier")
            shot(page, "05_cart.png", full=True)

            # 5. Checkout
            print("Checkout…")
            page.goto(f"{BASE}/checkout/", wait_until="networkidle")
            page.fill("#shipping_address", BUYER_ADDRESS)
            add_toast(page, "info", "Paiement sécurisé via Pi Network 🔒")
            page.wait_for_timeout(300)
            shot(page, "06_checkout.png", full=True)

            # 6. Real order + demo payment → escrow
            print("Order + escrow…")
            result = page.evaluate(
                """async ([addr]) => {
                    const token = localStorage.getItem('access_token');
                    const items = JSON.parse(localStorage.getItem('cart'))
                        .map(c => ({product_id: c.productId, quantity: c.quantity}));
                    const headers = {'Content-Type': 'application/json',
                                     'Authorization': 'Bearer ' + token};
                    const r1 = await fetch('/api/shops/orders/create/', {
                        method: 'POST', headers,
                        body: JSON.stringify({items: items, currency: 'pi',
                                              shipping_address: addr, notes: 'Livraison à Dakar'})
                    });
                    const o = await r1.json();
                    if (!r1.ok) return {error: 'order', body: o};
                    const r2 = await fetch('/api/payments/create/' + o.order.id + '/',
                                           {method: 'POST', headers});
                    const pay = await r2.json();
                    if (!r2.ok) return {error: 'payment', body: pay};
                    return {orderId: o.order.id, orderNumber: o.order.order_number};
                }""",
                [BUYER_ADDRESS],
            )
            if "error" in result:
                raise RuntimeError(f"Order flow failed: {result}")
            print(f"  Order {result['orderNumber']} paid in escrow")
            page.goto(f"{BASE}/orders/{result['orderId']}/", wait_until="networkidle")
            add_toast(page, "success", "Paiement effectué — fonds sécurisés en escrow 🔒")
            page.wait_for_timeout(500)
            shot(page, "07_order_detail.png", full=True)

            # 7. Dashboards (same session)
            print("Dashboards…")
            page.goto(f"{BASE}/account/", wait_until="networkidle")
            shot(page, "08_account_dashboard.png", full=True)
            page.goto(f"{BASE}/dashboard/buyer/", wait_until="networkidle")
            shot(page, "09_buyer_dashboard.png", full=True)

            ctx.close()

            # 8. Auth pages (anonymous)
            ctx2 = browser.new_context(
                viewport={"width": 1440, "height": 900},
                device_scale_factor=2, locale="fr-FR",
            )
            p2 = ctx2.new_page()
            print("Auth pages…")
            p2.goto(f"{BASE}/auth/login/", wait_until="networkidle")
            shot(p2, "10_auth_login.png")
            p2.goto(f"{BASE}/auth/register/", wait_until="networkidle")
            shot(p2, "11_auth_register.png")

            # 9. Messaging (if page exists)
            print("Messaging…")
            resp = p2.goto(f"{BASE}/messenger/", wait_until="domcontentloaded")
            if resp and resp.status != 404:
                p2.wait_for_timeout(1200)
                shot(p2, "12_messaging.png", full=True)
            else:
                print("  (no /messenger/ page — skipped)")

            ctx2.close()

            # 10. Admin (real Django session login)
            print("Admin…")
            ctx3 = browser.new_context(
                viewport={"width": 1440, "height": 900},
                device_scale_factor=2,
                locale="fr-FR",
            )
            p3 = ctx3.new_page()
            try:
                p3.goto(f"{BASE}/admin/login/", wait_until="networkidle")
                p3.fill("#id_username", ADMIN_PHONE)
                p3.fill("#id_password", ADMIN_PASS)
                p3.click("input[type='submit']")
                p3.goto(f"{BASE}/admin/shops/order/", wait_until="networkidle", timeout=20000)
                p3.wait_for_selector("#result_list", timeout=10000)
                shot(p3, "13_admin_orders.png", full=True)
            except Exception as e:
                print(f"  (admin capture skipped: {e})")
            ctx3.close()
            browser.close()
    finally:
        stop_server(proc)

    # index README
    lines = ["# Captures d'écran — Pi Market", "",
             "Générées automatiquement par `scripts/take_portfolio_screenshots.py`.",
             "Parcours réel : login JWT → catalogue → panier → checkout → commande payée en escrow.", ""]
    names = {
        "01_home_hero.png": "Page d'accueil (hero) — visuel principal",
        "02_home_full.png": "Page d'accueil complète (catégories, comment ça marche, escrow)",
        "03_product_list.png": "Catalogue produits avec images",
        "04_product_detail.png": "Fiche produit (galerie, quantité, ajout panier)",
        "05_cart.png": "Panier (localStorage, quantités, totaux)",
        "06_checkout.png": "Checkout (adresse, choix fiat/Pi)",
        "07_order_detail.png": "Commande payée — statut escrow",
        "08_account_dashboard.png": "Dashboard post-login",
        "09_buyer_dashboard.png": "Dashboard acheteur",
        "10_auth_login.png": "Connexion téléphone",
        "11_auth_register.png": "Inscription",
        "12_messaging.png": "Messagerie",
        "13_admin_orders.png": "Admin Django — commandes & escrow",
    }
    for f in sorted(OUT_DIR.glob("*.png")):
        lines.append(f"- `{f.name}` — {names.get(f.name, '')}")
    (OUT_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n✓ Done:", OUT_DIR)


if __name__ == "__main__":
    main()

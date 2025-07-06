import logging
import os
import secrets
import signal
import sys
import threading
import time
import webview
from flask import Flask, flash, redirect, render_template, url_for, request
from sqlite3 import IntegrityError
from lib.app.utils import register_entity_routes
from lib.db import utils, customer, purchase, sale, supplier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)


@app.route("/")
def index():
    return render_template("index.html")


register_entity_routes(
    entity_name="suppliers",
    template_name="suppliers.html",
    repo_class=supplier.SupplierRepository,
    app=app,
)

register_entity_routes(
    entity_name="customers",
    template_name="customers.html",
    repo_class=customer.CustomerRepository,
    app=app,
)


@app.route("/sales", methods=["GET"])
def sales():
    repo = sale.SaleRepository()
    filters = {
        "customer": request.args.get("customer", "").strip(),
        "invoice": request.args.get("invoice", "").strip(),
        "net": {},
        "vat": [],
        "payment": [],
        "timeFrom": request.args.get("timeFrom", "").strip(),
        "timeTo": request.args.get("timeTo", "").strip(),
    }

    net_min = request.args.get("net_min")
    net_max = request.args.get("net_max")
    net_eq = request.args.get("net_eq")

    if net_eq:
        filters["net"]["eq"] = float(net_eq)
    else:
        if net_min:
            filters["net"]["min"] = float(net_min)
        if net_max:
            filters["net"]["max"] = float(net_max)

    vat_values = request.args.getlist("vat")
    payment_values = request.args.getlist("payment")
    if vat_values:
        filters["vat"] = [float(v) for v in vat_values if v]
    if payment_values:
        filters["payment"] = [p for p in payment_values if p]

    all_sales = repo.all()
    vat_options = sorted(set(s.vat_percent for s in all_sales))
    payment_options = sorted(set(s.payment_method for s in all_sales))

    sales = repo.search(filters) if any(filters.values()) else repo.all()
    return render_template(
        "sales.html",
        filters=filters,
        sales=sales,
        payment_options=payment_options,
        vat_options=vat_options,
    )


@app.route("/sales/create", methods=["GET", "POST"])
def create_sale():
    repo = sale.SaleRepository()
    customer_repo = customer.CustomerRepository()
    customers = customer_repo.all()
    render = render_template("create_sale.html", customers=customers)

    if request.method == "POST":
        try:
            customer_name = request.form.get("customer_name")
            customer_obj = next(
                (c for c in customers if c.name == customer_name), None
            )
            if not customer_obj:
                flash("Invalid customer selected", "error")
                return redirect("/purchases")

            new_sale = sale.Sale(
                id=None,
                customer_id=customer_obj.id,
                customer_name=customer_obj.name,
                invoice_number=request.form["invoice_number"],
                net_amount=float(request.form["net_amount"]),
                vat_percent=float(request.form["vat_percent"]),
                payment_method=request.form["payment_method"],
                timestamp=request.form["timestamp"],
            )
            repo.create(new_sale)
            flash("Sale created successfully.", "success")
            return redirect("/sales/create")
        except IntegrityError as err:
            logger.warning(err)
            flash(f"Unexpected Error: {str(err)}", "error")

    return render


@app.route("/purchases", methods=["GET"])
def purchases():
    repo = purchase.PurchaseRepository()
    filters = {
        "supplier": request.args.get("supplier", "").strip(),
        "supplier_invoice": request.args.get("supplier_invoice", "").strip(),
        "internal_invoice": request.args.get("internal_invoice", "").strip(),
        "net": {},
        "goods": {},
        "utilities": {},
        "motor_expenses": {},
        "sundries": {},
        "miscellaneous": {},
        "vat": [],
        "payment": [],
        "capital_spend": request.args.get("capital_spend", "").strip(),
        "timeFrom": request.args.get("timeFrom", "").strip(),
        "timeTo": request.args.get("timeTo", "").strip(),
    }

    def parse_range(prefix):
        result = {}
        min_val = request.args.get(f"{prefix}_min")
        max_val = request.args.get(f"{prefix}_max")
        eq_val = request.args.get(f"{prefix}_eq")
        if eq_val:
            result["eq"] = float(eq_val)
        else:
            if min_val:
                result["min"] = float(min_val)
            if max_val:
                result["max"] = float(max_val)
        return result

    filters["net"] = parse_range("net")
    filters["goods"] = parse_range("goods")
    filters["utilities"] = parse_range("utilities")
    filters["motor_expenses"] = parse_range("motor_expenses")
    filters["sundries"] = parse_range("sundries")
    filters["miscellaneous"] = parse_range("miscellaneous")
    vat_values = request.args.getlist("vat")
    payment_values = request.args.getlist("payment")
    if vat_values:
        filters["vat"] = [float(v) for v in vat_values if v]
    if payment_values:
        filters["payment"] = [p for p in payment_values if p]

    all_purchases = repo.all()
    vat_options = sorted(set(p.vat_percent for p in all_purchases))
    payment_options = sorted(set(p.payment_method for p in all_purchases))
    purchases = (
        repo.search(filters) if any(filters.values()) else all_purchases
    )

    return render_template(
        "purchases.html",
        filters=filters,
        purchases=purchases,
        vat_options=vat_options,
        payment_options=payment_options,
    )


@app.route("/purchases/create", methods=["GET", "POST"])
def create_purchase():
    repo = purchase.PurchaseRepository()
    suppliers = supplier.SupplierRepository().all()

    if request.method == "POST":
        supplier_name = request.form.get("supplier_name")
        supplier_obj = next(
            (s for s in suppliers if s.name == supplier_name), None
        )
        if not supplier_obj:
            flash("Invalid supplier selected", "error")
            return redirect("/purchases")

        timestamp = request.form["timestamp"]
        new_purchase = purchase.Purchase(
            id=None,
            supplier_id=supplier_obj.id,
            supplier_name=supplier_obj.name,
            supplier_invoice_code=request.form.get("supplier_invoice_code"),
            internal_invoice_number=request.form.get(
                "internal_invoice_number"
            ),
            net_amount=float(request.form.get("net_amount")),
            vat_percent=float(request.form.get("vat_percent")),
            goods=float(request.form.get("goods")),
            utilities=float(request.form.get("utilities")),
            motor_expenses=float(request.form.get("motor_expenses")),
            sundries=float(request.form.get("sundries")),
            miscellaneous=float(request.form.get("miscellaneous")),
            payment_method=request.form.get("payment_method"),
            timestamp=timestamp,
            capital_spend=bool(request.form.get("capital_spend")),
        )

        try:
            repo.create(new_purchase)
            flash("Purchase created successfully.", "success")
        except IntegrityError as err:
            logger.warning(err)
            flash(f"Unexpected Error: {str(err)}", "error")

        return redirect("/purchases")

    return render_template("create_purchase.html", suppliers=suppliers)


def run_flask(debug=False):
    app.run(port=1304, debug=debug)


def main():
    debug_mode = len(sys.argv) > 1 and sys.argv[1] == "debug"

    if debug_mode:
        run_flask(debug=True)  # allows reloader, runs in main thread
    else:
        flask_thread = threading.Thread(
            target=run_flask, kwargs={"debug": False}, daemon=True
        )
        flask_thread.start()

        # Give Flask a moment to start
        time.sleep(1)

        # Launch embedded browser window
        window = webview.create_window(
            "Bookkeeppr", "http://localhost:1304", width=1000, height=700
        )

        try:
            webview.start()
        finally:
            print("[APP] Window closed, exiting...")
            sys.exit(0)


if __name__ == "__main__":
    main()

import logging
import os
import secrets
import signal
import sys
import threading
import time
import webview
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    send_file,
    send_from_directory,
    url_for,
    request,
)
from flask_apscheduler import APScheduler
from io import BytesIO
from sqlite3 import IntegrityError
from lib.app.utils import (
    SchedulerConfig,
    register_entity_routes,
    register_transaction_routes,
    open_export_file_picker,
    export_to_xlsx,
)
from lib.db import utils, customer, purchase, sale, supplier

log_path = utils.get_app_data_folder_path() / ".bookkeeppr.log"
log_path.parent.mkdir(parents=True, exist_ok=True)
filehandler = logging.FileHandler(log_path, encoding="utf-8")
filehandler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
)
filehandler.setLevel(logging.INFO)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(filehandler)

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config.from_object(SchedulerConfig())

# Start scheduler
scheduler = APScheduler()
scheduler.init_app(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "assets"),
        "bookkeeppr.ico",
        mimetype="image/vnd.microsoft.icon",
    )


register_entity_routes(
    entity_name="suppliers",
    template_name="suppliers.html",
    model_class=supplier.Supplier,
    repo_class=supplier.SupplierRepository,
    app=app,
)

register_entity_routes(
    entity_name="customers",
    template_name="customers.html",
    model_class=customer.Customer,
    repo_class=customer.CustomerRepository,
    app=app,
)


register_transaction_routes(
    transaction_name="sales",
    template_name="sales.html",
    model_class=sale.Sale,
    repo_class=sale.SaleRepository,
    entity_repo_class=customer.CustomerRepository,
    entity_class_name="Customer",
    app=app,
)

register_transaction_routes(
    transaction_name="purchases",
    template_name="purchases.html",
    model_class=purchase.Purchase,
    repo_class=purchase.PurchaseRepository,
    entity_repo_class=supplier.SupplierRepository,
    entity_class_name="Supplier",
    app=app,
)


@app.route("/export", methods=["GET", "POST"])
def export():
    if request.method == "POST":
        transaction_type = request.form.get("transaction_type")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        if app.debug:
            # Debug mode: send file to browser
            file_stream = BytesIO()
            file_stream = export_to_xlsx(
                transaction_type, start_date, end_date, file_stream
            )
            filename = f"{transaction_type}_record.xlsx"
            return send_file(
                file_stream,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                as_attachment=True,
                download_name=filename,
            )
        else:
            # Production mode: show file picker and save to disk
            path = open_export_file_picker(transaction_type)
            if not path:
                flash("Export cancelled — no file selected.", "error")
                return redirect(url_for("export"))

            _ = export_to_xlsx(transaction_type, start_date, end_date, path)

            flash(f"Exported to {path}", "success")
            return redirect(url_for("export"))

    return render_template("export.html")


def run_flask(debug=False):
    app.run(port=1304, debug=debug)


def main():
    debug_mode = len(sys.argv) > 1 and sys.argv[1] == "debug"

    try:
        utils.init_db()
    except Exception as e:
        logger.error(f"[DB] Failed to initialize or verify database: {e}")
        sys.exit(1)

    try:
        logger.info("[CLEANUP] Running startup housekeeping...")
        utils.delete_old_recovery_dbs(older_than_days=25)
    except Exception as e:
        logger.error(f"[CLEANUP] Startup housekeeping failed: {e}")
    scheduler.start()

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
            logger.info("[APP] Window closed, exiting...")
            sys.exit(0)


if __name__ == "__main__":
    main()

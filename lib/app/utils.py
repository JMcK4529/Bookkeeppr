import logging
from flask import (
    flash,
    make_response,
    redirect,
    render_template,
    url_for,
    request,
)
from sqlite3 import IntegrityError
from lib.db import utils as dbutils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_single_entity_view(entity_name, model_class, repo_class):
    def view(**kwargs):
        entity_id = kwargs[f"{entity_name[:-1]}_id"]
        repo = repo_class()
        match request.method:
            case "GET":
                obj = repo.read(id=entity_id)
                template = f"{entity_name[:-1]}.html"
                context_key = f"{entity_name[:-1]}_obj"

                if obj:
                    return render_template(template, **{context_key: obj})
                else:
                    flash(
                        f"{entity_name[:-1].capitalize()} does not exist",
                        "error",
                    )
                    return redirect(
                        request.referrer or url_for(f"{entity_name}")
                    )
            case "POST":
                pass
            case "PATCH":
                name = request.form.get("name", "").strip()
                try:
                    repo.update(model_class(id=entity_id, name=name))
                    flash(
                        f"{entity_name[:-1].capitalize()} updated successfully",
                        "success",
                    )
                    response = make_response("OK", 204)
                except IntegrityError as err:
                    if "UNIQUE constraint failed" in str(err):
                        err_msg = f"{name} already exists"
                    else:
                        err_msg = f"Unexpected error: {str(err)}"
                    logger.warning(err_msg)
                    flash(err_msg, "error")
                    response = make_response(f"Update failed. {err_msg}", 409)
                response.headers["Content-Type"] = "text/plain; charset=utf-8"
                return response
            case "DELETE":
                # Assume by this point we have safely confirmed the delete command
                entity = repo.read(id=entity_id)
                if not entity:
                    err_msg = f"{entity_name[:-1].capitalize()} not found."
                    logger.warning(f"[DELETE] {err_msg}")
                    flash(err_msg, "error")
                    response = make_response(err_msg, 404)
                    response.headers["Content-Type"] = (
                        "text/plain; charset=utf-8"
                    )
                    return response

                safe_to_delete = False
                # Create the recovery DB
                try:
                    dbutils.backup_deleted_entity(entity, repo_class)
                    safe_to_delete = True
                except Exception as err:
                    err_msg = f"Data backup failed. Delete operation on {entity.name} aborted."
                    logger.warning(f"[DELETE] {err_msg}.\n" + f"{err}")
                    flash(err_msg, "error")
                    response = make_response(err_msg, 500)

                if safe_to_delete:
                    try:
                        repo.delete(entity.id)
                        flash(
                            f"{entity.name} was successfully deleted.",
                            "success",
                        )
                        response = make_response("OK", 204)
                    except IntegrityError as err:
                        err_msg = f"Delete blocked due to data constraint: {str(err)}"
                        logger.warning(f"[DELETE] {err_msg}")
                        flash(err_msg, "error")
                        response = make_response(err_msg, 409)
                    except Exception as err:
                        err_msg = f"Unexpected error: {str(err)}"
                        logger.error(f"[DELETE] {err_msg}")
                        flash(f"{entity.name} could not be deleted.", "error")
                        response = make_response(f"{err_msg}", 500)

                response.headers["Content-Type"] = "text/plain; charset=utf-8"
                return response

    return view


def register_entity_routes(
    entity_name, template_name, model_class, repo_class, app
):
    list_endpoint = f"/{entity_name}"
    create_endpoint = f"/{entity_name}/create"
    by_id_endpoint = f"/{entity_name}/<int:{entity_name[:-1]}_id>"

    list_endpoint_name = f"{entity_name}"
    create_endpoint_name = f"create_{entity_name}"
    by_id_endpoint_name = f"single_{entity_name[:-1]}"

    @app.route(list_endpoint, endpoint=list_endpoint_name)
    def list_entities():
        query = request.args.get("q", "")
        repo = repo_class()
        results = repo.search(query) if query else repo.all()
        return render_template(
            template_name, query=query, **{entity_name: results}
        )

    @app.route(
        create_endpoint, methods=["POST"], endpoint=create_endpoint_name
    )
    def create_entity():
        name = request.form.get("name")
        repo = repo_class()
        try:
            new_entity = repo.create(model_class(None, name))
            flash(f"Successfully added {entity_name[:-1]}: {name}", "success")
        except IntegrityError as err:
            if "UNIQUE constraint failed" in str(err):
                err_msg = f"{name} already exists"
            else:
                err_msg = f"Unexpected Error: {str(err)}"
            logger.warning(err_msg)
            flash(err_msg, "error")
        return redirect(list_endpoint)

    app.add_url_rule(
        rule=by_id_endpoint,
        endpoint=by_id_endpoint_name,
        view_func=create_single_entity_view(
            entity_name, model_class, repo_class
        ),
        methods=["GET", "POST", "PATCH", "DELETE"],
    )

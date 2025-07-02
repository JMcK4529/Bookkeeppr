import logging
from flask import flash, redirect, render_template, url_for, request
from sqlite3 import IntegrityError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_single_entity_view(entity_name, repo_class):
    def view(**kwargs):
        entity_id = kwargs[f"{entity_name}_id"]
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
                pass
            case "DELETE":
                pass

    return view


def register_entity_routes(entity_name, template_name, repo_class, app):
    list_endpoint = f"/{entity_name}"
    create_endpoint = f"/{entity_name}/create"
    by_id_endpoint = f"/{entity_name}/<int:{entity_name}_id>"

    list_endpoint_name = f"{entity_name}"
    create_endpoint_name = f"create_{entity_name}"
    by_id_endpoint_name = f"single_{entity_name}"

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
            new_entity = repo.create(None, name)
            flash(f"Successfully added {entity_name[:-1]}: {name}", "success")
        except IntegrityError as err:
            if "UNIQUE constraint failed" in str(err):
                err_msg = f"{name} already exists"
                logger.warning(err_msg)
                flash(err_msg, "error")
            else:
                logger.warning(err_msg)
                flash(f"Unexpected Error: {str(err)}", "error")
        return redirect(list_endpoint)

    app.add_url_rule(
        rule=by_id_endpoint,
        endpoint=by_id_endpoint_name,
        view_func=create_single_entity_view(entity_name, repo_class),
        methods=["GET", "POST", "PATCH", "DELETE"],
    )

import re

from shiny import App, reactive, render, req, ui

from src.control_plane.retrieval import retrieve
from src.data_plane.embeddings import DATA_DIR, build_index
from src.utils.logger import get_logger

logger = get_logger(__name__)

FILES_URL_PATH = "/files"


def _compile_filter(pattern: str) -> "re.Pattern | None":
    """Compile a user-entered filter as a case-insensitive regex.

    Returns None if the field is blank (no filter) or the pattern is invalid
    (so an unfinished regex doesn't hide every row while the user is typing).
    """
    pattern = pattern.strip()
    if not pattern:
        return None
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error:
        return None

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h4("Document Search"),
        ui.input_text("query", "Query", placeholder="e.g. EGFR resistance mechanism"),
        ui.input_numeric("k", "Top results", value=5, min=1, max=20),
        ui.input_action_button("search_btn", "Search", class_="btn-primary w-100 mb-2"),
        ui.hr(),
        ui.input_action_button("build_btn", "Build / Refresh Index", class_="btn-secondary w-100"),
        ui.output_text("index_status"),
        width=280,
    ),
    ui.h2("Results"),
    ui.output_text("results_count"),
    ui.div(
        ui.input_text("filter_filename", "Filter: filename (regex)", placeholder="e.g. ^EGFR.*\\.pdf$"),
        ui.input_text("filter_type", "Filter: type (regex)", placeholder="e.g. pdf|docx"),
        ui.input_numeric("filter_min_score", "Min score", value=0.0, min=0.0, max=1.0, step=0.01),
        ui.input_select("page_size", "Per page", choices=["5", "10", "20"], selected="10"),
        class_="d-flex gap-3 flex-wrap align-items-end mb-3",
    ),
    ui.output_ui("results_table"),
    ui.div(
        ui.input_action_button("prev_page", "◀ Prev", class_="btn btn-sm btn-outline-secondary"),
        ui.output_text("page_indicator", inline=True),
        ui.input_action_button("next_page", "Next ▶", class_="btn btn-sm btn-outline-secondary"),
        class_="d-flex align-items-center gap-3 mt-2",
    ),
    title="Amgen Document Search",
)


def server(input, output, session):
    index_msg = reactive.value("Index not built. Click 'Build / Refresh Index' to start.")
    current_page = reactive.value(1)

    @reactive.effect
    @reactive.event(input.build_btn)
    def _build():
        index_msg.set("Checking for new or changed documents...")
        #this is where the chain starts to synchronize the document embedding index with the current state of the data directory. When the "Build / Refresh Index" button is clicked, it triggers this reactive effect, which first updates the index status message to indicate that it's checking for new or changed documents. Then, it calls build_index(refresh=True) to perform the synchronization process, which involves embedding new or modified documents and updating the database accordingly. Once the process is complete, it updates the index status message again to show how many documents are currently indexed, providing feedback to the user about the state of the index.
        docs = build_index(refresh=True)
        index_msg.set(f"Index ready: {len(docs)} documents indexed.")
        logger.info("Index refreshed; %d documents indexed", len(docs))

    @output
    @render.text
    def index_status():
        return index_msg()

    @reactive.calc
    @reactive.event(input.search_btn)
    def search_results():
        req(input.query())
        logger.info("Search query=%r k=%d", input.query(), input.k())
        return retrieve(input.query(), k=input.k())

    @reactive.calc
    def filtered_results():
        results = search_results()
        name_pattern = _compile_filter(input.filter_filename())
        type_pattern = _compile_filter(input.filter_type())
        min_score = input.filter_min_score()
        return [
            r for r in results
            if (name_pattern is None or name_pattern.search(r["filename"]))
            and (type_pattern is None or type_pattern.search(r["source_type"]))
            and r["score"] >= min_score
        ]

    @reactive.calc
    def total_pages():
        page_size = int(input.page_size())
        return max(1, -(-len(filtered_results()) // page_size))  # ceil division

    # Jump back to page 1 whenever the search, filters, or page size change
    @reactive.effect
    def _reset_page_on_change():
        filtered_results()
        input.page_size()
        current_page.set(1)

    @reactive.effect
    @reactive.event(input.prev_page)
    def _go_prev():
        current_page.set(max(1, current_page() - 1))

    @reactive.effect
    @reactive.event(input.next_page)
    def _go_next():
        current_page.set(min(total_pages(), current_page() + 1))

    @output
    @render.text
    def page_indicator():
        return f"Page {current_page()} of {total_pages()}"

    @output
    @render.text
    def results_count():
        total = len(search_results())
        shown = len(filtered_results())
        if shown == total:
            return f"{total} result{'s' if total != 1 else ''} found"
        return f"Showing {shown} of {total} results (filtered)"

    @output
    @render.ui
    def results_table():
        results = filtered_results()
        if not results:
            return ui.p("No results match your search and filters.")

        page_size = int(input.page_size())
        page = min(current_page(), total_pages())
        start = (page - 1) * page_size
        page_results = results[start : start + page_size]

        header = ui.tags.tr(
            ui.tags.th("Filename"),
            ui.tags.th("Type"),
            ui.tags.th("Score"),
            ui.tags.th("Document"),
        )
        body_rows = [
            ui.tags.tr(
                ui.tags.td(r["filename"]),
                ui.tags.td(r["source_type"]),
                ui.tags.td(f"{r['score']:.4f}"),
                ui.tags.td(
                    ui.tags.a(
                        "Download",
                        href=f"{FILES_URL_PATH}/{r['filename']}",
                        download=r["filename"],
                        class_="btn btn-sm btn-outline-primary",
                    )
                ),
            )
            for r in page_results
        ]
        return ui.tags.table(
            ui.tags.thead(header),
            ui.tags.tbody(*body_rows),
            class_="table table-striped table-hover",
        )


app = App(app_ui, server, static_assets={FILES_URL_PATH: DATA_DIR.resolve()})

if __name__ == "__main__":
    import shiny
    shiny.run_app(app, host="127.0.0.1", port=8000, reload=False)

import pandas as pd
from shiny import App, reactive, render, req, ui

from src.control_plane.retrieval import retrieve
from src.data_plane.embeddings import build_index
from src.utils.logger import get_logger

logger = get_logger(__name__)

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
    ui.output_data_frame("results_table"),
    title="Amgen Document Search",
)


def server(input, output, session):
    index_msg = reactive.value("Index not built. Click 'Build / Refresh Index' to start.")

    @reactive.effect
    @reactive.event(input.build_btn)
    def _build():
        index_msg.set("Building index — this may take a few minutes...")
        docs = build_index(force=True)
        index_msg.set(f"Index ready: {len(docs)} documents indexed.")
        logger.info("Index built with %d documents", len(docs))

    @output
    @render.text
    def index_status():
        return index_msg()

    @output
    @render.data_frame
    @reactive.event(input.search_btn)
    def results_table():
        req(input.query())
        logger.info("Search query=%r k=%d", input.query(), input.k())
        results = retrieve(input.query(), k=input.k())
        if not results:
            return render.DataGrid(
                pd.DataFrame(columns=["filename", "source_type", "score", "preview"])
            )
        df = pd.DataFrame(results)[["filename", "source_type", "score", "preview"]]
        df["score"] = df["score"].map(lambda x: f"{x:.4f}")
        return render.DataGrid(df, width="100%")


app = App(app_ui, server)

if __name__ == "__main__":
    import shiny
    shiny.run_app(app, host="127.0.0.1", port=8000, reload=False)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from shiny import App, ui, render, reactive

# Load cancer gene data from Excel on startup. Path is relative to this file
# so it works regardless of where you launch shiny from.
EXCEL_PATH = Path(__file__).parent / "cancer_genes.xlsx"
gene_df = pd.read_excel(EXCEL_PATH)

ALL_CANCER_TYPES = sorted(gene_df["Cancer Type"].unique().tolist())
ALL_PATHWAYS     = sorted(gene_df["Pathway"].unique().tolist())
MAX_PATIENTS     = int(gene_df["Patient Count"].max())

# page_navbar creates a top-level navigation bar with multiple pages/tabs.
# Each ui.nav_panel() becomes one tab in the navbar.
app_ui = ui.page_navbar(

    # ── Tab 1: Cancer Gene Dashboard ────────────────────────────────────────
    ui.nav_panel(
        "Cancer Gene Dashboard",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("Filters"),

                # Checkbox groups let the user select one or more cancer types / pathways.
                # The choices list is built from the unique values in the Excel file,
                # so adding a new row to the spreadsheet automatically extends the filter.
                ui.input_checkbox_group(
                    "cancer_types",
                    "Cancer Type:",
                    choices=ALL_CANCER_TYPES,
                    selected=ALL_CANCER_TYPES,
                ),
                ui.input_checkbox_group(
                    "pathways",
                    "Pathway:",
                    choices=ALL_PATHWAYS,
                    selected=ALL_PATHWAYS,
                ),
                ui.input_slider(
                    "min_patients",
                    "Min. Patients:",
                    min=0,
                    max=MAX_PATIENTS,
                    value=0,
                    step=500,
                ),
                ui.input_select(
                    "drug_status",
                    "Drug Status:",
                    {"All": "All", "Approved": "Approved",
                     "Investigational": "Investigational", "None": "No Targeted Therapy"},
                ),
            ),

            # The main area uses inner tabs so the user can switch between views
            # without losing their filter selections in the sidebar.
            ui.navset_tab(
                ui.nav_panel("Expression Levels", ui.output_plot("expression_plot")),
                ui.nav_panel("Patient Counts",    ui.output_plot("patient_plot")),
                ui.nav_panel("Data Table",         ui.output_table("gene_table")),
            ),
        ),
    ),

    # ── Tab 2: Shiny Validation Test (original content) ──────────────────────
    ui.nav_panel(
        "Shiny Validation",

        #This is a simple Shiny app to test the basic functionality of Shiny for Python. It includes an input field for the user's name, a button to trigger a greeting, and reactive outputs to display the greeting and the number of times the button has been clicked.
        ui.h2("Shiny for Python - Validation Test"),
        ui.input_text("name", "Enter your name:", placeholder="e.g. Amgen"),
        ui.input_action_button("greet_btn", "Say Hello"),

        #what is the purpose of this hr() element? It seems to be used for visual separation between the input elements and the output elements in the UI. It creates a horizontal line that helps to distinguish between different sections of the app, making it easier for users to understand the layout and flow of the interface.
        ui.hr(),

        #the output_text_verbatim function is used to display text output in a verbatim format, which preserves whitespace and formatting. In this app, it is used to show the greeting message and the click count in a clear and readable way.
        ui.output_text_verbatim("greeting"),
        ui.output_text_verbatim("click_count"),

        ui.hr(),

        # --- Reactive visualization section ---
        # The sidebar layout puts controls on the left and the plot on the right.
        # Changing any slider or dropdown immediately re-renders both the plot and the table below.

        #the h3 function creates a header for the reactive data explorer section of the app, indicating that the following content will allow users to explore data in a reactive way. It serves as a title for that part of the UI, helping to organize the layout and guide users through the different sections of the app.
        ui.h3("Reactive Data Explorer"),

        #the layout_sidebar function creates a layout with a sidebar for inputs and a main area for outputs. The sidebar contains input controls for selecting the distribution type, sample size, and number of histogram bins. The main area is designated for displaying the histogram plot based on the selected inputs.
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_select(
                    "distribution",
                    "Distribution:",
                    #the options for the distribution input are defined as a dictionary where the keys are the internal values used in the code (e.g., "normal", "uniform", "exponential") and the values are the labels that will be displayed in the dropdown menu (e.g., "Normal", "Uniform", "Exponential"). This allows users to select a distribution type from a user-friendly dropdown while the app can still use the corresponding internal values for processing.
                    {"normal": "Normal", "uniform": "Uniform", "exponential": "Exponential"},
                ),
                ui.input_slider("n_samples", "Sample size:", min=50, max=2000, value=300, step=50),
                ui.input_slider("n_bins", "Histogram bins:", min=5, max=60, value=20, step=5),
            ),
            ui.output_plot("hist_plot"),
        ),

        ui.h4("Summary Statistics"),
        # output_table renders a pandas DataFrame as an HTML table
        ui.output_table("stats_table"),
    ),

    title="Amgen Target Knowledge POC",
)


#this server function defines the reactive behavior of the app. It uses reactive values and effects to manage state and update the UI based on user interactions. The clicks variable keeps track of how many times the greet button has been clicked, and the greeting and click_count functions generate the appropriate output based on the current state of the inputs and reactive values.
def server(input, output, session):

    # ── Cancer Gene Dashboard logic ──────────────────────────────────────────

    # reactive.calc caches the filtered dataframe and only recomputes when any
    # filter input changes. All three outputs read from this single calc so they
    # always stay in sync without repeating the filter logic.
    @reactive.calc
    def filtered_gene_df():
        mask = (
            gene_df["Cancer Type"].isin(input.cancer_types()) &
            gene_df["Pathway"].isin(input.pathways()) &
            (gene_df["Patient Count"] >= input.min_patients())
        )
        if input.drug_status() != "All":
            mask &= gene_df["Drug Status"] == input.drug_status()
        return gene_df[mask].copy()

    @render.plot
    def expression_plot():
        data = filtered_gene_df().sort_values("Expression Level (log2FC)", ascending=False)
        if data.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "No genes match the current filters.",
                    ha="center", va="center", transform=ax.transAxes)
            return fig

        pathway_list = data["Pathway"].unique()
        palette   = plt.cm.get_cmap("tab10", len(pathway_list))
        color_map = {p: palette(i) for i, p in enumerate(pathway_list)}
        colors    = [color_map[p] for p in data["Pathway"]]

        fig, ax = plt.subplots(figsize=(10, max(5, len(data) * 0.38)))
        ax.barh(data["Gene"], data["Expression Level (log2FC)"], color=colors)
        ax.axvline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.5)
        ax.set_xlabel("Expression Level (log2 Fold Change vs. Normal Tissue)")
        ax.set_title("Gene Expression Levels by Target")
        ax.invert_yaxis()

        legend_handles = [mpatches.Patch(color=color_map[p], label=p) for p in pathway_list]
        ax.legend(handles=legend_handles, fontsize=8, loc="lower right")
        fig.tight_layout()
        return fig

    @render.plot
    def patient_plot():
        data = filtered_gene_df().sort_values("Patient Count", ascending=True)
        if data.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "No genes match the current filters.",
                    ha="center", va="center", transform=ax.transAxes)
            return fig

        fig, ax = plt.subplots(figsize=(10, max(5, len(data) * 0.38)))
        ax.barh(data["Gene"], data["Patient Count"], color="#2196F3")
        ax.set_xlabel("Number of Patients with Gene Alteration")
        ax.set_title("Patient Counts by Target Gene")
        for i, val in enumerate(data["Patient Count"]):
            ax.text(val + 80, i, f"{val:,}", va="center", fontsize=8)
        fig.tight_layout()
        return fig

    @render.table
    def gene_table():
        return filtered_gene_df().reset_index(drop=True)

    # ── Shiny Validation logic (original) ────────────────────────────────────

    #Wrapped in reactive value to make it reactive and allow it to trigger updates when it changes. This variable will keep track of how many times the greet button has been clicked, and it will be updated in the increment function whenever the button is clicked.
    clicks = reactive.value(0)

    #The increment function is defined as a reactive effect that is triggered by the greet_btn input. Whenever the greet button is clicked, this function will be executed, and it will update the clicks reactive value by incrementing it by 1. This allows the app to keep track of how many times the button has been clicked and to trigger updates to any outputs that depend on the clicks value.
    @reactive.effect
    @reactive.event(input.greet_btn)
    def increment():
        #saying to incremenent clicks reactive by 1 each time the button is clicked
        clicks.set(clicks() + 1)

    #what is @render.text doing here? The @render.text decorator is used to define a reactive output that generates text based on the current state of the inputs and reactive values. In this case, the greeting function is decorated with @render.text, which means that it will be called whenever the relevant inputs (like the name input and the greet button) change, and it will return a string that will be displayed in the UI as the greeting message. The function checks if the greet button has been clicked at least once, and if so, it constructs a greeting message using the name input. If the name input is empty, it defaults to "World". If the greet button has not been clicked, it prompts the user to click the button to test reactivity.
    @render.text
    def greeting():
        if input.greet_btn() == 0:
            return "Click the button to test reactivity."
        name = input.name().strip() or "World"
        return f"Hello, {name}! Shiny is working."

    @render.text
    #this is the text boxes that show up in the website
    def click_count():
        if clicks() > 0:
            return f"Button clicked {clicks()} time(s) — reactive state is working."
        return ""

    # reactive.calc is like a cached reactive expression — it recomputes only when its
    # inputs (n_samples or distribution) change. Both hist_plot and stats_table read from
    # this one calculation, so they always stay in sync without duplicating the sampling logic.
    @reactive.calc
    def sampled_data():
        n = input.n_samples()
        dist = input.distribution()
        rng = np.random.default_rng(seed=42)
        if dist == "normal":
            return rng.standard_normal(n)
        elif dist == "uniform":
            return rng.uniform(0, 1, n)
        else:  # exponential
            return rng.exponential(scale=1.0, size=n)

    # @render.plot tells Shiny to expect a matplotlib Figure returned from this function.
    # It re-renders automatically whenever sampled_data() or n_bins changes.
    @render.plot
    def hist_plot():
        data = sampled_data()
        dist = input.distribution()
        bins = input.n_bins()

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(data, bins=bins, color="#4C9BE8", edgecolor="white", linewidth=0.5)
        ax.set_title(f"{dist.capitalize()} distribution  (n={len(data)}, bins={bins})")
        ax.set_xlabel("Value")
        ax.set_ylabel("Frequency")
        fig.tight_layout()
        return fig

    # @render.table expects a pandas DataFrame. Shiny converts it to an HTML table automatically.
    @render.table
    def stats_table():
        data = sampled_data()
        stats = {
            "Statistic": ["Count", "Mean", "Std Dev", "Min", "25th %ile", "Median", "75th %ile", "Max"],
            "Value": [
                len(data),
                round(np.mean(data), 4),
                round(np.std(data), 4),
                round(np.min(data), 4),
                round(np.percentile(data, 25), 4),
                round(np.median(data), 4),
                round(np.percentile(data, 75), 4),
                round(np.max(data), 4),
            ],
        }
        return pd.DataFrame(stats)


#How does it run? I don't call app directly — shiny run shiny_test.py picks up the
#module-level `app` variable automatically and starts the server.
app = App(app_ui, server)

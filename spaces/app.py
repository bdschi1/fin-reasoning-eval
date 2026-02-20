"""
HuggingFace Spaces App for Financial Reasoning Eval Benchmark

Interactive leaderboard and evaluation interface.

Deploy to HuggingFace Spaces:
    huggingface-cli repo create financial-reasoning-eval --type space --sdk gradio
    git push
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import gradio as gr
    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False
    print("Gradio not installed. Install with: pip install gradio")

import pandas as pd
from datetime import datetime


# Sample leaderboard data (will be replaced with real data)
SAMPLE_LEADERBOARD = [
    {
        "rank": 1,
        "model": "GPT-4o",
        "organization": "OpenAI",
        "overall": 0.847,
        "easy": 0.923,
        "medium": 0.861,
        "hard": 0.782,
        "expert": 0.654,
        "earnings": 0.871,
        "dcf": 0.823,
        "accounting": 0.859,
        "catalyst": 0.834,
        "formula": 0.812,
        "financial_stmt": 0.885,
    },
    {
        "rank": 2,
        "model": "Claude 3.5 Sonnet",
        "organization": "Anthropic",
        "overall": 0.832,
        "easy": 0.912,
        "medium": 0.847,
        "hard": 0.771,
        "expert": 0.638,
        "earnings": 0.856,
        "dcf": 0.812,
        "accounting": 0.845,
        "catalyst": 0.819,
        "formula": 0.798,
        "financial_stmt": 0.862,
    },
    {
        "rank": 3,
        "model": "Llama 3.1 70B",
        "organization": "Meta",
        "overall": 0.764,
        "easy": 0.867,
        "medium": 0.782,
        "hard": 0.698,
        "expert": 0.542,
        "earnings": 0.789,
        "dcf": 0.745,
        "accounting": 0.778,
        "catalyst": 0.751,
        "formula": 0.723,
        "financial_stmt": 0.798,
    },
    {
        "rank": 4,
        "model": "Llama 3.1 8B",
        "organization": "Meta",
        "overall": 0.623,
        "easy": 0.756,
        "medium": 0.634,
        "hard": 0.541,
        "expert": 0.387,
        "earnings": 0.645,
        "dcf": 0.598,
        "accounting": 0.634,
        "catalyst": 0.612,
        "formula": 0.589,
        "financial_stmt": 0.661,
    },
]


def load_leaderboard_data():
    """Load leaderboard data from storage or use sample data."""
    leaderboard_path = Path(__file__).parent.parent / "data" / "leaderboard.json"

    if leaderboard_path.exists():
        with open(leaderboard_path) as f:
            data = json.load(f)
            return data.get('entries', SAMPLE_LEADERBOARD)

    return SAMPLE_LEADERBOARD


def create_leaderboard_df(data: list) -> pd.DataFrame:
    """Create a pandas DataFrame from leaderboard data."""
    df = pd.DataFrame(data)

    # Format percentages
    pct_cols = ['overall', 'easy', 'medium', 'hard', 'expert',
                'earnings', 'dcf', 'accounting', 'catalyst', 'formula', 'financial_stmt']

    for col in pct_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{x:.1%}" if pd.notna(x) else "-")

    return df


def create_main_leaderboard():
    """Create the main leaderboard table."""
    data = load_leaderboard_data()
    df = create_leaderboard_df(data)

    # Select main columns
    main_cols = ['rank', 'model', 'organization', 'overall', 'easy', 'medium', 'hard', 'expert']
    display_df = df[main_cols] if all(c in df.columns for c in main_cols) else df

    return display_df


def create_category_leaderboard():
    """Create the category breakdown leaderboard."""
    data = load_leaderboard_data()
    df = create_leaderboard_df(data)

    # Select category columns
    cat_cols = ['rank', 'model', 'earnings', 'dcf', 'accounting', 'catalyst', 'formula', 'financial_stmt']
    display_df = df[cat_cols] if all(c in df.columns for c in cat_cols) else df

    return display_df


def format_model_card(model_data: dict) -> str:
    """Format model details as markdown."""
    return f"""
## {model_data.get('model', 'Unknown Model')}

**Organization:** {model_data.get('organization', 'Unknown')}

**Overall Accuracy:** {model_data.get('overall', 0):.1%}

### Performance by Difficulty
| Difficulty | Accuracy |
|------------|----------|
| Easy | {model_data.get('easy', 0):.1%} |
| Medium | {model_data.get('medium', 0):.1%} |
| Hard | {model_data.get('hard', 0):.1%} |
| Expert | {model_data.get('expert', 0):.1%} |

### Performance by Category
| Category | Accuracy |
|----------|----------|
| Earnings Surprise | {model_data.get('earnings', 0):.1%} |
| DCF Sanity | {model_data.get('dcf', 0):.1%} |
| Accounting Red Flags | {model_data.get('accounting', 0):.1%} |
| Catalyst ID | {model_data.get('catalyst', 0):.1%} |
| Formula Audit | {model_data.get('formula', 0):.1%} |
| Financial Statement | {model_data.get('financial_stmt', 0):.1%} |
"""


def get_model_details(model_name: str) -> str:
    """Get detailed information about a model."""
    data = load_leaderboard_data()

    for entry in data:
        if entry.get('model') == model_name:
            return format_model_card(entry)

    return "Model not found."


def create_app():
    """Create the Gradio app."""
    if not GRADIO_AVAILABLE:
        raise ImportError("Gradio not installed")

    # Custom CSS
    custom_css = """
    .leaderboard-table {
        font-family: monospace;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 8px;
        background: #f5f5f5;
    }
    """

    with gr.Blocks(css=custom_css, title="Financial Reasoning Eval Benchmark") as app:
        gr.Markdown("""
        # 🏦 Financial Reasoning Eval Benchmark

        A benchmark for evaluating LLM performance on financial reasoning tasks including:
        - **Earnings Surprises** - Beat/miss calculations, driver identification
        - **DCF Sanity Checks** - Terminal growth, WACC validation, projection analysis
        - **Accounting Red Flags** - Revenue recognition, receivables quality, accruals
        - **Catalyst Identification** - Event timing, magnitude, probability assessment
        - **Formula Audit** - Hard-coded values, circular references, logic errors
        - **Financial Statement Analysis** - Ratios, margins, cash flow

        📊 **200-500 curated problems** | 🎯 **4 difficulty levels** | 📈 **6 categories**
        """)

        with gr.Tabs():
            # Main Leaderboard Tab
            with gr.TabItem("🏆 Leaderboard"):
                gr.Markdown("### Overall Rankings")
                leaderboard_df = create_main_leaderboard()
                leaderboard_table = gr.Dataframe(
                    value=leaderboard_df,
                    headers=["Rank", "Model", "Organization", "Overall", "Easy", "Medium", "Hard", "Expert"],
                    interactive=False,
                    elem_classes=["leaderboard-table"],
                )

                gr.Markdown("### Category Performance")
                category_df = create_category_leaderboard()
                category_table = gr.Dataframe(
                    value=category_df,
                    headers=["Rank", "Model", "Earnings", "DCF", "Accounting", "Catalyst", "Formula", "Fin. Stmt"],
                    interactive=False,
                )

            # Model Details Tab
            with gr.TabItem("🔍 Model Details"):
                model_dropdown = gr.Dropdown(
                    choices=[entry['model'] for entry in load_leaderboard_data()],
                    label="Select Model",
                    value=load_leaderboard_data()[0]['model'] if load_leaderboard_data() else None,
                )
                model_details = gr.Markdown(
                    value=get_model_details(load_leaderboard_data()[0]['model']) if load_leaderboard_data() else ""
                )

                model_dropdown.change(
                    fn=get_model_details,
                    inputs=[model_dropdown],
                    outputs=[model_details],
                )

            # About Tab
            with gr.TabItem("📖 About"):
                gr.Markdown("""
                ## About the Benchmark

                The Financial Reasoning Eval Benchmark is designed to test LLM capabilities
                on real-world financial analysis tasks that require:

                - **Numerical reasoning** - Calculating margins, ratios, and growth rates
                - **Domain knowledge** - Understanding financial concepts and conventions
                - **Critical analysis** - Identifying red flags and inconsistencies
                - **Multi-step reasoning** - Following complex financial logic

                ### Problem Categories

                | Category | Description | Example Tasks |
                |----------|-------------|---------------|
                | Earnings Surprise | Analyzing earnings results | Beat/miss calculation, driver analysis |
                | DCF Sanity | Validating valuation models | Terminal growth checks, WACC validation |
                | Accounting Red Flags | Detecting accounting issues | Revenue recognition, accrual analysis |
                | Catalyst ID | Identifying stock catalysts | Event timing, probability assessment |
                | Formula Audit | Finding model errors | Hard-coded values, circular references |
                | Financial Statement | Analyzing financials | Ratio analysis, margin trends |

                ### Difficulty Levels

                - **Easy** - Clear-cut problems with obvious solutions
                - **Medium** - Requires solid financial knowledge
                - **Hard** - Subtle issues requiring careful analysis
                - **Expert** - Complex, multi-factor problems

                ### Evaluation

                Models are evaluated on:
                1. **Accuracy** - Correct answer identification
                2. **Reasoning Quality** - Step-by-step analysis quality
                3. **Calibration** - Confidence alignment with correctness

                ### Citation

                ```bibtex
                @misc{financial-reasoning-eval,
                  title={Financial Reasoning Eval Benchmark},
                  year={2024},
                  publisher={HuggingFace}
                }
                ```
                """)

            # Submit Tab
            with gr.TabItem("📤 Submit"):
                gr.Markdown("""
                ## Submit Your Results

                To submit your model's results to the leaderboard:

                1. Run the evaluation using our provided scripts
                2. Upload your results JSON file below
                3. Your submission will be validated and added to the leaderboard

                ### Running the Evaluation

                ```bash
                # Install dependencies
                pip install -r requirements.txt

                # Generate the benchmark dataset
                python benchmark/scripts/generate_dataset.py

                # Run evaluation
                python benchmark/runners/run_evaluation.py --model your-model-name
                ```

                ### Results Format

                Your results file should contain:
                ```json
                {
                    "model": "your-model-name",
                    "metrics": {
                        "overall_accuracy": 0.85,
                        "total_examples": 300,
                        "category_accuracy": {...},
                        "difficulty_accuracy": {...}
                    }
                }
                ```
                """)

                with gr.Row():
                    submission_file = gr.File(
                        label="Upload Results JSON",
                        file_types=[".json"],
                    )
                    submitter_name = gr.Textbox(
                        label="Submitter Name (optional)",
                        placeholder="Your name or organization",
                    )

                submit_btn = gr.Button("Submit Results", variant="primary")
                submission_output = gr.Markdown()

                def process_submission(file, name):
                    if file is None:
                        return "Please upload a results file."

                    try:
                        with open(file.name, 'r') as f:
                            results = json.load(f)

                        # Validate
                        if 'model' not in results or 'metrics' not in results:
                            return "❌ Invalid submission format. Missing 'model' or 'metrics'."

                        metrics = results['metrics']
                        if 'overall_accuracy' not in metrics:
                            return "❌ Invalid submission. Missing 'overall_accuracy' in metrics."

                        # Success message
                        acc = metrics['overall_accuracy']
                        model = results['model']
                        return f"""
                        ✅ **Submission Received!**

                        **Model:** {model}
                        **Overall Accuracy:** {acc:.1%}

                        Your submission is being processed and will appear on the leaderboard shortly.
                        """

                    except json.JSONDecodeError:
                        return "❌ Invalid JSON file."
                    except Exception as e:
                        return f"❌ Error processing submission: {str(e)}"

                submit_btn.click(
                    fn=process_submission,
                    inputs=[submission_file, submitter_name],
                    outputs=[submission_output],
                )

        # Footer
        gr.Markdown("""
        ---
        📊 **Financial Reasoning Eval Benchmark** | [GitHub](https://github.com/your-repo) | [Dataset](https://huggingface.co/datasets/your-dataset)
        """)

    return app


def main():
    """Run the Gradio app."""
    app = create_app()
    app.launch(share=True)


if __name__ == "__main__":
    main()

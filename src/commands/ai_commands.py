import click
from config import config as app_config # To get GOOGLE_GEMINI_API_KEY

@click.group('ai')
def ai_group():
    """Commands for managing and querying AI Models/Tables."""
    pass

@ai_group.command('create-classifier')
@click.argument('model_name')
@click.option('--engine', default='google_gemini', show_default=True, help="AI engine to use (e.g., 'google_gemini').")
# Parameters for CREATE MODEL. Some are optional or depend on the engine.
# For Gemini, api_key is crucial. Prompt template is good for guiding classification.
@click.option('--mode', default='generative', show_default=True, help="Model mode (e.g., 'generative' for Gemini).")
@click.option('--prompt-template', default=None, help="Default prompt template for the model. E.g., 'Classify: {{text}} Categories: [A,B,C]'")
# The handler's create_ai_table method takes: model_name, target_column_to_predict, source_table_for_training,
# text_feature_column, gemini_api_key, additional_using_params.
# For a general Gemini setup not tied to a specific training table initially, some of these are less relevant.
# The CLI command should simplify this for the user for the "create a generic classifier" use case.
@click.pass_context
def ai_create_classifier(ctx, model_name, engine, mode, prompt_template):
    """
    Creates an AI Model (e.g., a classifier) using a specified engine like Google Gemini.
    This command sets up a generative model that can be used for classification
    by providing appropriate prompts during querying or as a default template.
    """
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red'))
        return

    gemini_api_key = app_config.GOOGLE_GEMINI_API_KEY
    if engine == 'google_gemini' and not gemini_api_key:
        click.echo(click.style("GOOGLE_GEMINI_API_KEY not found in configuration. Cannot create Gemini model.", fg='red'))
        click.echo("Please set it in your .env file or environment variables.")
        return

    additional_params = {'engine': engine, 'mode': mode}
    if prompt_template:
        additional_params['prompt_template'] = prompt_template

    # For the handler.create_ai_table, some parameters are for training-based models.
    # Since we are creating a more general generative model endpoint via this CLI command,
    # we pass placeholders or None for training-specific args.
    click.echo(f"Creating AI Model '{model_name}' using {engine}...")
    if handler.create_ai_table(
        model_name=model_name,
        target_column_to_predict="response", # For generative, this is often the output column name
        source_table_for_training=None, # Not training from a table in this command
        text_feature_column="text", # A common input feature name
        gemini_api_key=gemini_api_key if engine == 'google_gemini' else None,
        additional_using_params=additional_params
    ):
        click.echo(click.style(f"AI Model '{model_name}' created successfully or already exists.", fg='green'))
    else:
        click.echo(click.style(f"Failed to create AI Model '{model_name}'.", fg='red'))

@ai_group.command('query-classifier')
@click.argument('model_name')
@click.argument('text_to_classify')
@click.option('--prompt', 'classification_prompt', default=None, help="Specific prompt for this query. Overrides model's default. Use '{text}' for placeholder.")
@click.pass_context
def ai_query_classifier(ctx, model_name, text_to_classify, classification_prompt):
    """
    Queries an AI Model (classifier) with the given text.
    Uses the model's default prompt template if --prompt is not provided.
    If --prompt is used, it can include '{text}' which will be replaced by TEXT_TO_CLASSIFY.
    Example for --prompt: "Classify the sentiment of the following text: {text}. Options: Positive, Negative, Neutral."
    """
    handler = ctx.obj
    if not handler or not handler.project:
        click.echo(click.style("MindsDB connection not available.", fg='red'))
        return

    click.echo(f"Querying AI Model '{model_name}' with text: '{text_to_classify[:50]}...'")

    result = handler.query_ai_table(
        model_name=model_name,
        text_to_classify=text_to_classify,
        classification_prompt=classification_prompt
    )

    if result is not None:
        click.echo(click.style("Query result:", fg='green'))
        click.echo(result) # Result from handler is usually the direct response string or content
    else:
        click.echo(click.style(f"Failed to get a response from AI Model '{model_name}'.", fg='red'))
        click.echo("Ensure the model exists and the text/prompt is valid.")

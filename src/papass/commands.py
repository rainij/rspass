from pathlib import Path

import click

from papass import (
    PassphraseGenerator,
    PasswordGenerator,
    WordList,
)
from papass.alphabet import (
    alphabet_base_names,
    alphabet_from_charset_names,
    alphabet_shortcuts,
)
from papass.random import (
    available_randomness_sources_str,
    default_randomness_source,
    get_rng,
)

RESULT_BG_COLOR = (0, 44, 77)


@click.command()
@click.help_option("--help", "-h")
@click.option(
    "--length",
    "-l",
    type=int,
    required=True,
    help="Number of words to generate.",
)
@click.option(
    "--randomness-source",
    "-r",
    default=f"{default_randomness_source()}",
    help=f"Source of randomness (default: '{default_randomness_source()}',"
    f" available: {available_randomness_sources_str()}).",
)
@click.option(
    "--wordlist-file",
    "-w",
    required=True,
    help="A file with a new-line-separated list of words.",
)
@click.option(
    "--delimiter",
    "-d",
    default=" ",
    help="Separator between the words (default: ' ').",
)
@click.option(
    "--min-word-size",
    "--minw",
    type=int,
    default=1,
    help="Filter out words which are shorter than this (default: 1).",
)
@click.option(
    "--max-word-size",
    "--maxw",
    type=int,
    help="Filter out words which are longer than this (default: no limit).",
)
@click.option(
    "--dice-sides",
    "-s",
    type=int,
    default=6,
    help="Number of sides of dice (default: 6).",
)
@click.option(
    "--remove-leading-digits",
    "--rld",
    is_flag=True,
    help="If wordlist contains entries like `123 foo` normalizes it to `foo`.",
)
def pp(
    length,
    randomness_source,
    wordlist_file,
    delimiter,
    min_word_size,
    max_word_size,
    dice_sides,
    remove_leading_digits,
):
    """Create a passphrase."""

    try:
        rng = get_rng(randomness_source, dice_sides=dice_sides)

        wordlist = WordList.from_file(
            Path(wordlist_file),
            min_word_size=min_word_size,
            max_word_size=max_word_size,
            remove_leading_digits=remove_leading_digits,
        )

        passphrase_generator = PassphraseGenerator(
            wordlist=wordlist, rng=rng, delimiter=delimiter
        )
        result = passphrase_generator.generate(length)
    except AssertionError as error:
        click.secho(f"ERROR: {error}", fg="red")
        click.echo("Try again!")
        return

    passphrase = click.style(result.passphrase, bg=RESULT_BG_COLOR)

    click.echo(f"Passphrase: {passphrase}")
    click.echo(f"Entropy: {result.entropy:.6}")

    if not result.entropy_is_guaranteed:
        click.secho(
            "WARNING: Entropy might be slightly lower than estimated. "
            "See https://papass.readthedocs.io/en/stable/usage_cli.html#entropy-guarantee.",
            fg="yellow",
        )


@click.command()
@click.help_option("--help", "-h")
@click.option(
    "--length",
    "-l",
    type=int,
    help="Number of words to generate.",
)
@click.option(
    "--randomness-source",
    "-r",
    default=f"{default_randomness_source()}",
    help=f"Source of randomness (default: '{default_randomness_source()}',"
    f" available: {available_randomness_sources_str()}).",
)
@click.option(
    "--dice-sides",
    "-s",
    type=int,
    default=6,
    help="Number of sides of dice (default: 6).",
)
@click.option("--alpha-include", "-i", help="The characters for the password.")
@click.option("--alpha-preset", "-p", help="Comma separated list of alphabet names.")
@click.option(
    "--alpha-exclude", "-e", help="The characters to exclude from the alphabet."
)
@click.option(
    "--help-alpha-preset",
    is_flag=True,
    help="Show available --alpha-preset names and exit.",
)
def pw(
    length,
    randomness_source,
    dice_sides,
    alpha_include,
    alpha_preset,
    alpha_exclude,
    help_alpha_preset,
):
    """Create a password.

    NOTE: You can use both --alphabet and --alphabet-names together (they merge).
    """

    if help_alpha_preset:
        print_alphabet_names()
        return

    try:
        assert length, "Missing option --length."
        alpha: str = alpha_include or ""

        if alpha_preset:
            alpha += alphabet_from_charset_names(alpha_preset.split(","))

        if alpha_exclude:
            alpha = "".join(c for c in alpha if c not in alpha_exclude)

        assert alpha, "No alphabet given. Did you forget --alphabet or alphabet-names?"

        rng = get_rng(randomness_source, dice_sides=dice_sides)
        password_generator = PasswordGenerator(rng=rng, alphabet=alpha)
        result = password_generator.generate(length)
    except AssertionError as error:
        click.secho(f"ERROR: {error}", fg="red")
        click.echo("Try again!")
        return

    password = click.style(result.password, bg=RESULT_BG_COLOR)

    click.echo(f"Password: {password}")
    click.echo(f"Entropy: {result.entropy:.6}")


def print_alphabet_names() -> None:
    base_names = {
        k: click.style(v, bg=RESULT_BG_COLOR) for k, v in alphabet_base_names().items()
    }
    shortcuts = {k: ",".join(v) for k, v in alphabet_shortcuts().items()}

    click.echo("The following values can be used with -p, --alpha-preset:")
    click.echo("\n".join(f"{name:9}: {alpha}" for name, alpha in base_names.items()))

    click.echo("\nIn addition the following shortcuts can be used:")
    click.echo("\n".join(f"{short:9}: {name}" for short, name in shortcuts.items()))

    click.echo("\nExample: -p letters,digits")

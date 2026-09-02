"""Sphinx configuration for the reproducible Read-the-Docs build."""

from datetime import date

project = "SerpScrap"
copyright = f"2017-{date.today().year}, ecoron"
author = "ecoron"
version = "2.0"
release = "2.0.0-alpha.3"

needs_sphinx = "7.4"
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.todo",
]

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
master_doc = "index"
language = "en"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "alpaha-2.0.0-tools.md"]
pygments_style = "sphinx"
todo_include_todos = True

html_theme = "default"
html_title = "SerpScrap Documentation"
htmlhelp_basename = "SerpScrapdoc"
html_sidebars = {
    "**": ["globaltoc.html", "relations.html", "searchbox.html"],
}

latex_documents = [(master_doc, "SerpScrap.tex", "SerpScrap Documentation", author, "manual")]
man_pages = [(master_doc, "serpscrap", "SerpScrap Documentation", [author], 1)]
texinfo_documents = [
    (
        master_doc,
        "SerpScrap",
        "SerpScrap Documentation",
        author,
        "SerpScrap",
        "Structured SERP retrieval with Selenium and headless Chrome.",
        "Miscellaneous",
    )
]
epub_title = project
epub_author = author
epub_publisher = author
epub_copyright = copyright
epub_exclude_files = ["search.html"]

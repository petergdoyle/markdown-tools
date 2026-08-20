"""Minimal CSS styles for PDF rendering."""

DEFAULT_CSS = """
@page {
    size: A4;
    margin: 2.5cm;
}

body {
    font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
}

h1, h2, h3, h4, h5, h6 {
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    color: #111;
}

code {
    font-family: "SF Mono", "Fira Code", monospace;
    font-size: 0.9em;
    background: #f5f5f5;
    padding: 0.15em 0.3em;
    border-radius: 3px;
}

pre {
    background: #f5f5f5;
    padding: 1em;
    border-radius: 4px;
    overflow-x: auto;
}

blockquote {
    border-left: 3px solid #ddd;
    margin-left: 0;
    padding-left: 1em;
    color: #666;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
}

th, td {
    border: 1px solid #ddd;
    padding: 0.5em 0.75em;
    text-align: left;
}

th {
    background: #f8f8f8;
    font-weight: 600;
}

img {
    max-width: 100%;
}
"""

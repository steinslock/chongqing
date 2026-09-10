# LaTeX reports

One folder per report. Each holds its `.tex` source and a `build/` directory
containing the compiled PDF. Two reports may cover the same work for different
readers; they are separate documents, not versions of one document, and neither
supersedes the other.

```
reports/latex/
  advisor/     non-technical reporting version
  technical/   full technical version, with complete result tables
```

## Current reports

| Folder | Report | Pages | Reader |
|---|---|---|---|
| `advisor/` | `chongqing_progress_20260907_20260910_advisor.tex` | 11 | Supervisor and hospital collaborators. Purpose and conclusion per modality, why each fell short, no methods detail. |
| `technical/` | `chongqing_progress_20260907_20260910_technical.tex` | 27 | Project record. Methods, complete result tables, statistics. |

Both cover 2026-09-07 to 2026-09-10 and draw every figure from the tables under
`results/`. `technical/writing_record.md` records how the technical version was
drafted.

## Building

TeX Live 2026 with `ctex`, compiled by XeLaTeX. From inside a report's folder:

```
latexmk -xelatex -interaction=nonstopmode -outdir=build <file>.tex
```

Both sources carry a `% !TeX program = xelatex` line, so editors that honour it
pick the right engine on their own.

## What is tracked

The `.tex` source and `build/*.pdf`. Everything else latexmk or an editor
produces — `.aux`, `.log`, `.fls`, `.xdv`, `.synctex.gz` and in-place PDFs
beside the source — is regenerable and gitignored. Keep compiled output inside
`build/`; a PDF written next to the `.tex` is ignored and will not reach the
repository.

## Adding a report

Create a sibling folder with its own `build/`. The gitignore rules match
`reports/latex/*/` and `reports/latex/*/build/`, so a new folder is covered
without editing them.

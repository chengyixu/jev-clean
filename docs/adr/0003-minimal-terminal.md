# ADR 0003: Minimal sequential terminal

Accepted 2026-09-28. Supersedes the dashboard/persistent-panel/B-toggle presentation in ADR 0002; the underlying System Data workflow and automatic model installation remain.

The owner explicitly requested Mole-like simplicity, not a caption-heavy dashboard. Startup shows only the application name, `1. Clean`, `2. Status`, and a short navigation hint. This is an independent implementation based on observed Mole behavior; no GPL source or assets are copied.

Clean follows: sudo Yes/No (default No) → agent logs → selectable model-and-guard-approved files → delete Yes/No (default No). Deletion still means reversible user Trash and retains model re-assessment, fingerprint/open-file checks and journal/undo. A shorter consent dialog is not weaker authorization: no default-Yes, automatic selection, or implicit action on Enter.

Status starts without a permission dialog, shows agent logs, then locations with usage bars and percentages. Percentages are calculated over fully measured non-overlapping rows at the current view level. A parent and its descendants never contribute to the same denominator. Missing/partial measurements remain `?`; row shares are not advertised as Apple category membership. Enter drills into observed child nodes or requests a new model investigation of the selected directory.

Only one stage occupies the terminal at a time. No Header/Footer/ProgressBar, banners, badge rows, permanent input box, debug distributions panel or second pane. Filter/help/export/history/update remain on-demand shortcuts or CLI utilities. Model warnings are retained in report diagnostics instead of breaking the terminal layout. The model is still mandatory and real.

Verification includes actual Textual interaction at 80x24 and 60x20, default-No confirmation, permission cancellation, cancellation during inference, literal checkbox rendering, and percentage arithmetic/unknowns. Public assets are recaptured from the actual TUI with synthetic disk metadata and real model inference.

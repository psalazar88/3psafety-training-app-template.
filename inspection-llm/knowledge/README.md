# Reference library

What the model is allowed to cite. It only quotes standards that are in here.

- `standards/`: the OSHA and ASME sections you inspect against (29 CFR 1910.179, 1910.178, 1926.1400 subpart CC, ASME B30.2, B30.5, B30.9, B30.10, B30.20, etc.). PDFs or text.
- `past-reports/`: finished reports you are happy with. They teach it your format and wording.

In Open WebUI, upload these folders as Knowledge collections and attach them to the 3p-inspector model (README step 5).
Don't put customer-confidential reports here unless every user of the system is allowed to see them. Customer-specific history goes in `memory/<customer>/`.

# Living Explainers

Living Explainers lets an engineer explore one reviewed request path without losing the connection to its sources. Its durable asset is a small authored system model, not a generated paragraph.

The example follows a document preview request through a handler, authorization service, and renderer. Readers choose the success path, denied-access path, or renderer-timeout path; inspect each step's purpose and source lines; and see which facts were observed, documented, or proposed. Choosing a failure outside the model gives “not covered.” If a referenced source file changes, affected steps remain visible but are marked as needing review.

The first release generates a self-contained offline HTML explorer from JSON. Path selection, step inspection, evidence filtering, and an assumptions view use the same model. A reviewer explicitly updates a source baseline after checking it. Rebuilding the HTML cannot silently turn stale evidence current.

This is bounded documentation exploration. It does not infer a repository's architecture, execute the target system, synthesize failure behavior, or claim runtime timing from a sequence. Whole-file source fingerprints are a conservative maintenance signal, not proof that the explanation is correct.

Validate the product by asking new engineers to trace a request and locate a failure boundary using existing docs versus the explorer. Measure answer correctness, source navigation, and maintenance effort after a code change. These are planned evaluation questions, not reported results.

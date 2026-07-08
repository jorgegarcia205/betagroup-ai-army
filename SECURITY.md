# Security & data handling

This repository is a **curated portfolio**. It intentionally contains:

- **No credentials or API keys.** Runnable code reads keys from the environment
  (`OPENAI_API_KEY`); see [`.env.example`](.env.example).
- **No personal data.** The evaluation study uses **synthetic** candidate
  profiles generated for this experiment ([`evals/dataset.json`](evals/dataset.json)).
  No real résumés, companies, or client data appear anywhere.
- **No proprietary business logic.** The `code_samples/` are sanitized,
  illustrative excerpts, not the production source.

The production system that this portfolio describes is kept in a private
repository.

If you believe something sensitive was published here by mistake, please email
**jorge@betagroupservices.com** and I will address it promptly.

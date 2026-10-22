# secrets/

Only the v5 dashboard needs a secret: an **OpenAI API key**.

1. Create an API key at <https://platform.openai.com/api-keys> and make sure the account has credits (Billing).
2. Put the key in **`secrets/openai_api_key`**: one line, nothing else. Use your editor, or run this in a terminal outside your agent:
   ```bash
   umask 077 && printf '%s' 'sk-…' > secrets/openai_api_key
   ```
   **Never paste a key into a chat with an AI assistant.** A key that lands in a transcript has to be rotated.
3. Make it readable only by you and link it to where the v5 dashboard reads it. Dash Server starts at login and doesn't see shell variables, so the app reads a file:
   ```bash
   chmod 600 secrets/openai_api_key
   ln -sf "$PWD/secrets/openai_api_key" ~/.exasol-starter-kit/credentials/openai_api_key
   ```

Everything in this folder except this README and `openai_api_key.example` is gitignored. Check with `git check-ignore -v secrets/openai_api_key`.

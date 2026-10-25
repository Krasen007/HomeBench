Every time I send a message to you it SHOULD be appended to the @History.md file.
Each message from the @History.md file SHOULD be mapped to a test file.
If a past history message contradicts with a new history message, confirm if the user intended to change the application behaviour. Then create the new test file and remove the older as it will no longer apply.
If a test fails, do not try to fix it, first explain in detail why it failed and ask the user to confirm if this is intended.
# Security policy

## Reporting a vulnerability

Please **don't open a public issue** for security problems.

Report them privately through GitHub: go to the **Security** tab of this repository and choose
**Report a vulnerability**. You'll get a reply as soon as possible.

## Scope

Video File Organizer is a local desktop app. It doesn't use the network. It moves, renames and
trashes files only inside the folders the user picks. Relevant reports include, for example:

- a way to make the app overwrite or permanently delete a file,
- a way to make it touch files outside the chosen folders,
- a vulnerable dependency (PySide6 / Qt / FFmpeg).

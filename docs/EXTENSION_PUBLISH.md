# Publishing AI Ethics Extension

1. **Prepare the release branch**
   - Ensure workspace clean; commit extension build artifacts only in `vscode-extension/out`.
   - Update `package.json` and `CHANGELOG` with the next version, then run `npm --prefix vscode-extension run compile`.
   - Verify `git status` only shows intended edits.

2. **Package the VS Code extension**
   - Install `vsce` globally if needed: `npm install -g vsce`.
   - From `vscode-extension/` run `vsce package`. The `.vsix` file embeds the compiled `out/`.
   - Keep a copy for manual upload/testing.

3. **Publish to Marketplace**
   - Register a Microsoft Partner Center account and create a publisher.
   - Use `vsce login <publisher>` to cache credentials or set `VSCE_PAT`.
   - Run `vsce publish <version|patch|minor|major>` from `vscode-extension/`.
   - Monitor Partner Center for validation; the Marketplace listing updates automatically.

4. **Enable continuous updates via git**
   - Push commits that touch extension sources (`src/`, `package.json`, configuration).
   - Include updated version in `package.json`; `vsce publish` uses that.
   - Tag releases (e.g., `git tag vscode-1.4.0`) and push tags so CI or other tools can reference published versions.
   - Document release notes so users know what changed.

5. **Automate publishing**
   - Create GitHub Actions or another CI job triggered on tags.
   - Checkout repo, install Node, run `npm ci`, `npm run compile`, and `vsce publish --pat ${{ secrets.VSCE_PAT }}`.
   - Keep the PAT in repo secrets and restrict scope to `Marketplace`.

6. **Local testing flow**
   - Install the `.vsix` via `code --install-extension vscode-extension-*.vsix`.
   - Use `npm --prefix vscode-extension run compile` before packaging to ensure the built code matches.

7. **Best practices**
   - Update `README` and `vscode-extension/README.md` whenever functionality changes.
   - Track dependencies in `package.json` and rerun `npm install`.
   - Use `git push` after publishing to keep repo in sync; add release tags to signal published versions.


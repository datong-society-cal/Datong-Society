# Website deployment and handover

Production: **https://datong.studentorg.berkeley.edu/**

Source: **https://github.com/datong-society-cal/Datong-Society**

GitHub Pages is a preview mirror, not the canonical site.

## Everyday updates

Edit the HTML, CSS, JavaScript, or images and open a pull request. The
**Validate static site** check must pass. Merge into `main`; **Deploy OCF**
packages the site, transfers it over SSH, verifies it, and records a successful
GitHub deployment. A push to `main` uses the same workflow.

Watch the **Publish to OCF** job in Actions. Success means the exact expected
file set and SHA-256 hashes were verified on disk, and the production homepage,
version marker, main CSS/JS, logo, and QR image were checked over HTTPS.

The current production commit is available at
[deploy-version.json](https://datong.studentorg.berkeley.edu/deploy-version.json).
The commit identifies content; this file contains no credentials.

## Source and artifact boundaries

This is a static site with no package manager or application server dependency.
Python 3.11+ is used only for checks and deployment tooling. OCF serves the files
with its managed Apache server.

- `index.html`, published CSS/JS/fonts, images, and `LICENSE.txt` are packaged.
- The packager generates reviewed `.htaccess`, a version marker, and a SHA-256
  manifest. The manifest stays private on OCF; it is not served by Apache.
- Git metadata, workflows, scripts, documentation, legacy Sass, backups, and keys
  never enter the website output. `dist/` and `site.tar.gz` are ignored by Git.
- **Edit `assets/css/main.css` directly.** Legacy `assets/sass/` is not a valid
  build source. See `assets/css/BUILD-STATUS.md` before considering a migration.
- Keep local URLs relative to the page/CSS so the site also works at
  `https://www.ocf.berkeley.edu/~datong/`.
- New file types or Apache directives require a deliberate change to
  `scripts/site_contract.py`, its tests, and the installed OCF receiver contract.

Local validation from the repository root:

```sh
python3 -m unittest discover -s scripts/tests -v
python3 scripts/package_site.py --commit "$(git rev-parse HEAD)"
```

The packager uses tracked file names. Add new website files to Git before
packaging, and commit before releasing. It never recompiles CSS.

## OCF layout

```text
/home/d/da/datong/
├── .ssh/authorized_keys       human key plus a restricted CI key
├── archive/                   private, durable historical backups
├── deploy/
│   ├── bin/                   installed receiver and reviewed static contract
│   ├── releases/<commit>/     validated static releases, including manifest
│   ├── state.json             current/previous commits and workflow sequence
│   ├── history.jsonl          successful deployment log
│   └── publish.lock           shared publish/rollback lock
└── public_html -> /services/http/users/d/datong
```

`public_html` and its real OCF webspace directory must remain intact. Do not
replace the link as a way of changing the Apache document root.

There is no cron, scheduled pull, Git checkout, Ruby runtime, or Node process in
the publishing path. OCF system-created services/configuration are not website
deployment components and should not be removed.

## Identity and GitHub settings

- GitHub environment: `production`, restricted to branch `main`.
- Environment secret: `OCF_DEPLOY_KEY` (an OpenSSH private key, never committed).
- The existing human key, `~/.ssh/datong_ocf_deploy`, remains independent.
  Use `ssh -i ~/.ssh/datong_ocf_deploy datong@ssh.ocf.berkeley.edu` to administer.
- Server identity: the checked-in `scripts/ocf-known-hosts` pins the trusted
  OCF Ed25519 host key. If it changes, verify with OCF before updating it.
- The CI public key has `restrict` and a forced command in `authorized_keys`.
  It cannot request a shell, arbitrary rsync paths, forwarding, or SFTP, and
  cannot update its own receiver or retrieve historical backups.
- Workflow actions are pinned to full commits; update the pins deliberately.
- Do not expose the production secret to pull requests. PR jobs only validate.

The forced command accepts exactly one of:

```text
publish <40-character-commit> <GitHub-run-id> <run-attempt>
rollback <40-character-commit> <GitHub-run-id> <run-attempt>
```

Publish accepts a bounded gzip/tar stream, rejects symlinks, traversal, duplicate
entries, unexpected files, unreviewed Apache directives, and incorrect hashes.
The server serializes changes and rejects an older/already-completed workflow
sequence. GitHub also serializes production jobs without canceling active syncs.

The CI key is a restricted entry point under the Datong Unix account, not a
separate Unix user. Keep its receiver small and tested. A Datong administrator
still has full control of that account.

## Rollback

In GitHub **Actions → Deploy OCF → Run workflow**, choose branch `main` and enter
a retained full commit SHA in `rollback_commit`. Find retained/current commits
in the successful deployment history or `~/deploy/state.json` via the human SSH
key. A rollback runs the same validation, backup, disk checks, and HTTPS checks.
It does not execute code from an old commit or upload an arbitrary archive.

The server retains the three most recent release directories plus the current
and previous successful commits when those differ. Failed uploads are removed.
GitHub keeps the packaged artifact for seven days. Historical archives are never
pruned automatically.

For a version older than retained releases, revert the relevant source changes
on `main` and publish a new commit. Do not forge a commit marker or overwrite a
retained release with different content.

A failed disk/HTTPS validation automatically restores the tree captured just
before the change. SSH/network/host failure can interrupt any multi-file sync:
rsync's delayed updates reduce partial exposure, but this is not an atomic
whole-site switch. Use the human key and historical backup if the first migration
is interrupted. Do not describe this process as zero downtime.

## Receiver updates

The installed receiver is deliberately not updated by the CI identity.
After changing `scripts/ocf_receive.py` or `scripts/site_contract.py`, run the
tests, review the diff, then use the human key to copy both files to
`~/deploy/bin/`. Keep them mode 600 under the private mode-700 `deploy/bin`.
Install changes when no publish job is running; update both files together.
Commit the matching repository code and rerun the workflow.

## First migration and historical backups

First migration requires verified website/home archives and a **nonempty**
database dump. A valid gzip file or matching download hash alone does not prove
a valid database backup. Check export exit status, SQL table definitions, data,
completion marker, and a restore where practical. Backups containing old
configuration and database records remain private (directory 700, files 600).

The administrator creates `~/deploy/allow-initial-migration` only after preparing
the migration and backups. Without it, an empty deployment state cannot publish.
The receiver consumes this marker after the first successful publish.

Before initial publish, archive the complete old webspace, including hidden
Apache rules. Initial static sync removes legacy WordPress/PHP and Hugo files
from the served directory, but never drops the old database. Keep a separate
archive of old home projects before cleaning Ruby/Git remnants or shell startup
references. Do not treat system-provided services as old website processes.

The private local migration report and backup folder record the actual historical
backup filenames and verification outcomes; these records are not public assets.

## Handover and key rotation

1. Add the next maintainer to the GitHub organization/repository and ensure the
   appropriate RSO signatories retain OCF account-recovery access.
2. Confirm they can edit via PR, inspect Actions, and identify the deployed SHA.
3. Keep a human SSH key separate from the CI key and protect the downloaded
   historical archives. Never put either private keys or database dumps in Git.
4. To rotate CI access, generate a new key locally, add it with the same forced
   command/restrictions, replace `production/OCF_DEPLOY_KEY`, run and verify a
   deployment, then remove only the old CI public-key line. Preserve human keys.
5. Review GitHub branch/environment permissions and OCF account contact details
   when officers change. No special application-server knowledge is required.

## Hosting requirements

The visible OCF badge and student-group disclaimer belong in the shared footer.
They are required for the Berkeley virtual host; do not remove them when editing
the design. References: [OCF hosting](https://www.ocf.berkeley.edu/docs/services/web/),
[virtual-host requirements](https://www.ocf.berkeley.edu/docs/services/vhost/),
[official badges](https://www.ocf.berkeley.edu/docs/services/vhost/badges/).

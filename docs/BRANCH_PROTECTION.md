# Branch Protection Setup

To ensure that all pull requests pass tests before merging, you need to configure branch protection rules in GitHub.

## Steps to Enable Required Status Checks

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Branches**
3. Under "Branch protection rules", click **Add rule** or edit existing rules for `dev` and `main` branches
4. Configure the following settings:

### Required Settings:
- **Branch name pattern**: `dev` (create one rule for dev, another for main)
- Check **Require status checks to pass before merging**
- Check **Require branches to be up to date before merging**
- In the status checks search box, select:
  - `test` (this is the job name from the PR Tests workflow)

### Optional but Recommended Settings:
- Check **Require a pull request before merging**
- Check **Require approvals** (set to 1 or more)
- Check **Do not allow bypassing the above settings**

5. Click **Create** or **Save changes**

## What This Does

Once configured, GitHub will:
- Automatically run tests on every pull request to `dev` or `main`
- Block merging if tests fail
- Block merging if mypy type checking fails
- Show a clear status indicator on the PR showing whether checks have passed

## Workflow Details

The `PR Tests` workflow (`.github/workflows/pr-tests.yml`) runs:
1. All pytest tests in the `tests/` directory
2. mypy type checking on the `fpl/` directory

Both must pass for the PR to be mergeable.

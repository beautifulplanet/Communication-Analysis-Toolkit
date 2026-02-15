#!/bin/bash
export FILTER_BRANCH_SQUELCH_WARNING=1
git filter-branch -f --env-filter '
OLD_EMAIL="dmitrymart83@gmail.com"
CORRECT_NAME="Dmitry M."
CORRECT_EMAIL="132169796+beautifulplanet@users.noreply.github.com"
if [ "$GIT_COMMITTER_EMAIL" = "$OLD_EMAIL" ]; then
    export GIT_COMMITTER_NAME="$CORRECT_NAME"
    export GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
fi
if [ "$GIT_AUTHOR_EMAIL" = "$OLD_EMAIL" ]; then
    export GIT_AUTHOR_NAME="$CORRECT_NAME"
    export GIT_AUTHOR_EMAIL="$CORRECT_EMAIL"
fi
' --tag-name-filter cat -- --branches --tags

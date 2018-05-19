#!/bin/sh
set -e

if [ "$#" -ne 1 ]; then
    echo >&2 "USAGE: $0 new_version"
    exit 2
fi

RELEASE_BRANCH=release
DEV_BRANCH=master
NEW_VERSION=$1

T() {
    printf >&2 -- '-> %s\n' "$*"
    "$@"
}

ask() {
    local ans
    echo ""
    echo -n "  $* (“yes” to proceed) >>> "
    read -r ans || exit 3
    if [ "$ans" != yes ]; then
        exit 3
    fi
}

if ! grep -qFx "VERSION = '$NEW_VERSION'" setup.py; then
    echo "Please update the VERSION variable in “setup.py” first."
    exit 1
fi


if ! T git checkout $RELEASE_BRANCH; then
    T git branch $RELEASE_BRANCH
    T git checkout $RELEASE_BRANCH
fi

T git merge $DEV_BRANCH
ask 'Push?'

T git tag --force v$NEW_VERSION
T git push --set-upstream origin $RELEASE_BRANCH
T git push --tags

if ! T git checkout $DEV_BRANCH; then
    echo ""
    echo "Ignoring this to show the message below."
fi

cat <<EOF

===
Done! Now:
  * Release it on GitHub:
    * The “<number> release(s)” link on the GitHub page of the project;
    * The “Tags” tab;
    * “Add release notes”;
    * Fill in everything needed, click “Publish release”.

  * Run:
      python3 setup.py sdist && python3 setup.py bdist_wheel && twine upload dist/*
    to upload it to PyPI.

  * Tell everybody about it!!
===
EOF

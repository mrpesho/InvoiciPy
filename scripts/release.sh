#!/bin/bash
set -e

VERSION=$(grep -oP '__version__\s*=\s*"\K[^"]+' app/__init__.py)

if [ -z "$VERSION" ]; then
    echo "Error: Could not extract version from app/__init__.py"
    exit 1
fi

TAG="v$VERSION"

if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "Error: Tag $TAG already exists"
    exit 1
fi

git tag -a "$TAG" -m "Release $VERSION"
git push origin "$TAG"

echo "Released $TAG"

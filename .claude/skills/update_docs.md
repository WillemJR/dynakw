---
description: Update and publish the online Sphinx documentation
---

You are helping a software developer release a software library documentation on GitHub.

The documentation is created using Sphinx.

Build the documentation with:
```
cd docs
make html
```

Publish the documentation with:
```
ghp-import -n -p -f docs/_build/html
```

Suggest and execute the commands needed to update the documentation.

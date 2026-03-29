# Remove old doku
rm -rf _build

# Create new doku
sphinx-apidoc -o content/modules/ ../optimizationTools/ -E -d 3 -P -M -f --implicit-namespace

jupyter-book build . --toc _toc.yml

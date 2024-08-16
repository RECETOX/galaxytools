for d in tools/*/
do
(cd "$d" && planemo test --biocontainers .)
done
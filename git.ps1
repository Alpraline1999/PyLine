$version = "v0.1.0"
Write-Output "version: $version"
git checkout $version
git add .
git commit -m "$version"
git push origin $version

git checkout main
git merge $version
git push origin main
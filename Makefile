# Main deployment script - makes all shell scripts executable and runs deploy

if [ ! -x scripts/deploy.sh ]; then
  chmod +x scripts/*.sh
fi

./scripts/deploy.sh
